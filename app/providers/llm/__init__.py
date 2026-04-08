from app.providers.llm.openai_compatible import OpenAICompatibleLLM
from app.models import SystemConfig


def get_llm_client() -> OpenAICompatibleLLM:
    """Return a configured LLM client using DB config (falls back to env / defaults)."""
    base_url = SystemConfig.get("llm_base_url", "https://api.openai.com/v1")
    api_key = SystemConfig.get("llm_api_key", "")
    model = SystemConfig.get("llm_model", "gpt-4o-mini")
    return OpenAICompatibleLLM(base_url=base_url, api_key=api_key, model=model)
