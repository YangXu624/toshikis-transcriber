import pytest
from core.registry import structurizer_registry
from core.interfaces import BaseStructurizer
from modules.structurizers.gemini import GeminiStructurizer
from domain.models import Transcript
from domain.exceptions import StructurizerError

def test_structurizer_registered_successfully():
    cls = structurizer_registry.get("gemini")
    assert cls is GeminiStructurizer
    assert issubclass(cls, BaseStructurizer)

def test_gemini_scaffold_structurizes_correctly(mocker, sample_transcript):
    mock_genai = mocker.patch("google.generativeai.GenerativeModel")
    mock_response = mocker.MagicMock()
    mock_response.text = (
        '{"presentation": "This is presentation text", '
        '"q_and_a": "[Question]: Is it? [Answer]: Yes."}'
    )
    mock_genai.return_value.generate_content.return_value = mock_response

    structurizer = GeminiStructurizer(api_key="test-key", model_name="gemini-2.5-flash")

    pres_text, qa_text = structurizer.structurize(sample_transcript)

    assert pres_text == "This is presentation text"
    assert qa_text == "[Question]: Is it?\n[Answer]: Yes."
    mock_genai.assert_called_once_with(model_name="gemini-2.5-flash")

def test_gemini_scaffold_raises_structurizer_error_on_empty_transcript():
    structurizer = GeminiStructurizer(api_key="test-key")
    empty_transcript = Transcript(raw_text="")

    with pytest.raises(StructurizerError) as exc_info:
        structurizer.structurize(empty_transcript)

    assert "Structuring failed" in str(exc_info.value)

def test_gemini_raises_error_on_missing_api_key(mocker, sample_transcript):
    mocker.patch.dict("os.environ", {}, clear=True)
    structurizer = GeminiStructurizer(api_key="")

    with pytest.raises(StructurizerError) as exc_info:
        structurizer.structurize(sample_transcript)
        
    assert "Gemini API key is missing" in str(exc_info.value)
