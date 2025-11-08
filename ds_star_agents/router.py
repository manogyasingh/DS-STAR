from typing import Any


class RouterAgent:
    """Router agent decides whether to add a new plan step or backtrack."""

    def __init__(self, llm_client: Any, prompt: str = ""):
        self.llm_client = llm_client
        self.prompt = prompt or ""

    @property
    def configured(self) -> bool:
        return bool(self.prompt)

    def decide(
        self,
        plan_steps: str,
        query: str,
        last_result: str,
        data_info: str,
        num_steps: int,
    ) -> str:
        if not self.prompt:
            raise ValueError("Router prompt not configured.")
        response = self.llm_client.generate(
            self.prompt,
            plan_steps=plan_steps,
            query=query,
            last_result=last_result,
            data_info=data_info,
            num_steps=num_steps,
        )
        return response.strip()

