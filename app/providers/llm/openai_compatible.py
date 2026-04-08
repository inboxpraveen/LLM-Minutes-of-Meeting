from typing import List, Dict, Any
from openai import OpenAI
from app.providers.llm.base import BaseLLMProvider


class OpenAICompatibleLLM(BaseLLMProvider):
    """
    Works with any OpenAI-compatible provider:
    OpenAI, OpenRouter, Groq, Together, Azure, Gemini (via compat endpoint), etc.

    Usage:
        client = OpenAICompatibleLLM(
            base_url="https://openrouter.ai/api/v1",
            api_key="sk-...",
            model="anthropic/claude-opus-4",
        )
        result = client.complete(messages=[{"role": "user", "content": "Hello"}])
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        self.model = model
        self._client = OpenAI(base_url=base_url, api_key=api_key or "none")

    def complete(self, messages: List[Dict], **kwargs: Any) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def complete_with_reasoning(self, messages: List[Dict], **kwargs: Any) -> Dict:
        """Returns both content and reasoning_details (for providers that support it)."""
        extra_body = kwargs.pop("extra_body", {"reasoning": {"enabled": True}})
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            extra_body=extra_body,
            **kwargs,
        )
        msg = response.choices[0].message
        return {
            "content": msg.content or "",
            "reasoning_details": getattr(msg, "reasoning_details", None),
        }
