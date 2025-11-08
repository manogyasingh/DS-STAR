from typing import Any, Optional


class LLMBackedAgent:
    """
    Base class for agents that rely on an LLM client and a prompt template.
    """

    def __init__(self, llm_client: Any, prompt: str = "", name: Optional[str] = None):
        self.llm_client = llm_client
        self.prompt = prompt or ""
        self.name = name or self.__class__.__name__

    @property
    def configured(self) -> bool:
        return bool(self.prompt)

    def invoke(self, **kwargs) -> str:
        if not self.prompt:
            raise ValueError(f"Prompt not configured for agent '{self.name}'.")
        return self.llm_client.generate(self.prompt, **kwargs)

