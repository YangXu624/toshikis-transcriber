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

def test_gemini_scaffold_summarizes_correctly(mocker, sample_transcript):
    # Given
    mock_genai = mocker.patch("google.generativeai.GenerativeModel")
    mock_response = mocker.MagicMock()
    mock_response.text = (
        '{"content": "This is a summary", '
        '"key_points": ["point 1"], "action_items": ["item 1"], '
        '"topics": ["topic 1"]}'
    )
    mock_genai.return_value.generate_content.return_value = mock_response

    summarizer = GeminiSummarizer(api_key="test-key", model_name="gemini-1.5-flash")

    # When
    summary = summarizer.summarize(sample_transcript)

    # Then
    assert summary.content == "This is a summary"
    assert summary.key_points == ["point 1"]
    assert summary.action_items == ["item 1"]
    assert summary.topics == ["topic 1"]
    
    mock_genai.assert_called_once_with(model_name="gemini-1.5-flash")

def test_gemini_scaffold_raises_summarizer_error_on_empty_transcript():
    # Given
    summarizer = GeminiSummarizer(api_key="test-key")
    empty_transcript = Transcript(raw_text="")

    # When / Then
    with pytest.raises(SummarizerError) as exc_info:
        summarizer.summarize(empty_transcript)

    assert "Summarization failed" in str(exc_info.value)

def test_gemini_raises_error_on_missing_api_key(mocker, sample_transcript):
    # Given
    # Clean environmental variables for the test context
    mocker.patch.dict("os.environ", {}, clear=True)
    summarizer = GeminiSummarizer(api_key="")

    # When / Then
    with pytest.raises(SummarizerError) as exc_info:
        summarizer.summarize(sample_transcript)
        
    assert "Gemini API key is missing" in str(exc_info.value)

