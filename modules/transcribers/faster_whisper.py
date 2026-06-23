import logging
from pathlib import Path

from core.interfaces import BaseTranscriber
from core.registry import transcriber_registry
from domain.models import Transcript, TranscriptSegment
from domain.exceptions import TranscriberError

logger = logging.getLogger(__name__)

@transcriber_registry.register("faster_whisper")
class FasterWhisperTranscriber(BaseTranscriber):
    """Adapter for Faster-Whisper transcription library.

    This adapter manages third-party Whisper executions, handles errors,
    and returns clean Domain models.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        logger.info(
            f"FasterWhisperTranscriber initialized with model={model_size}, "
            f"device={device}, compute={compute_type}"
        )

    def transcribe(self, audio_path: Path) -> Transcript:
        """Stub transcription logic that converts audio into a domain Transcript.

        In a future step, this will load the faster_whisper library and perform
        actual inference.
        """
        logger.info(f"Mock transcribing audio file: {audio_path}")
        
        try:
            # Check for file existence to simulate basic transcription validation
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # Return a mock domain transcript for the scaffold
            segments = [
                TranscriptSegment(
                    start_time=0.0,
                    end_time=2.5,
                    text="Hello and welcome to this session.",
                    speaker="Speaker 1"
                ),
                TranscriptSegment(
                    start_time=2.5,
                    end_time=6.0,
                    text="Today we are discussing our software architecture plan.",
                    speaker="Speaker 1"
                )
            ]
            raw_text = " ".join(seg.text for seg in segments)
            return Transcript(raw_text=raw_text, segments=segments, language="en")
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            # Wrap third-party and standard library exceptions into our custom domain exception
            raise TranscriberError(f"Transcription failed: {str(e)}") from e
