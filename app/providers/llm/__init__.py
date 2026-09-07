from collections.abc import Callable

from app.providers.llm.client import OpenAICompatibleLLM
from app.utils.text import split_text

PART_PROMPT = (
    "You are taking notes on one part of a longer meeting transcript. "
    "In bullet points, capture the topics discussed, decisions reached, action items with "
    "owners and dates, and any figures or names mentioned. Attribute points to speakers when "
    "the transcript labels them. Do not write an introduction or a conclusion, and do not "
    "invent anything: this is one section of several."
)

MERGE_HEADER = (
    "Below are notes taken from consecutive parts of a single meeting, in order. "
    "Write the final Minutes of Meeting covering the whole meeting.\n\n"
)


def get_llm_client(config: dict) -> OpenAICompatibleLLM:
    return OpenAICompatibleLLM(
        base_url=(config.get("llm_base_url") or "").strip(),
        api_key=(config.get("llm_api_key") or "").strip(),
        model=(config.get("llm_model") or "").strip(),
        temperature=_number(config.get("llm_temperature"), 0.2),
        max_tokens=int(_number(config.get("llm_max_output_tokens"), 4000)),
        timeout=int(_number(config.get("llm_timeout_seconds"), 300)),
    )


def generate_minutes(
    client: OpenAICompatibleLLM,
    transcript: str,
    prompt: str,
    chunk_chars: int,
    on_progress: Callable[[int, int], None] | None = None,
) -> str:
    """Summarise a transcript of any length.

    Transcripts that exceed the chunk size are summarised part by part and then
    merged, so meeting length is not capped by the model's context window.
    """
    chunks = split_text(transcript, chunk_chars)
    if len(chunks) == 1:
        return client.complete(prompt, f"Transcript:\n\n{transcript}")

    notes = []
    for index, chunk in enumerate(chunks, start=1):
        notes.append(f"### Part {index} of {len(chunks)}\n{client.complete(PART_PROMPT, chunk)}")
        if on_progress:
            on_progress(index, len(chunks))
    return client.complete(prompt, MERGE_HEADER + "\n\n".join(notes))


def _number(value, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback
