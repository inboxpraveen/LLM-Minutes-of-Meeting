from openai import OpenAI


class OpenAICompatibleLLM:
    """Any endpoint that speaks the OpenAI chat completions API.

    Covers OpenAI, OpenRouter, Groq, Together, Fireworks, Mistral, Cerebras,
    Anthropic and Gemini compatibility endpoints, and local servers such as
    Ollama, LM Studio, vLLM and llama.cpp.
    """

    def __init__(self, base_url: str, api_key: str, model: str,
                 temperature: float = 0.2, max_tokens: int = 4000, timeout: int = 300):
        if not base_url:
            raise RuntimeError("No LLM base URL configured. Set one in Settings → LLM provider.")
        if not model:
            raise RuntimeError("No LLM model configured. Set one in Settings → LLM provider.")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = OpenAI(
            base_url=base_url, api_key=api_key or "not-needed", timeout=timeout, max_retries=3
        )

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if not response.choices:
            raise RuntimeError("The LLM returned no choices.")
        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise RuntimeError("The LLM returned an empty response.")
        return content

    def check(self) -> str:
        reply = self.complete("Reply with the single word OK.", "ping")
        return f"Model {self.model} responded: {reply[:60]}"
