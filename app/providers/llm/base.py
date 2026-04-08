from abc import ABC, abstractmethod
from typing import List, Dict


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def complete(self, messages: List[Dict], **kwargs) -> str:
        """Send messages and return the assistant's text response."""
        ...

    def generate_minutes(self, transcript: str) -> str:
        """Generate structured minutes of meeting from a transcript."""
        system_prompt = (
            "You are an expert meeting analyst. Given a meeting transcript, "
            "produce well-structured **Minutes of Meeting** in Markdown with:\n\n"
            "## Meeting Summary\n"
            "A concise 2-4 sentence overview.\n\n"
            "## Attendees\n"
            "Names/roles mentioned (or 'Not specified').\n\n"
            "## Key Discussion Points\n"
            "Bullet list of main topics discussed.\n\n"
            "## Decisions Made\n"
            "Numbered list of decisions reached.\n\n"
            "## Action Items\n"
            "Table with columns: | Task | Owner | Due Date |\n\n"
            "## Next Steps\n"
            "What happens after this meeting.\n\n"
            "Be concise, professional, and accurate. Use only information from the transcript."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript:\n\n{transcript}"},
        ]
        return self.complete(messages)
