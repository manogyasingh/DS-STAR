from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Sequence


PROMPT_KEYS = [
    "analyzer",
    "planner_initial",
    "planner_next",
    "coder_initial",
    "coder_next",
    "verifier",
    "router",
    "debugger_summarize",
    "debugger_analyzer",
    "debugger_solution",
    "finalyzer",
]


def load_prompts(prompts_dir: str) -> Dict[str, str]:
    """
    Load prompt templates from a directory containing .txt files.
    Missing prompts fall back to empty strings.
    """
    prompts = {key: "" for key in PROMPT_KEYS}
    base_path = Path(prompts_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")

    for path in base_path.glob("*.txt"):
        prompts[path.stem] = path.read_text()
    return prompts


def extract_code_from_markdown(text: str) -> str:
    """
    Extract the first fenced code block from markdown text; fallback to raw text.
    """
    import re

    if not text:
        return ""

    patterns = [
        r"```python\s*(.*?)```",
        r"```\s*(.*?)```",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[0].strip()
    return text.strip()


def _to_lines(data_descriptions: Sequence) -> Iterable[str]:
    for desc in data_descriptions:
        file_path = getattr(desc, "file_path", None) or desc.get("file_path")
        description = getattr(desc, "description", None) or desc.get("description")
        if file_path:
            yield f"## {file_path}"
        if description:
            yield str(description).strip()
        yield ""


def format_data_info(data_descriptions: Sequence) -> str:
    """
    Format data descriptions for prompting.
    """
    if not data_descriptions:
        return ""
    return "\n".join(_to_lines(data_descriptions)).strip()


def format_plan_steps(plan: Sequence[str]) -> str:
    """
    Format plan steps as a numbered list.
    """
    if not plan:
        return ""
    return "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan))

