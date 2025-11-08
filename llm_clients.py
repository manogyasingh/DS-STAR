import os
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

DEFAULT_GEMINI_MAX_OUTPUT_TOKENS = 8192


class BaseLLMClient:
    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError("Implement this method in subclass")


class OpenRouterClient(BaseLLMClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url

    def generate(self, prompt: str, **kwargs) -> str:
        import requests
        formatted_prompt = prompt.format(**kwargs) if kwargs else prompt
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant specialized in data science tasks."},
                {"role": "user", "content": formatted_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    
class GeminiClient(BaseLLMClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "models/gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        max_output_limit: Optional[int] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        genai.configure(api_key=self.api_key)
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_output_limit = max_output_limit or DEFAULT_GEMINI_MAX_OUTPUT_TOKENS
        if self.max_output_limit < self.max_tokens:
            self.max_output_limit = self.max_tokens
        self.client = genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str, **kwargs) -> str:
        formatted_prompt = prompt.format(**kwargs) if kwargs else prompt
        attempted_max_retry = False
        current_max_tokens = min(max(1, self.max_tokens), self.max_output_limit)
        initial_max_tokens = current_max_tokens

        def _invoke(max_tokens: int):
            try:
                return self.client.generate_content(
                    formatted_prompt,
                    generation_config={
                        "temperature": self.temperature,
                        "max_output_tokens": max_tokens
                    }
                )
            except Exception as exc:  # pylint: disable=broad-except
                raise RuntimeError("Gemini generation failed") from exc

        def _candidate_text(candidate):
            content = getattr(candidate, "content", None)
            if content is None:
                return ""
            parts = getattr(content, "parts", None) or []
            texts = [getattr(part, "text", "") for part in parts if getattr(part, "text", "")]
            return "".join(texts).strip()

        def _format_finish_reason(reason):
            if reason is None:
                return "None"
            name = getattr(reason, "name", None)
            value = getattr(reason, "value", None)
            if name is not None and value is not None:
                return f"{name}({value})"
            return str(reason)

        def _is_max_tokens_reason(reason) -> bool:
            if reason is None:
                return False
            name = getattr(reason, "name", None)
            if isinstance(name, str) and name.upper() == "MAX_TOKENS":
                return True
            value = getattr(reason, "value", None)
            if value == 2:
                return True
            if isinstance(reason, str) and reason.upper() == "MAX_TOKENS":
                return True
            return False

        def _feedback_details(response):
            feedback = getattr(response, "prompt_feedback", None)
            if feedback is None:
                return []
            details = []
            block_reason = getattr(feedback, "block_reason", None)
            if block_reason:
                details.append(f"block_reason={block_reason}")
            safety_ratings = getattr(feedback, "safety_ratings", None) or []
            if safety_ratings:
                ratings = ", ".join(
                    f"{getattr(r, 'category', 'unknown')}={getattr(r, 'probability', 'unknown')}"
                    for r in safety_ratings
                )
                details.append(f"safety_ratings=[{ratings}]")
            return details

        while True:
            response = _invoke(current_max_tokens)
            candidates = getattr(response, "candidates", None) or []
            for candidate in candidates:
                text = _candidate_text(candidate)
                if text:
                    if attempted_max_retry and current_max_tokens > self.max_tokens:
                        self.max_tokens = current_max_tokens
                    return text

            raw_finish_reasons = [getattr(candidate, "finish_reason", None) for candidate in candidates]
            has_max_tokens_reason = any(_is_max_tokens_reason(reason) for reason in raw_finish_reasons)
            finish_reasons_str = ", ".join(_format_finish_reason(reason) for reason in raw_finish_reasons)

            if (
                has_max_tokens_reason
                and not attempted_max_retry
                and current_max_tokens < self.max_output_limit
            ):
                attempted_max_retry = True
                current_max_tokens = min(self.max_output_limit, current_max_tokens * 2)
                continue

            feedback_details = _feedback_details(response)
            details = "; ".join(feedback_details)
            message = (
                "Gemini returned no textual content."
                f" finish_reasons=[{finish_reasons_str}]"
            )
            if attempted_max_retry:
                message += f"; attempted_max_tokens={current_max_tokens}"
            if initial_max_tokens != current_max_tokens:
                message += f"; initial_max_tokens={initial_max_tokens}"
            if details:
                message += f"; {details}"
            raise RuntimeError(message)

def create_llm_client(provider: str, **kwargs) -> BaseLLMClient:
    providers = {
        "openrouter": OpenRouterClient,
        "gemini": GeminiClient,
    }
    provider_lower = provider.lower()
    if provider_lower not in providers:
        raise ValueError(f"Unknown provider: {provider}. Choose from {list(providers.keys())}")
    return providers[provider_lower](**kwargs)
