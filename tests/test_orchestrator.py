import pytest
from core.orchestrator import SessionOrchestrator
from domain.exceptions import TranscriberError, SummarizerError, StorageError
from tests.conftest import StubTranscriber, StubSummarizer, StubStorage

def test_orchestrator_pipeline_success(
    mock_audio_path,
    stub_transcriber,
    stub_summarizer,
    stub_storage,
    sample_transcript,
    sample_summary
):
    # Given
    orchestrator = SessionOrchestrator(
        transcriber=stub_transcriber,
        summarizer=stub_summarizer,
        storage=stub_storage
    )

    # When
    session = orchestrator.run_pipeline(
        audio_path=mock_audio_path,
        title="Successful Meeting"
    )

    # Then
    assert session.session_id is not None
    assert session.metadata.title == "Successful Meeting"
    
    # Assert coordinates were called with appropriate types/arguments
    assert stub_transcriber.called_with == mock_audio_path
    assert stub_summarizer.called_with == sample_transcript.raw_text
    assert stub_storage.saved_session == session
    
    # Assert session payload is correct
    assert session.transcript == sample_transcript
    assert session.summary == sample_summary

def test_orchestrator_propagates_transcriber_error(
    mock_audio_path,
    stub_summarizer,
    stub_storage,
    sample_transcript
):
    # Given
    class BrokenTranscriber(StubTranscriber):
        def transcribe(self, audio_path):
            raise TranscriberError("Failed to initialize whisper models.")

    orchestrator = SessionOrchestrator(
        transcriber=BrokenTranscriber(sample_transcript),
        summarizer=stub_summarizer,
        storage=stub_storage
    )

    # When / Then
    with pytest.raises(TranscriberError) as exc_info:
        orchestrator.run_pipeline(mock_audio_path)
    assert "Failed to initialize whisper" in str(exc_info.value)
    # Ensure summarizer and storage were not called due to crash in stage 2
    assert stub_summarizer.called_with is None
    assert stub_storage.saved_session is None

def test_orchestrator_propagates_summarizer_error(
    mock_audio_path,
    stub_transcriber,
    stub_storage,
    sample_summary
):
    # Given
    class BrokenSummarizer(StubSummarizer):
        def summarize(self, transcript):
            raise SummarizerError("Gemini API connection timeout.")

    orchestrator = SessionOrchestrator(
        transcriber=stub_transcriber,
        summarizer=BrokenSummarizer(sample_summary),
        storage=stub_storage
    )

    # When / Then
    with pytest.raises(SummarizerError) as exc_info:
        orchestrator.run_pipeline(mock_audio_path)
    assert "Gemini API connection timeout" in str(exc_info.value)
    # Ensure storage was not called due to crash in stage 3
    assert stub_storage.saved_session is None

def test_orchestrator_propagates_storage_error(
    mock_audio_path,
    stub_transcriber,
    stub_summarizer
):
    # Given
    class BrokenStorage(StubStorage):
        def save(self, session):
            raise StorageError("Disk full error.")

    orchestrator = SessionOrchestrator(
        transcriber=stub_transcriber,
        summarizer=stub_summarizer,
        storage=BrokenStorage()
    )

    # When / Then
    with pytest.raises(StorageError) as exc_info:
        orchestrator.run_pipeline(mock_audio_path)
    assert "Disk full error" in str(exc_info.value)
