import pytest
from core.registry import summarizer_registry
from core.interfaces import BaseSummarizer
from modules.summarizers.gemini import GeminiSummarizer
from domain.models import Transcript
from domain.exceptions import SummarizerError

def test_summarizer_registered_successfully():
    # Assert gemini is registered in the summarizer registry
    cls = summarizer_registry.get("gemini")
    assert cls is GeminiSummarizer
    assert issubclass(cls, BaseSummarizer)

def test_gemini_scaffold_summarizes_correctly(sample_transcript):
    # Given
    summarizer = GeminiSummarizer(api_key="test-key", model_name="gemini-1.5-flash")

    # When
    summary = summarizer.summarize(sample_transcript)

    # Then
    assert summary.content is not None
    assert len(summary.key_points) > 0
    assert len(summary.topics) > 0

def test_gemini_scaffold_raises_summarizer_error_on_empty_transcript():
    # Given
    summarizer = GeminiSummarizer()
    empty_transcript = Transcript(raw_text="")

    # When / Then
    with pytest.raises(SummarizerError) as exc_info:
        summarizer.summarize(empty_transcript)

    assert "Summarization failed" in str(exc_info.value)
