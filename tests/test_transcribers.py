import pytest
from pathlib import Path
from core.registry import transcriber_registry
from core.interfaces import BaseTranscriber
from modules.transcribers.faster_whisper import FasterWhisperTranscriber
from domain.exceptions import TranscriberError

def test_transcriber_registered_successfully():
    # Assert faster_whisper is registered in the transcriber registry
    cls = transcriber_registry.get("faster_whisper")
    assert cls is FasterWhisperTranscriber
    assert issubclass(cls, BaseTranscriber)

def test_faster_whisper_scaffold_transcribes_correctly(mock_audio_path):
    # Given
    transcriber = FasterWhisperTranscriber(model_size="tiny", device="cpu")

    # When
    transcript = transcriber.transcribe(mock_audio_path)

    # Then
    assert transcript.raw_text is not None
    assert len(transcript.segments) > 0
    assert transcript.language == "en"

def test_faster_whisper_scaffold_raises_transcriber_error_on_missing_file():
    # Given
    transcriber = FasterWhisperTranscriber()
    non_existent_file = Path("non_existent_file.wav")

    # When / Then
    with pytest.raises(TranscriberError) as exc_info:
        transcriber.transcribe(non_existent_file)
    
    assert "Transcription failed" in str(exc_info.value)
