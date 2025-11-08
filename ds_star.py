from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from langgraph.graph import END, START, StateGraph

from ds_star_agents import AgentBundle
from ds_star_core import format_data_info, format_plan_steps, load_prompts
from ds_star_core.execution import PythonScriptRunner
from ds_star_core.models import DSStarState, DataDescription, ExecutionResult, VerificationResult
from ds_star_core.services import (
    AnalyzerService,
    CodingService,
    FinalizationService,
    PlanningService,
    RouterService,
    SolutionExecutionService,
    VerificationOutcome,
    VerificationService,
)


class DSSTAR:
    """
    LangGraph implementation of the DS-STAR multi-agent framework.
    """

    def __init__(
        self,
        llm_client: Any,
        max_refinement_rounds: int = 10,
        max_debug_attempts: int = 3,
        use_retriever: bool = False,
        top_k_files: int = 10,
        prompts_dir: str = "prompts",
        verbose: bool = True,
    ):
        self.llm_client = llm_client
        self.max_refinement_rounds = max_refinement_rounds
        self.max_debug_attempts = max_debug_attempts
        self.use_retriever = use_retriever
        self.top_k_files = top_k_files
        self.prompts_dir = prompts_dir
        self.verbose = verbose

        self.prompts = load_prompts(prompts_dir)

        self.agents = AgentBundle.create(llm_client, self.prompts)

        self.script_runner = PythonScriptRunner()

        self.analyzer_service = AnalyzerService(
            analyzer=self.agents.analyzer,
            runner=self.script_runner,
            debugger=self.agents.analyzer_debugger,
            summarizer=self.agents.traceback_summarizer,
            max_attempts=self.max_debug_attempts,
            use_retriever=self.use_retriever,
            top_k_files=self.top_k_files,
        )
        self.execution_service = SolutionExecutionService(
            runner=self.script_runner,
            debugger=self.agents.solution_debugger,
            summarizer=self.agents.traceback_summarizer,
            max_attempts=self.max_debug_attempts,
        )
        self.planning_service = PlanningService(self.agents.planner)
        self.coding_service = CodingService(self.agents.coder)
        self.verification_service = VerificationService(self.agents.verifier)
        self.router_service = RouterService(self.agents.router)
        self.finalization_service = FinalizationService(self.agents.finalyzer)

        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(DSStarState)

        graph.add_node("analyze", self._node_analyze)
        graph.add_node("planner_initial", self._node_planner_initial)
        graph.add_node("coder_initial", self._node_coder_initial)
        graph.add_node("execute", self._node_execute)
        graph.add_node("verify", self._node_verify)
        graph.add_node("router", self._node_router)
        graph.add_node("planner_next", self._node_planner_next)
        graph.add_node("coder_next", self._node_coder_next)
        graph.add_node("finalize", self._node_finalize)

        graph.add_edge(START, "analyze")
        graph.add_edge("analyze", "planner_initial")
        graph.add_edge("planner_initial", "coder_initial")
        graph.add_edge("coder_initial", "execute")
        graph.add_edge("execute", "verify")
        graph.add_conditional_edges(
            "verify",
            self._route_after_verify,
            {
                "verified": "finalize",
                "maxed": "finalize",
                "continue": "router",
            },
        )
        graph.add_edge("router", "planner_next")
        graph.add_edge("planner_next", "coder_next")
        graph.add_edge("coder_next", "execute")
        graph.add_edge("finalize", END)

        return graph.compile()

    def set_prompt(self, agent_name: str, prompt: str):
        """Set the prompt for a specific agent and update the bound agent instance."""
        if agent_name not in self.prompts:
            raise ValueError(f"Unknown agent: {agent_name}")
        self.prompts[agent_name] = prompt
        self.agents.update_prompt(agent_name, prompt)

    def execute_code(self, code: str, timeout: int = 30) -> ExecutionResult:
        """
        Execute Python code and return the result.
        """
        return self.script_runner.run(code, timeout=timeout)

    def _node_analyze(self, state: DSStarState) -> Dict[str, Any]:
        self._log("Analyzing data files...")
        data_files = state.get("data_files", [])
        query = state.get("query", "")
        data_descriptions = self.analyzer_service.analyze_files(data_files, query)
        return {"data_descriptions": data_descriptions}

    def _node_planner_initial(self, state: DSStarState) -> Dict[str, Any]:
        self._log("Generating initial plan...")
        data_info = format_data_info(state.get("data_descriptions", []))
        plan = self.planning_service.generate_initial_plan(state["query"], data_info)
        return {"plan": plan}

    def _node_coder_initial(self, state: DSStarState) -> Dict[str, Any]:
        self._log("Implementing initial plan...")
        data_info = format_data_info(state.get("data_descriptions", []))
        code = self.coding_service.generate_initial_code(state["plan"][0], data_info)
        return {"code": code, "execution_results": []}

    def _node_execute(self, state: DSStarState) -> Dict[str, Any]:
        data_info = format_data_info(state.get("data_descriptions", []))
        code_in = state.get("code", "")
        self._log("Executing solution code...")
        code, exec_result = self.execution_service.execute(code_in, data_info)
        execution_results = list(state.get("execution_results", []))
        execution_results.append(self._execution_observation(exec_result))
        return {
            "code": code,
            "last_execution": exec_result,
            "execution_results": execution_results,
        }

    def _node_verify(self, state: DSStarState) -> Dict[str, Any]:
        self._log("Verifying plan sufficiency...")
        plan_steps = format_plan_steps(state.get("plan", []))
        result_text = self._execution_observation(state.get("last_execution"))
        outcome: VerificationOutcome = self.verification_service.evaluate(
            plan_steps=plan_steps,
            query=state["query"],
            code=state.get("code", ""),
            result_text=result_text,
        )
        verification = outcome.result
        iteration = state.get("iteration", 0)
        if verification == VerificationResult.INSUFFICIENT:
            iteration += 1

        updates: Dict[str, Any] = {
            "verification": verification,
            "verifier_response": outcome.response,
            "iteration": iteration,
        }

        if verification == VerificationResult.SUFFICIENT:
            updates["finalization_reason"] = "verified"
        elif iteration >= self.max_refinement_rounds:
            updates["finalization_reason"] = "max_rounds"

        return updates

    def _route_after_verify(self, state: DSStarState) -> str:
        verification = state.get("verification")
        if verification == VerificationResult.SUFFICIENT:
            return "verified"
        if state.get("iteration", 0) >= self.max_refinement_rounds:
            return "maxed"
        return "continue"

    def _node_router(self, state: DSStarState) -> Dict[str, Any]:
        self._log("Routing next action...")
        plan_steps = format_plan_steps(state.get("plan", []))
        last_result = self._execution_observation(state.get("last_execution"))
        data_info = format_data_info(state.get("data_descriptions", []))
        decision = self.router_service.decide(
            plan_steps=plan_steps,
            query=state["query"],
            last_result=last_result,
            data_info=data_info,
            num_steps=len(state.get("plan", [])),
        )
        return {"router_decision": decision}

    def _node_planner_next(self, state: DSStarState) -> Dict[str, Any]:
        plan = self.planning_service.truncate_plan(
            state.get("plan", []),
            state.get("router_decision", "Add Step"),
        )
        self._log("Generating next plan step...")
        data_info = format_data_info(state.get("data_descriptions", []))
        last_result = self._execution_observation(state.get("last_execution"))
        next_step = self.planning_service.generate_next_step(
            plan,
            state["query"],
            last_result,
            data_info,
        )
        plan.append(next_step)
        return {"plan": plan}

    def _node_coder_next(self, state: DSStarState) -> Dict[str, Any]:
        self._log("Implementing updated plan...")
        data_info = format_data_info(state.get("data_descriptions", []))
        plan = list(state.get("plan", []))
        previous_code = state.get("code", "")
        code = self.coding_service.generate_next_code(
            plan,
            state["query"],
            previous_code,
            data_info,
        )
        return {"code": code}

    def _node_finalize(self, state: DSStarState) -> Dict[str, Any]:
        self._log("Finalizing solution...")
        data_info = format_data_info(state.get("data_descriptions", []))
        code = state.get("code", "")
        result_text = self._execution_observation(state.get("last_execution"))
        final_code = self.finalization_service.finalize(
            query=state["query"],
            code=code,
            result_text=result_text,
            data_info=data_info,
            guidelines="",
        )
        return {
            "final_code": final_code,
            "final_plan": list(state.get("plan", [])),
            "final_execution_results": list(state.get("execution_results", [])),
            "finalization_reason": state.get("finalization_reason", "verified"),
        }

    def _execution_observation(self, execution: Optional[ExecutionResult]) -> str:
        if execution is None:
            return ""
        if execution.success:
            return (execution.output or "").strip()
        return (execution.error or execution.output or "").strip()

    def _log(self, message: str):
        if self.verbose:
            print(message)

    def retrieve_relevant_files(
        self,
        query: str,
        data_descriptions: List[DataDescription],
    ) -> List[DataDescription]:
        return self.analyzer_service.select_relevant(query, data_descriptions)

    def solve(self, query: str, data_files: List[str]) -> Tuple[str, List[str], List[str]]:
        initial_state: DSStarState = {
            "query": query,
            "data_files": data_files,
            "plan": [],
            "execution_results": [],
            "iteration": 0,
        }

        final_state = self.graph.invoke(initial_state)

        final_code = final_state.get("final_code") or final_state.get("code", "")
        final_plan = final_state.get("final_plan") or final_state.get("plan", [])
        execution_results = final_state.get("final_execution_results") or final_state.get(
            "execution_results", []
        )
        return final_code, final_plan, execution_results
