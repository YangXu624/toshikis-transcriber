from abc import ABC, abstractmethod
from pathlib import Path
from domain.models import Transcript, Summary, Session

class BaseTranscriber(ABC):
    """Interface for transcription adapters."""

    @abstractmethod
    def transcribe(self, audio_path: Path) -> Transcript:
        """Transcribe audio from the given file path.

        Args:
            audio_path: The filesystem path to the audio file.

        Returns:
            A Transcript object containing text and segment details.

        Raises:
            TranscriberError: If the transcription process fails.
        """
        pass

class BaseSummarizer(ABC):
    """Interface for summarization adapters."""

    @abstractmethod
    def summarize(self, transcript: Transcript) -> Summary:
        """Generate a summary of the provided transcript.

        Args:
            transcript: The transcript data to summarize.

        Returns:
            A Summary object containing content, key points, etc.

        Raises:
            SummarizerError: If the summarization process fails.
        """
        pass

class BaseStorage(ABC):
    """Interface for session storage adapters."""

    @abstractmethod
    def save(self, session: Session) -> None:
        """Persist a Session object to storage.

        Args:
            session: The Session domain model instance to save.

        Raises:
            StorageError: If storage serialization/write fails.
        """
        pass

    @abstractmethod
    def load(self, session_id: str) -> Session:
        """Retrieve a Session object from storage.

        Args:
            session_id: The unique identifier of the session to load.

        Returns:
            A Session domain model instance.

        Raises:
            SessionNotFoundError: If the session id is not found.
            StorageError: If storage deserialization/read fails.
        """
        pass
