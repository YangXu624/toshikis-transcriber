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
        self._model = None
        logger.info(
            f"FasterWhisperTranscriber initialized with model={model_size}, "
            f"device={device}, compute={compute_type}"
        )

    @property
    def model(self):
        """Lazily initialize the WhisperModel to save memory and startup time."""
        if self._model is None:
            logger.info(f"Loading WhisperModel '{self.model_size}' on '{self.device}' with '{self.compute_type}'...")
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
            except Exception as e:
                logger.error(f"Failed to load WhisperModel: {e}")
                raise TranscriberError(f"Failed to load WhisperModel: {str(e)}") from e
        return self._model

    def transcribe(self, audio_path: Path, language: Optional[str] = None, **kwargs) -> Transcript:
        """Transcribe audio file using faster_whisper and return a domain Transcript."""
        logger.info(f"Transcribing audio file: {audio_path} with language={language}, options={kwargs}")
        
        try:
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")

            # Get the loaded model (triggers lazy initialization)
            model = self.model
            
            # Execute transcription (beam_size=5 is standard for transcription accuracy)
            transcribe_opts = {"beam_size": 5}
            if language is not None:
                transcribe_opts["language"] = language
            transcribe_opts.update(kwargs)
            segments_iter, info = model.transcribe(str(audio_path), **transcribe_opts)
            
            segments = []
            raw_text_parts = []
            
            duration = info.duration if info else None
            last_print_time = 0.0
            # Consume generator from faster-whisper
            for segment in segments_iter:
                # Map to our domain model
                seg = TranscriptSegment(
                    start_time=segment.start,
                    end_time=segment.end,
                    text=segment.text.strip(),
                    speaker=None  # basic whisper model does not diarize speakers
                )
                segments.append(seg)
                raw_text_parts.append(seg.text)
                
                try:
                    if duration and isinstance(duration, (int, float)) and isinstance(segment.end, (int, float)):
                        percent = min(100.0, (segment.end / duration) * 100)
                        import time
                        current_time = time.time()
                        # Rate limit printing to once every 0.1 seconds, or when finishing
                        if current_time - last_print_time >= 0.1 or percent >= 99.9:
                            bar_length = 15
                            filled_length = int(round(bar_length * min(1.0, segment.end / duration)))
                            bar = '#' * filled_length + '-' * (bar_length - filled_length)
                            # Compact output formatting to prevent terminal line wrapping
                            print(f"\r\033[KProgress: |{bar}| {percent:.1f}% ({int(segment.end)}s/{int(duration)}s)", end="", flush=True)
                            last_print_time = current_time
                except Exception:
                    pass
                    
            if duration and isinstance(duration, (int, float)):
                print()
                
            raw_text = " ".join(raw_text_parts)
            language = info.language if info else None
            
            return Transcript(raw_text=raw_text, segments=segments, language=language)
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise TranscriberError(f"Transcription failed: {str(e)}") from e
