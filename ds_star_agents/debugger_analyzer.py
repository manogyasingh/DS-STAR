from .base import LLMBackedAgent
from ds_star_core import extract_code_from_markdown


class AnalyzerDebuggerAgent(LLMBackedAgent):
    """Debugger agent that fixes analyzer scripts based on traceback summaries."""

    def debug(self, script: str, error_traceback: str) -> str:
        response = self.invoke(script=script, error_traceback=error_traceback)
        return extract_code_from_markdown(response)

