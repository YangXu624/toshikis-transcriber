import json
import logging
import os
import re
from typing import Tuple
from pydantic import BaseModel, Field

from core.interfaces import BaseStructurizer
from core.registry import structurizer_registry
from domain.models import Transcript
from domain.exceptions import StructurizerError

logger = logging.getLogger(__name__)

class GeminiStructureSchema(BaseModel):
    """Pydantic schema to enforce structured JSON responses from Gemini."""
    presentation: str = Field(description="The exact word-for-word text from the transcript that corresponds to the main presentation. Do not rewrite, edit, or summarize any words.")
    q_and_a: str = Field(description="The exact word-for-word text from the Q&A session, formatted to label each speaker interaction as [Question]:, [Answer]:, or [Follow-up]:. Do not edit, summarize or rewrite any words. The presentation text must NOT be included here.")

@structurizer_registry.register("gemini")
class GeminiStructurizer(BaseStructurizer):
    """Adapter for Google Gemini structure layer.

    It separates Q&A from the main presentation and formats/labels Q&A,
    strictly keeping the original wordings.
    """

    def __init__(
        self,
        api_key: str = "",
        model_name: str = "",
        temperature: float = 0.0
    ):
        self.api_key = api_key
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
        self.temperature = temperature
        logger.info(
            f"GeminiStructurizer initialized with model={self.model_name}, "
            f"temperature={temperature}, api_key_length={len(api_key)}"
        )

    def _clean_qa_format(self, raw_qa: str) -> str:
        """Merge consecutive duplicate tags and map [Follow-up] to [Question]."""
        # Find all matches of [Tag]: content
        pattern = re.compile(
            r'\[(Question|Answer|Follow-up)\]:\s*(.*?)(?=\s*\[(?:Question|Answer|Follow-up)\]:|$)', 
            re.DOTALL
        )
        matches = pattern.findall(raw_qa)
        
        merged_blocks = []
        current_type = None
        current_text = []
        
        for tag, content in matches:
            # Map Follow-up to Question
            normalized_tag = 'Question' if tag in ('Question', 'Follow-up') else 'Answer'
            content_clean = content.strip()
            if not content_clean:
                continue
                
            if normalized_tag == current_type:
                current_text.append(content_clean)
            else:
                if current_type is not None:
                    merged_blocks.append(f"[{current_type}]: " + " ".join(current_text))
                current_type = normalized_tag
                current_text = [content_clean]
                
        if current_type is not None and current_text:
            merged_blocks.append(f"[{current_type}]: " + " ".join(current_text))
            
        return "\n".join(merged_blocks)

    def structurize(self, transcript: Transcript) -> Tuple[str, str]:
        """Separate Q&A and presentation, returning (presentation_text, structured_qa_text)."""
        logger.info("Structuring transcript using Gemini...")

        try:
            if not transcript.raw_text or not transcript.raw_text.strip():
                raise ValueError("Transcript text is empty; nothing to structure.")

            resolved_key = self.api_key or os.getenv("GEMINI_API_KEY")
            if not resolved_key:
                raise ValueError(
                    "Gemini API key is missing. Please set the GEMINI_API_KEY environment variable."
                )

            import google.generativeai as genai
            genai.configure(api_key=resolved_key)

            model = genai.GenerativeModel(model_name=self.model_name)

            prompt = f"""
            You are a precise transcription segmenter and formatter. 
            Your task is to take the raw transcript below and split it into two distinct parts:
            1. "presentation": The main presentation section at the beginning. This starts at the very beginning of the transcript and runs continuously until the presentation concludes and a judge/facilitator opens the Q&A session.
            2. "q_and_a": The Q&A (Question & Answer) session. This starts strictly when the judges, facilitators, or audience members thank the presenters and start asking questions, and continues to the end.

            CRITICAL CONSTRAINTS:
            - The "q_and_a" section must NOT contain any text from the main presentation. It must start strictly where the Q&A starts (e.g., when a judge/moderator says "Okay, thank you team for your presentation..." or starts asking questions).
            - In the "q_and_a" section, you must label each speaker interaction using one of these labels:
              - "[Question]:" for questions asked by the judges, facilitators, or audience.
              - "[Answer]:" for answers provided by the presenters/team.
              - "[Follow-up]:" for any follow-up questions, comments, or back-and-forth remarks.
            - Each label (e.g. "[Question]:", "[Answer]:", "[Follow-up]:") must start on a new line (i.e. preceded by a newline character).
            - DO NOT alter, rewrite, paraphrase, summarize, correct, or edit any words from the original transcript.
            - Every single word in the output sections must match the input transcript exactly.
            - Do not add any of your own commentary, explanations, or introductory text.

            Transcript:
            \"\"\"
            {transcript.raw_text}
            \"\"\"
            """

            logger.info("Sending request to Google Generative AI API for structuring...")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiStructureSchema,
                    temperature=self.temperature
                )
            )

            if not response.text:
                raise ValueError("Received empty response text from Gemini API during structuring.")

            data = json.loads(response.text)
            presentation_text = data.get("presentation", "").strip()
            raw_qa = data.get("q_and_a", "").strip()
            qa_text = self._clean_qa_format(raw_qa)

            return presentation_text, qa_text

        except Exception as e:
            logger.error(f"Error during structuring: {e}")
            raise StructurizerError(f"Structuring failed: {str(e)}") from e
