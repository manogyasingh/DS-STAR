from typing import Any, List

from ds_star_core import extract_code_from_markdown, format_plan_steps


class CoderAgent:
    """Coder agent responsible for implementing plan steps into Python code."""

    def __init__(self, llm_client: Any, initial_prompt: str = "", next_prompt: str = "", logger=None):
        self.llm_client = llm_client
        self.initial_prompt = initial_prompt or ""
        self.next_prompt = next_prompt or ""
        self.logger = logger
        self.name = "CoderAgent"

    @property
    def initial_configured(self) -> bool:
        return bool(self.initial_prompt)

    @property
    def next_configured(self) -> bool:
        return bool(self.next_prompt)

    def generate_initial(self, plan_step: str, data_info: str) -> str:
        if not self.initial_prompt:
            raise ValueError("Initial coder prompt not configured.")

        if self.logger:
            self.logger.agent_start(self.name, details={"method": "generate_initial"})
            self.logger.llm_call_start(self.name)

        try:
            response = self.llm_client.generate(
                self.initial_prompt,
                plan_step=plan_step,
                data_info=data_info,
            )
            result = extract_code_from_markdown(response)

            if self.logger:
                self.logger.llm_call_end(self.name, details={"code_length": len(result)})
                self.logger.agent_end(self.name, details={"method": "generate_initial"})

            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Coder initial generation failed: {str(e)}", details={"error": str(e)})
            raise

    def generate_next(
        self,
        plan: List[str],
        query: str,
        previous_code: str,
        data_info: str,
    ) -> str:
        if not self.next_prompt:
            raise ValueError("Next coder prompt not configured.")

        if self.logger:
            self.logger.agent_start(self.name, details={"method": "generate_next", "plan_length": len(plan)})
            self.logger.llm_call_start(self.name)

        try:
            previous_plans = format_plan_steps(plan[:-1]) if len(plan) > 1 else ""
            current_plan = plan[-1] if plan else ""
            response = self.llm_client.generate(
                self.next_prompt,
                previous_plans=previous_plans,
                current_plan=current_plan,
                query=query,
                previous_code=previous_code,
                data_info=data_info,
            )
            result = extract_code_from_markdown(response)

            if self.logger:
                self.logger.llm_call_end(self.name, details={"code_length": len(result)})
                self.logger.agent_end(self.name, details={"method": "generate_next"})

            return result
        except Exception as e:
            if self.logger:
                self.logger.error(f"Coder next generation failed: {str(e)}", details={"error": str(e)})
            raise

