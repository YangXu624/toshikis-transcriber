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

def test_faster_whisper_scaffold_transcribes_correctly(mocker, mock_audio_path):
    # Given
    mock_whisper = mocker.patch("faster_whisper.WhisperModel")
    
    mock_segment = mocker.MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 2.5
    mock_segment.text = "Hello and welcome to this session."
    
    mock_info = mocker.MagicMock()
    mock_info.language = "en"
    
    mock_whisper.return_value.transcribe.return_value = ([mock_segment], mock_info)
    
    transcriber = FasterWhisperTranscriber(model_size="tiny", device="cpu")

    # When
    transcript = transcriber.transcribe(mock_audio_path)

    # Then
    assert transcript.raw_text == "Hello and welcome to this session."
    assert len(transcript.segments) == 1
    assert transcript.segments[0].start_time == 0.0
    assert transcript.segments[0].end_time == 2.5
    assert transcript.segments[0].text == "Hello and welcome to this session."
    assert transcript.language == "en"
    
    mock_whisper.assert_called_once_with("tiny", device="cpu", compute_type="int8")
    mock_whisper.return_value.transcribe.assert_called_once_with(str(mock_audio_path), beam_size=5)

def test_faster_whisper_scaffold_raises_transcriber_error_on_missing_file():
    # Given
    transcriber = FasterWhisperTranscriber()
    non_existent_file = Path("non_existent_file.wav")

    # When / Then
    with pytest.raises(TranscriberError) as exc_info:
        transcriber.transcribe(non_existent_file)
    
    assert "Transcription failed" in str(exc_info.value)

def test_faster_whisper_raises_error_on_initialization_failure(mocker, mock_audio_path):
    # Given
    mocker.patch("faster_whisper.WhisperModel", side_effect=RuntimeError("CUDA memory error"))
    transcriber = FasterWhisperTranscriber()

    # When / Then
    with pytest.raises(TranscriberError) as exc_info:
        transcriber.transcribe(mock_audio_path)
    
    assert "Failed to load WhisperModel" in str(exc_info.value)

