from typing import Any, Optional


class VerifierAgent:
    """Verifier agent evaluates whether the current plan sufficiently answers the query."""

    def __init__(self, llm_client: Any, prompt: str = "", logger=None):
        self.llm_client = llm_client
        self.prompt = prompt or ""
        self.logger = logger
        self.name = "VerifierAgent"

    @property
    def configured(self) -> bool:
        return bool(self.prompt)

    def verify(self, plan_steps: str, query: str, code: str, result: str) -> str:
        if not self.prompt:
            raise ValueError("Verifier prompt not configured.")

        # Log agent start
        if self.logger:
            details = {
                "prompt_length": len(self.prompt),
                "plan_steps_length": len(plan_steps),
                "query_length": len(query),
                "code_length": len(code),
                "result_length": len(result),
            }
            self.logger.agent_start(self.name, details=details)
            self.logger.llm_call_start(self.name, details=details)

        try:
            response = self.llm_client.generate(
                self.prompt,
                plan_steps=plan_steps,
                query=query,
                code=code,
                result=result,
            )

            # Log agent end
            if self.logger:
                details = {"response_length": len(response) if response else 0}
                self.logger.llm_call_end(self.name, details=details)
                self.logger.agent_end(self.name, details=details)

            return response.strip()
        except Exception as e:
            # Log errors
            if self.logger:
                self.logger.error(f"Agent '{self.name}' failed: {str(e)}", details={"error": str(e)})
            raise

