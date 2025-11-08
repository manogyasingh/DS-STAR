from typing import Any

from ds_star_core import extract_code_from_markdown


class FinalyzerAgent:
    """Finalyzer agent formats the final solution script/output."""

    def __init__(self, llm_client: Any, prompt: str = ""):
        self.llm_client = llm_client
        self.prompt = prompt or ""

    @property
    def configured(self) -> bool:
        return bool(self.prompt)

    def finalize(
        self,
        query: str,
        code: str,
        result: str,
        data_info: str,
        guidelines: str = "",
    ) -> str:
        if not self.prompt:
            return code
        response = self.llm_client.generate(
            self.prompt,
            query=query,
            code=code,
            result=result,
            data_info=data_info,
            guidelines=guidelines or "Print the answer clearly and concisely.",
        )
        return extract_code_from_markdown(response)

