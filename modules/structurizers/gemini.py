import json
import logging
import os
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
    q_and_a: str = Field(description="The exact word-for-word text from the Q&A session, formatted to label each [Question], [Answer], and [Follow-up]. Do not edit or paraphrase any words.")

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
            You are a precise transcription formatting tool.
            Your task is to take the raw transcript below and separate it into two parts:
            1. The main presentation section.
            2. The Q&A (Question & Answer) section.

            For the Q&A section, you must label each speaker interaction using one of these labels:
            - "[Question]:" for questions asked by the judges, facilitators, or audience.
            - "[Answer]:" for answers provided by the presenters/team.
            - "[Follow-up]:" for any follow-up questions, comments, or back-and-forth remarks.
            - "[Follow-up Response]:" for answers to follow-up questions.
            Start each label with a new line.

            CRITICAL CONSTRAINTS:
            - DO NOT alter, rewrite, paraphrase, summarize, correct, or edit any words from the original transcript.
            - Every single word in the output sections must match the input transcript exactly.
            - Your only role is to segment the transcript and add labels in the Q&A section. Do not add any of your own commentary, explanations, or introductory text.

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
            qa_text = data.get("q_and_a", "").strip()

            return presentation_text, qa_text

        except Exception as e:
            logger.error(f"Error during structuring: {e}")
            raise StructurizerError(f"Structuring failed: {str(e)}") from e
