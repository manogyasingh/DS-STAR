from typing import Any, List

from ds_star_core import format_plan_steps


class PlannerAgent:
    """Planner agent responsible for generating initial and subsequent plan steps."""

    def __init__(self, llm_client: Any, initial_prompt: str = "", next_prompt: str = "", logger=None):
        self.llm_client = llm_client
        self.initial_prompt = initial_prompt or ""
        self.next_prompt = next_prompt or ""
        self.logger = logger
        self.name = "PlannerAgent"

    @property
    def initial_configured(self) -> bool:
        return bool(self.initial_prompt)

    @property
    def next_configured(self) -> bool:
        return bool(self.next_prompt)

    def generate_initial(self, query: str, data_info: str) -> str:
        if not self.initial_prompt:
            raise ValueError("Initial planner prompt not configured.")

        if self.logger:
            self.logger.agent_start(self.name, details={"method": "generate_initial"})
            self.logger.llm_call_start(self.name)

        try:
            response = self.llm_client.generate(
                self.initial_prompt,
                query=query,
                data_info=data_info,
            )
            result = response.strip()

            if self.logger:
                self.logger.llm_call_end(self.name, details={"response_length": len(result)})
                self.logger.agent_end(self.name, details={"method": "generate_initial"})

            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Planner initial generation failed: {str(e)}", details={"error": str(e)})
            raise

    def generate_next(
        self,
        plan: List[str],
        query: str,
        last_result: str,
        data_info: str,
    ) -> str:
        if not self.next_prompt:
            raise ValueError("Next planner prompt not configured.")

        if self.logger:
            self.logger.agent_start(self.name, details={"method": "generate_next", "plan_length": len(plan)})
            self.logger.llm_call_start(self.name)

        try:
            plan_steps = format_plan_steps(plan)
            response = self.llm_client.generate(
                self.next_prompt,
                plan_steps=plan_steps,
                query=query,
                last_result=last_result,
                data_info=data_info,
            )
            result = response.strip()

            if self.logger:
                self.logger.llm_call_end(self.name, details={"response_length": len(result)})
                self.logger.agent_end(self.name, details={"method": "generate_next"})

            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Planner next generation failed: {str(e)}", details={"error": str(e)})
            raise

