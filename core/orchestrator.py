import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.interfaces import BaseTranscriber, BaseSummarizer, BaseStorage
from domain.models import Session, Metadata

logger = logging.getLogger(__name__)

class SessionOrchestrator:
    """Orchestrates the AI session capture, transcription, summarization, and storage lifecycle.

    This orchestrator depends exclusively on abstract interfaces and is isolated from
    concrete implementation details like Faster-Whisper, Gemini, or local storage schemas.
    """

    def __init__(
        self,
        transcriber: BaseTranscriber,
        summarizer: BaseSummarizer,
        storage: BaseStorage
    ):
        """Construct the orchestrator with concrete dependencies injected."""
        self._transcriber = transcriber
        self._summarizer = summarizer
        self._storage = storage

    def _capture_audio(self, audio_path: Path) -> str:
        """Placeholder stage for capture.

        In a production app, this stage could perform validation on the audio file,
        compute checksums, extract stream metadata, or copy/stream the file to raw storage.
        """
        logger.info(f"[Capture Stage] Validating audio source at {audio_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio source file does not exist: {audio_path}")
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        logger.info(f"[Capture Stage] Generated session ID: {session_id}")
        return session_id

    def run_pipeline(self, audio_path: Path, title: Optional[str] = None) -> Session:
        """Run the complete transcription, summarization, and archiving pipeline.

        Args:
            audio_path: Path to the recorded audio session.
            title: An optional user-friendly name for this session.

        Returns:
            The complete populated Session domain model.
        """
        logger.info("=== Starting AI Session Capture & Summarisation Pipeline ===")

        # 1. Capture Stage
        session_id = self._capture_audio(audio_path)
        
        metadata = Metadata(
            session_id=session_id,
            title=title or audio_path.stem,
            created_at=datetime.now(timezone.utc)
        )
        session = Session(session_id=session_id, metadata=metadata)

        # 2. Transcribe Stage
        logger.info(f"[Transcription Stage] Transcribing audio from {audio_path}...")
        transcript = self._transcriber.transcribe(audio_path)
        session = session.with_transcript(transcript)
        logger.info("[Transcription Stage] Completed successfully.")

        # 3. Summarize Stage
        logger.info("[Summarization Stage] Summarizing session transcript...")
        summary = self._summarizer.summarize(transcript)
        session = session.with_summary(summary)
        logger.info("[Summarization Stage] Completed successfully.")

        # 4. Archive Stage
        logger.info(f"[Storage Stage] Archiving session {session_id} to database/storage...")
        self._storage.save(session)
        logger.info("[Storage Stage] Archiving completed successfully.")

        logger.info(f"=== Pipeline completed successfully for session {session_id} ===")
        return session
