from dataclasses import dataclass
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.interfaces import BaseTranscriber, BaseSummarizer, BaseStorage
from core.pipeline import PipelineStep, SessionPipeline
from domain.models import Session, Metadata

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class PipelineContext:
    """Immutable data context passing state between pipeline steps."""
    audio_path: Path
    session: Session

class SessionOrchestrator:
    """Orchestrates the AI session capture, transcription, summarization, and storage lifecycle.

    This orchestrator coordinates the sequence of execution using a SessionPipeline, which
    guarantees step isolated errors and execution tracing.
    """

    def __init__(
        self,
        transcriber: BaseTranscriber,
        summarizer: BaseSummarizer,
        storage: BaseStorage
    ):
        """Construct the orchestrator and configure its sequential steps."""
        self._transcriber = transcriber
        self._summarizer = summarizer
        self._storage = storage

        # Define pipeline structure
        self._pipeline = SessionPipeline()
        self._pipeline.add_step(
            PipelineStep("Transcription", self._transcribe_step)
        ).add_step(
            PipelineStep("Summarization", self._summarize_step)
        ).add_step(
            PipelineStep("Archiving", self._archive_step)
        )

    def _capture_audio(self, audio_path: Path) -> str:
        """Validation stage before entering the pipeline."""
        logger.info(f"[Capture Stage] Validating audio source at {audio_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio source file does not exist: {audio_path}")
        
        session_id = str(uuid.uuid4())
        logger.info(f"[Capture Stage] Generated session ID: {session_id}")
        return session_id

    def _transcribe_step(self, context: PipelineContext) -> PipelineContext:
        """Step action to execute audio transcription."""
        transcript = self._transcriber.transcribe(context.audio_path)
        updated_session = context.session.with_transcript(transcript)
        return PipelineContext(audio_path=context.audio_path, session=updated_session)

    def _summarize_step(self, context: PipelineContext) -> PipelineContext:
        """Step action to execute text summarization."""
        if not context.session.transcript:
            raise ValueError("Summarization failed: Transcript is missing from session state.")
        summary = self._summarizer.summarize(context.session.transcript)
        updated_session = context.session.with_summary(summary)
        return PipelineContext(audio_path=context.audio_path, session=updated_session)

    def _archive_step(self, context: PipelineContext) -> PipelineContext:
        """Step action to persist session to database storage."""
        self._storage.save(context.session)
        return context

    def run_pipeline(self, audio_path: Path, title: Optional[str] = None) -> Session:
        """Run the complete pipeline over the configured session context."""
        logger.info("=== Starting AI Session Capture & Summarisation Pipeline ===")

        # 1. Capture setup
        session_id = self._capture_audio(audio_path)
        
        metadata = Metadata(
            session_id=session_id,
            title=title or audio_path.stem,
            created_at=datetime.now(timezone.utc)
        )
        initial_session = Session(session_id=session_id, metadata=metadata)

        # 2. Assemble context and execute sequential steps
        initial_context = PipelineContext(audio_path=audio_path, session=initial_session)
        final_context = self._pipeline.run(initial_context)

        logger.info(f"=== Pipeline completed successfully for session {session_id} ===")
        return final_context.session

