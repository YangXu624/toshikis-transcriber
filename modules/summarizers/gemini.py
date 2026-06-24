import json
import logging
import os
from typing import List
from pydantic import BaseModel, Field

from core.interfaces import BaseSummarizer
from core.registry import summarizer_registry
from domain.models import Transcript, Summary
from domain.exceptions import SummarizerError

logger = logging.getLogger(__name__)

class GeminiSummarySchema(BaseModel):
    """Pydantic schema to enforce structured JSON responses from Gemini."""
    content: str = Field(description="A concise narrative summary of the main discussion and context.")
    key_points: List[str] = Field(description="A bulleted list of the main key points discussed in the session.")
    action_items: List[str] = Field(description="A list of concrete actionable items, tasks, and assignments.")
    topics: List[str] = Field(description="List of key topics or categories covered in the session.")

@summarizer_registry.register("gemini")
class GeminiSummarizer(BaseSummarizer):
    """Adapter for Google Gemini summarization API.

    This adapter manages third-party API executions, wraps API exceptions,
    and maps responses back to domain Summary objects.
    """

    def __init__(
        self,
        api_key: str = "",
        model_name: str = "",
        temperature: float = 0.2
    ):
        self.api_key = api_key
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
        self.temperature = temperature
        logger.info(
            f"GeminiSummarizer initialized with model={self.model_name}, "
            f"temperature={temperature}, api_key_length={len(api_key)}"
        )

    def summarize(self, text: str) -> Summary:
        """Summarize structured Q&A answers using Gemini API with structured JSON output."""
        logger.info(f"Summarizing text using Gemini model '{self.model_name}'...")

        try:
            # 1. Input validation
            if not text or not text.strip():
                raise ValueError("Input text is empty; nothing to summarize.")

            # 2. Configure API key
            resolved_key = self.api_key or os.getenv("GEMINI_API_KEY")
            if not resolved_key:
                raise ValueError(
                    "Gemini API key is missing. Please provide it in the configuration "
                    "or set the GEMINI_API_KEY environment variable."
                )

            import google.generativeai as genai
            genai.configure(api_key=resolved_key)

            # 3. Setup model with Pydantic JSON enforcement
            model = genai.GenerativeModel(model_name=self.model_name)
            
            prompt = f"""
            You are an expert executive assistant. Analyze the following structured Q&A text and generate a structured summary.

            CRITICAL CONSTRAINTS:
            - You must summarize ONLY the answers to the questions (usually labeled with '[Answer]:' or provided by the presenting team).
            - Do NOT summarize the main presentation section or the questions themselves. Focus purely on capturing and summarizing the responses and key information provided in the answers.

            Structured Q&A Text:
            \"\"\"
            {text}
            \"\"\"
            """

            # 4. Generate structured content
            logger.info("Sending request to Google Generative AI API...")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiSummarySchema,
                    temperature=self.temperature
                )
            )

            if not response.text:
                raise ValueError("Received empty response text from Gemini API.")

            # 5. Parse and map to domain model
            data = json.loads(response.text)
            return Summary(
                content=data.get("content", ""),
                key_points=data.get("key_points", []),
                action_items=data.get("action_items", []),
                topics=data.get("topics", [])
            )
            
        except Exception as e:
            logger.error(f"Error during summarization: {e}")
            raise SummarizerError(f"Summarization failed: {str(e)}") from e
