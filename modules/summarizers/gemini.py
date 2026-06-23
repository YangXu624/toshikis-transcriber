import logging

from core.interfaces import BaseSummarizer
from core.registry import summarizer_registry
from domain.models import Transcript, Summary
from domain.exceptions import SummarizerError

logger = logging.getLogger(__name__)

@summarizer_registry.register("gemini")
class GeminiSummarizer(BaseSummarizer):
    """Adapter for Google Gemini summarization API.

    This adapter manages third-party API executions, wraps API exceptions,
    and maps responses back to domain Summary objects.
    """

    def __init__(
        self,
        api_key: str = "",
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.2
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        logger.info(
            f"GeminiSummarizer initialized with model={model_name}, "
            f"temperature={temperature}, api_key_length={len(api_key)}"
        )

    def summarize(self, transcript: Transcript) -> Summary:
        """Stub summarization logic converting a Transcript into a Summary.

        In a future step, this will load the google-generativeai SDK and perform
        actual API calls.
        """
        logger.info("Mock summarizing transcript using Gemini...")

        try:
            # Basic validation
            if not transcript.raw_text:
                raise ValueError("Transcript text is empty; nothing to summarize.")

            # Return mock domain summary for the scaffold
            return Summary(
                content=(
                    "This session discussed software architecture and modular systems design. "
                    "The team aligned on using clean architecture principles, constructor-based "
                    "dependency injection, and dynamic adapter registries to build a highly extensible "
                    "Python codebase that can be maintained over a 5-year horizon."
                ),
                key_points=[
                    "Clean architecture decouples core domain logic from Whisper/Gemini implementations.",
                    "Constructor dependency injection facilitates simple unit testing.",
                    "Adapter registries open the codebase to extensions without modifying existing code."
                ],
                action_items=[
                    "Implement Faster-Whisper transcriber adapter in the next iteration.",
                    "Implement Google Gemini API summarizer adapter in the next iteration.",
                    "Write automated test cases in tests/ directory."
                ],
                topics=["Clean Architecture", "SOLID Principles", "Session Scaffolding"]
            )
            
        except Exception as e:
            logger.error(f"Error during summarization: {e}")
            # Wrap third-party and standard library exceptions into our custom domain exception
            raise SummarizerError(f"Summarization failed: {str(e)}") from e
