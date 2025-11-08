from typing import Any

from .base import LLMBackedAgent


class TracebackSummarizerAgent(LLMBackedAgent):
    """Summarizes tracebacks before sending them to debugger agents."""

    def summarize(self, error_traceback: str) -> str:
        if not self.configured:
            return error_traceback
        try:
            response = self.invoke(error_traceback=error_traceback)
        except Exception:
            return error_traceback
        return response.strip() if response else error_traceback

