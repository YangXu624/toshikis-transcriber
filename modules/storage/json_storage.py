import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from core.interfaces import BaseStorage
from core.registry import storage_registry
from domain.models import Session, Metadata, Transcript, TranscriptSegment, Summary
from domain.exceptions import StorageError, SessionNotFoundError

logger = logging.getLogger(__name__)

@storage_registry.register("json")
class LocalJsonStorage(BaseStorage):
    """Storage adapter that persists Session data as JSON files on the local filesystem."""

    def __init__(self, output_dir: str = "./data"):
        self.output_dir = Path(output_dir)
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalJsonStorage initialized with directory: {self.output_dir.resolve()}")

    def _get_file_path(self, session_id: str) -> Path:
        return self.output_dir / f"{session_id}.json"

    def save(self, session: Session) -> None:
        """Serialize and save the Session domain model to a JSON file."""
        file_path = self._get_file_path(session.session_id)
        logger.info(f"Saving session {session.session_id} to {file_path}")

        try:
            # Manual dictionary conversion to handle datetime serialization cleanly
            data = {
                "session_id": session.session_id,
                "metadata": {
                    "session_id": session.metadata.session_id,
                    "created_at": session.metadata.created_at.isoformat(),
                    "title": session.metadata.title,
                    "duration_seconds": session.metadata.duration_seconds,
                    "extra_info": session.metadata.extra_info,
                },
                "transcript": None,
                "presentation_text": session.presentation_text,
                "structured_qa_text": session.structured_qa_text,
                "summary": None
            }

            if session.transcript:
                data["transcript"] = {
                    "raw_text": session.transcript.raw_text,
                    "segments": [
                        {
                            "start_time": seg.start_time,
                            "end_time": seg.end_time,
                            "text": seg.text,
                            "speaker": seg.speaker
                        } for seg in session.transcript.segments
                    ],
                    "language": session.transcript.language
                }

            if session.summary:
                data["summary"] = {
                    "content": session.summary.content,
                    "key_points": session.summary.key_points,
                    "action_items": session.summary.action_items,
                    "topics": session.summary.topics
                }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            # Write presentation and structured Q&A to separate text files
            if session.presentation_text is not None:
                pres_file = self.output_dir / f"{session.session_id}_presentation.txt"
                pres_file.write_text(session.presentation_text, encoding="utf-8")
                
            if session.structured_qa_text is not None:
                qa_file = self.output_dir / f"{session.session_id}_q_and_a.txt"
                qa_file.write_text(session.structured_qa_text, encoding="utf-8")
                
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
            raise StorageError(f"Failed to save session to disk: {str(e)}") from e

    def load(self, session_id: str) -> Session:
        """Load and deserialize a Session domain model from a JSON file."""
        file_path = self._get_file_path(session_id)
        logger.info(f"Loading session {session_id} from {file_path}")

        if not file_path.exists():
            raise SessionNotFoundError(f"Session file '{file_path}' does not exist.")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct Metadata
            meta_data = data["metadata"]
            created_at = datetime.fromisoformat(meta_data["created_at"])
            metadata = Metadata(
                session_id=meta_data["session_id"],
                created_at=created_at,
                title=meta_data.get("title"),
                duration_seconds=meta_data.get("duration_seconds"),
                extra_info=meta_data.get("extra_info", {})
            )

            # Reconstruct Transcript
            transcript = None
            if data.get("transcript"):
                t_data = data["transcript"]
                segments = [
                    TranscriptSegment(
                        start_time=seg["start_time"],
                        end_time=seg["end_time"],
                        text=seg["text"],
                        speaker=seg.get("speaker")
                    ) for seg in t_data.get("segments", [])
                ]
                transcript = Transcript(
                    raw_text=t_data["raw_text"],
                    segments=segments,
                    language=t_data.get("language")
                )

            # Reconstruct Summary
            summary = None
            if data.get("summary"):
                s_data = data["summary"]
                summary = Summary(
                    content=s_data["content"],
                    key_points=s_data.get("key_points", []),
                    action_items=s_data.get("action_items", []),
                    topics=s_data.get("topics", [])
                )

            return Session(
                session_id=data["session_id"],
                metadata=metadata,
                transcript=transcript,
                presentation_text=data.get("presentation_text"),
                structured_qa_text=data.get("structured_qa_text"),
                summary=summary
            )

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            raise StorageError(f"Failed to load session from disk: {str(e)}") from e
