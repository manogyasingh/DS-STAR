"""Agent implementations for the LangGraph-based DS-STAR framework."""

from dataclasses import dataclass
from typing import Any, Dict

from .analyzer import AnalyzerAgent
from .planner import PlannerAgent
from .coder import CoderAgent
from .verifier import VerifierAgent
from .router import RouterAgent
from .debugger_analyzer import AnalyzerDebuggerAgent
from .debugger_solution import SolutionDebuggerAgent
from .debugger_summarizer import TracebackSummarizerAgent
from .finalyzer import FinalyzerAgent


@dataclass
class AgentBundle:
    """Convenience container that holds all agent instances."""

    analyzer: AnalyzerAgent
    planner: PlannerAgent
    coder: CoderAgent
    verifier: VerifierAgent
    router: RouterAgent
    analyzer_debugger: AnalyzerDebuggerAgent
    solution_debugger: SolutionDebuggerAgent
    traceback_summarizer: TracebackSummarizerAgent
    finalyzer: FinalyzerAgent

    @classmethod
    def create(cls, llm_client: Any, prompts: Dict[str, str], logger=None) -> "AgentBundle":
        return cls(
            analyzer=AnalyzerAgent(llm_client, prompts.get("analyzer", ""), logger=logger),
            planner=PlannerAgent(
                llm_client,
                initial_prompt=prompts.get("planner_initial", ""),
                next_prompt=prompts.get("planner_next", ""),
                logger=logger,
            ),
            coder=CoderAgent(
                llm_client,
                initial_prompt=prompts.get("coder_initial", ""),
                next_prompt=prompts.get("coder_next", ""),
                logger=logger,
            ),
            verifier=VerifierAgent(llm_client, prompts.get("verifier", ""), logger=logger),
            router=RouterAgent(llm_client, prompts.get("router", ""), logger=logger),
            analyzer_debugger=AnalyzerDebuggerAgent(llm_client, prompts.get("debugger_analyzer", ""), logger=logger),
            solution_debugger=SolutionDebuggerAgent(llm_client, prompts.get("debugger_solution", ""), logger=logger),
            traceback_summarizer=TracebackSummarizerAgent(
                llm_client,
                prompts.get("debugger_summarize", ""),
                logger=logger,
            ),
            finalyzer=FinalyzerAgent(llm_client, prompts.get("finalyzer", ""), logger=logger),
        )

    def update_prompt(self, agent_name: str, prompt: str) -> None:
        if agent_name == "analyzer":
            self.analyzer.prompt = prompt
        elif agent_name == "planner_initial":
            self.planner.initial_prompt = prompt
        elif agent_name == "planner_next":
            self.planner.next_prompt = prompt
        elif agent_name == "coder_initial":
            self.coder.initial_prompt = prompt
        elif agent_name == "coder_next":
            self.coder.next_prompt = prompt
        elif agent_name == "verifier":
            self.verifier.prompt = prompt
        elif agent_name == "router":
            self.router.prompt = prompt
        elif agent_name == "debugger_analyzer":
            self.analyzer_debugger.prompt = prompt
        elif agent_name == "debugger_solution":
            self.solution_debugger.prompt = prompt
        elif agent_name == "debugger_summarize":
            self.traceback_summarizer.prompt = prompt
        elif agent_name == "finalyzer":
            self.finalyzer.prompt = prompt
        else:
            raise ValueError(f"Unknown agent: {agent_name}")


__all__ = [
    "AgentBundle",
    "AnalyzerAgent",
    "PlannerAgent",
    "CoderAgent",
    "VerifierAgent",
    "RouterAgent",
    "AnalyzerDebuggerAgent",
    "SolutionDebuggerAgent",
    "TracebackSummarizerAgent",
    "FinalyzerAgent",
]

