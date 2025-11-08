from typing import Any


class VerifierAgent:
    """Verifier agent evaluates whether the current plan sufficiently answers the query."""

    def __init__(self, llm_client: Any, prompt: str = ""):
        self.llm_client = llm_client
        self.prompt = prompt or ""

    @property
    def configured(self) -> bool:
        return bool(self.prompt)

    def verify(self, plan_steps: str, query: str, code: str, result: str) -> str:
        if not self.prompt:
            raise ValueError("Verifier prompt not configured.")
        response = self.llm_client.generate(
            self.prompt,
            plan_steps=plan_steps,
            query=query,
            code=code,
            result=result,
        )
        return response.strip()

