from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

@dataclass(frozen=True)
class TranscriptSegment:
    """Represents a chunk of transcribed audio with timing information."""
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None

@dataclass(frozen=True)
class Transcript:
    """Represents the complete transcription result."""
    raw_text: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    language: Optional[str] = None

@dataclass(frozen=True)
class Summary:
    """Represents the generated session summary."""
    content: str
    key_points: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class Metadata:
    """Represents context metadata for the session capture."""
    session_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    title: Optional[str] = None
    duration_seconds: Optional[float] = None
    extra_info: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Session:
    """Represents the entire session lifecycle containing metadata, transcript, and summary."""
    session_id: str
    metadata: Metadata
    transcript: Optional[Transcript] = None
    summary: Optional[Summary] = None

    def with_transcript(self, transcript: Transcript) -> 'Session':
        """Return a new Session instance with the transcript updated."""
        return Session(
            session_id=self.session_id,
            metadata=self.metadata,
            transcript=transcript,
            summary=self.summary
        )

    def with_summary(self, summary: Summary) -> 'Session':
        """Return a new Session instance with the summary updated."""
        return Session(
            session_id=self.session_id,
            metadata=self.metadata,
            transcript=self.transcript,
            summary=summary
        )
