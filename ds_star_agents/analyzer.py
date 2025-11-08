from .base import LLMBackedAgent
from ds_star_core import extract_code_from_markdown


class AnalyzerAgent(LLMBackedAgent):
    """Analyzer agent generates Python scripts to describe data files."""

    def generate_script(self, data_file: str) -> str:
        response = self.invoke(data_file=data_file)
        return extract_code_from_markdown(response)

