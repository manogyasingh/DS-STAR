from typing import Any, Optional


class LLMBackedAgent:
    """
    Base class for agents that rely on an LLM client and a prompt template.
    """

    def __init__(self, llm_client: Any, prompt: str = "", name: Optional[str] = None, logger=None):
        self.llm_client = llm_client
        self.prompt = prompt or ""
        self.name = name or self.__class__.__name__
        self.logger = logger

    @property
    def configured(self) -> bool:
        return bool(self.prompt)

    def invoke(self, **kwargs) -> str:
        if not self.prompt:
            raise ValueError(f"Prompt not configured for agent '{self.name}'.")

        # Log agent start
        if self.logger:
            details = {"prompt_length": len(self.prompt), "kwargs_keys": list(kwargs.keys())}
            self.logger.agent_start(self.name, details=details)
            self.logger.llm_call_start(self.name, details=details)

        try:
            result = self.llm_client.generate(self.prompt, **kwargs)

            # Log agent end
            if self.logger:
                details = {"response_length": len(result) if result else 0}
                self.logger.llm_call_end(self.name, details=details)
                self.logger.agent_end(self.name, details=details)

            return result
        except Exception as e:
            # Log errors
            if self.logger:
                self.logger.error(f"Agent '{self.name}' failed: {str(e)}", details={"error": str(e)})
            raise

