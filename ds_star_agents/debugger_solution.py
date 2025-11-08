from .base import LLMBackedAgent
from ds_star_core import extract_code_from_markdown


class SolutionDebuggerAgent(LLMBackedAgent):
    """Debugger agent that fixes solution scripts using traceback and data context."""

    def debug(self, script: str, error_traceback: str, data_info: str) -> str:
        response = self.invoke(
            script=script,
            error_traceback=error_traceback,
            data_info=data_info,
        )
        return extract_code_from_markdown(response)

