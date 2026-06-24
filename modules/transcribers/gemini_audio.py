import logging
import os
from pathlib import Path

from core.interfaces import BaseTranscriber
from core.registry import transcriber_registry
from domain.models import Transcript, TranscriptSegment
from domain.exceptions import TranscriberError

logger = logging.getLogger(__name__)

@transcriber_registry.register("gemini_audio")
class GeminiAudioTranscriber(BaseTranscriber):
    """Adapter for Google Gemini API's native audio-to-text transcription capability."""

    def __init__(
        self,
        api_key: str = "",
        model_name: str = "gemini-2.5-flash"
    ):
        self.api_key = api_key
        self.model_name = model_name
        logger.info(f"GeminiAudioTranscriber initialized with model={model_name}")

    def transcribe(self, audio_path: Path, language: Optional[str] = None, **kwargs) -> Transcript:
        """Upload audio to Gemini File API and transcribe it using the generative model."""
        logger.info(f"Transcribing audio file with Gemini API: {audio_path}")
        
        try:
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
                
            resolved_key = self.api_key or os.getenv("GEMINI_API_KEY")
            if not resolved_key:
                raise ValueError(
                    "Gemini API key is missing. Please set GEMINI_API_KEY env variable "
                    "or pass api_key in settings."
                )

            import google.generativeai as genai
            genai.configure(api_key=resolved_key)
            
            # Upload the file to Gemini File API
            logger.info("Uploading audio file to Gemini File API...")
            audio_file = genai.upload_file(path=str(audio_path))
            logger.info(f"File uploaded. Name: {audio_file.name}, URI: {audio_file.uri}")
            
            try:
                # Ask Gemini to transcribe
                model = genai.GenerativeModel(self.model_name)
                prompt = (
                    "Transcribe the audio file exactly as spoken. Do not summarize, "
                    "do not add commentary, just transcribe the words. "
                    "If the speaker has a Singaporean, Vietnamese, or Indonesian accent, "
                    "please ensure the English transcription is natural and accurate."
                )
                
                logger.info("Requesting transcription from Gemini...")
                response = model.generate_content([prompt, audio_file])
                
                raw_text = response.text.strip()
                
                # Gemini returns the transcript as plain text. 
                # Since Gemini does not return segment timings directly unless requested,
                # we return a single transcript segment covering the text.
                segment = TranscriptSegment(
                    start_time=0.0,
                    end_time=0.0,  # Timings not available in simple text response
                    text=raw_text
                )
                
                return Transcript(
                    raw_text=raw_text,
                    segments=[segment],
                    language=None
                )
            finally:
                # Clean up file in the cloud after transcription
                try:
                    logger.info(f"Cleaning up uploaded file: {audio_file.name}")
                    audio_file.delete()
                except Exception as cleanup_err:
                    logger.warning(f"Failed to delete uploaded file {audio_file.name}: {cleanup_err}")
                    
        except Exception as e:
            logger.error(f"Gemini transcription failed: {e}")
            raise TranscriberError(f"Gemini audio transcription failed: {str(e)}") from e
