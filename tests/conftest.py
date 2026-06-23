import pytest
from pathlib import Path
from datetime import datetime
from domain.models import Transcript, TranscriptSegment, Summary, Metadata, Session
from core.interfaces import BaseTranscriber, BaseSummarizer, BaseStorage

@pytest.fixture
def mock_audio_path(tmp_path) -> Path:
    audio_file = tmp_path / "test_session.wav"
    audio_file.write_text("dummy wave content")
    return audio_file

@pytest.fixture
def sample_transcript() -> Transcript:
    return Transcript(
        raw_text="This is a test transcription segment.",
        segments=[
            TranscriptSegment(
                start_time=0.0,
                end_time=3.5,
                text="This is a test transcription segment.",
                speaker="Speaker A"
            )
        ],
        language="en"
    )

@pytest.fixture
def sample_summary() -> Summary:
    return Summary(
        content="This is a summarized test session description.",
        key_points=["Point one", "Point two"],
        action_items=["Task A", "Task B"],
        topics=["Testing", "Orchestration"]
    )

@pytest.fixture
def sample_session_id() -> str:
    return "test-session-uuid-1234"

@pytest.fixture
def sample_metadata(sample_session_id) -> Metadata:
    return Metadata(
        session_id=sample_session_id,
        created_at=datetime(2026, 6, 23, 12, 0, 0),
        title="Architecture Review",
        duration_seconds=120.0
    )

@pytest.fixture
def sample_session(sample_session_id, sample_metadata, sample_transcript, sample_summary) -> Session:
    return Session(
        session_id=sample_session_id,
        metadata=sample_metadata,
        transcript=sample_transcript,
        summary=sample_summary
    )

# --- Abstract Mock Adapters for Orchestrator Tests ---

class StubTranscriber(BaseTranscriber):
    def __init__(self, transcript_to_return: Transcript):
        self.transcript_to_return = transcript_to_return
        self.called_with = None

    def transcribe(self, audio_path: Path) -> Transcript:
        self.called_with = audio_path
        return self.transcript_to_return

class StubSummarizer(BaseSummarizer):
    def __init__(self, summary_to_return: Summary):
        self.summary_to_return = summary_to_return
        self.called_with = None

    def summarize(self, transcript: Transcript) -> Summary:
        self.called_with = transcript
        return self.summary_to_return

class StubStorage(BaseStorage):
    def __init__(self):
        self.saved_session = None
        self.sessions_db = {}

    def save(self, session: Session) -> None:
        self.saved_session = session
        self.sessions_db[session.session_id] = session

    def load(self, session_id: str) -> Session:
        if session_id not in self.sessions_db:
            raise KeyError(f"Session {session_id} not found.")
        return self.sessions_db[session_id]

@pytest.fixture
def stub_transcriber(sample_transcript) -> StubTranscriber:
    return StubTranscriber(sample_transcript)

@pytest.fixture
def stub_summarizer(sample_summary) -> StubSummarizer:
    return StubSummarizer(sample_summary)

@pytest.fixture
def stub_storage() -> StubStorage:
    return StubStorage()
