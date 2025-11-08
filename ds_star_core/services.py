from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from ds_star_agents import (
    AnalyzerAgent,
    AnalyzerDebuggerAgent,
    CoderAgent,
    FinalyzerAgent,
    PlannerAgent,
    RouterAgent,
    SolutionDebuggerAgent,
    TracebackSummarizerAgent,
    VerifierAgent,
)

from .execution import PythonScriptRunner
from .models import DataDescription, ExecutionResult, VerificationResult


def _normalize_text(value: str) -> str:
    return value.strip() if value else ""


@dataclass
class AnalyzerService:
    analyzer: AnalyzerAgent
    runner: PythonScriptRunner
    debugger: AnalyzerDebuggerAgent | None = None
    summarizer: TracebackSummarizerAgent | None = None
    max_attempts: int = 3
    use_retriever: bool = False
    top_k_files: int = 10

    def analyze_files(self, data_files: Sequence[str], query: str = "") -> List[DataDescription]:
        descriptions = [self._analyze_file(path) for path in data_files]
        return self.select_relevant(query, descriptions)

    def select_relevant(
        self,
        query: str,
        descriptions: Sequence[DataDescription],
    ) -> List[DataDescription]:
        if not (self.use_retriever and len(descriptions) > self.top_k_files):
            return list(descriptions)
        return self._retrieve_relevant(query, descriptions)

    # ---------------------------------------------------------------------#
    # Internal helpers                                                     #
    # ---------------------------------------------------------------------#
    def _analyze_file(self, data_file: str) -> DataDescription:
        script = self.analyzer.generate_script(data_file)
        current_script = script
        description = ""

        for attempt in range(self.max_attempts):
            result = self.runner.run(current_script)
            if result.success:
                description = _normalize_text(result.output)
                break

            if self._can_debug_analyzer(attempt):
                summary = self._summarize_traceback(result)
                current_script = self.debugger.debug(current_script, summary)
                continue

            description = (
                f"ERROR: Failed to analyze file after {self.max_attempts} attempts.\n"
                f"{_normalize_text(result.error or result.output)}"
            )

        return DataDescription(file_path=data_file, description=description, script=current_script)

    def _can_debug_analyzer(self, attempt: int) -> bool:
        return (
            attempt < self.max_attempts - 1
            and self.debugger is not None
            and self.debugger.configured
        )

    def _summarize_traceback(self, result: ExecutionResult) -> str:
        if not self.summarizer or not self.summarizer.configured:
            return _normalize_text(result.traceback or result.error or "")
        try:
            return _normalize_text(
                self.summarizer.summarize(result.traceback or result.error or ""),
            )
        except Exception:
            return _normalize_text(result.traceback or result.error or "")

    def _retrieve_relevant(
        self,
        query: str,
        descriptions: Sequence[DataDescription],
    ) -> List[DataDescription]:
        # Placeholder for future retrieval implementation. For now, use a deterministic subset.
        _ = query  # The query is reserved for future relevance scoring.
        return list(descriptions[: self.top_k_files])


@dataclass
class SolutionExecutionService:
    runner: PythonScriptRunner
    debugger: SolutionDebuggerAgent | None = None
    summarizer: TracebackSummarizerAgent | None = None
    max_attempts: int = 3

    def execute(self, script: str, data_info: str) -> Tuple[str, ExecutionResult]:
        current_script = script
        last_result = ExecutionResult(success=False, output="")

        for attempt in range(self.max_attempts):
            last_result = self.runner.run(current_script)
            if last_result.success:
                return current_script, last_result

            if not self._can_debug_solution(attempt):
                continue

            summary = self._summarize_traceback(last_result)
            current_script = self.debugger.debug(current_script, summary, data_info)

        return current_script, last_result

    def _can_debug_solution(self, attempt: int) -> bool:
        return (
            attempt < self.max_attempts - 1
            and self.debugger is not None
            and self.debugger.configured
        )

    def _summarize_traceback(self, result: ExecutionResult) -> str:
        if not self.summarizer or not self.summarizer.configured:
            return _normalize_text(result.traceback or result.error or "")
        try:
            return _normalize_text(
                self.summarizer.summarize(result.traceback or result.error or ""),
            )
        except Exception:
            return _normalize_text(result.traceback or result.error or "")


@dataclass
class PlanningService:
    planner: PlannerAgent

    def generate_initial_plan(self, query: str, data_info: str) -> List[str]:
        initial_step = self.planner.generate_initial(query, data_info)
        return [initial_step]

    def generate_next_step(
        self,
        plan: Sequence[str],
        query: str,
        last_result: str,
        data_info: str,
    ) -> str:
        return self.planner.generate_next(list(plan), query, last_result, data_info)

    @staticmethod
    def truncate_plan(plan: Sequence[str], decision: str) -> List[str]:
        if not decision:
            return list(plan)
        decision_normalized = decision.strip().lower()
        if decision_normalized == "add step":
            return list(plan)
        try:
            step_index = int(decision)
        except (TypeError, ValueError):
            return list(plan)

        if step_index <= 0:
            return []

        keep_count = min(len(plan), step_index)
        return list(plan[:keep_count])


@dataclass
class CodingService:
    coder: CoderAgent

    def generate_initial_code(self, plan_step: str, data_info: str) -> str:
        return self.coder.generate_initial(plan_step, data_info)

    def generate_next_code(
        self,
        plan: Sequence[str],
        query: str,
        previous_code: str,
        data_info: str,
    ) -> str:
        return self.coder.generate_next(list(plan), query, previous_code, data_info)


@dataclass
class VerificationOutcome:
    result: VerificationResult
    response: str


@dataclass
class VerificationService:
    verifier: VerifierAgent

    def evaluate(self, plan_steps: str, query: str, code: str, result_text: str) -> VerificationOutcome:
        response = _normalize_text(
            self.verifier.verify(
                plan_steps=plan_steps,
                query=query,
                code=code,
                result=result_text,
            )
        )
        normalized = response.lower()
        if "insufficient" in normalized:
            verdict = VerificationResult.INSUFFICIENT
        elif "sufficient" in normalized:
            verdict = VerificationResult.SUFFICIENT
        else:
            verdict = VerificationResult.INSUFFICIENT
        return VerificationOutcome(result=verdict, response=response)


@dataclass
class RouterService:
    router: RouterAgent

    def decide(
        self,
        plan_steps: str,
        query: str,
        last_result: str,
        data_info: str,
        num_steps: int,
    ) -> str:
        return _normalize_text(
            self.router.decide(
                plan_steps=plan_steps,
                query=query,
                last_result=last_result,
                data_info=data_info,
                num_steps=num_steps,
            )
        )


@dataclass
class FinalizationService:
    finalyzer: FinalyzerAgent

    def finalize(
        self,
        query: str,
        code: str,
        result_text: str,
        data_info: str,
        guidelines: str = "",
    ) -> str:
        return self.finalyzer.finalize(
            query=query,
            code=code,
            result=result_text,
            data_info=data_info,
            guidelines=guidelines,
        )

