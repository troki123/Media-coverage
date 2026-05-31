import os
import sqlite3
import logging
import json
from google import genai
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class GeminiSumarize:
    def __init__(self):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is missing!")
            
        self.client = genai.Client(api_key=api_key)
        self.primary_model = "gemini-2.5-flash"
        self.fallback_model = "gemini-2.5-flash-lite"

    def _generate_with_fallback(self, prompt: str):
        """Sends a request to the Gemini API with automatic fallback if the primary model is unavailable."""
        try:
            logger.info(f"Sending prompt to primary model: {self.primary_model}")
            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt
            )
            return response, self.primary_model
        except Exception as e:
            if "503" in str(e) or "429" in str(e):
                logger.warning(f"Rate limit or 503 Error on {self.primary_model} — switching to fallback model...")
                try:
                    response = self.client.models.generate_content(
                        model=self.fallback_model,
                        contents=prompt
                    )
                    return response, self.fallback_model
                except Exception as e2:
                    logger.error(f"Fallback model failed: {e2}", exc_info=True)
                    return None, None
            else:
                logger.error(f"Unexpected Gemini API error: {e}", exc_info=True)
                return None, None

    def get_summary(self, article_text: str = None) -> str:
        """Generates a structured AI summary for a single article based on specific criteria."""
        if not article_text:
            return "No text available to summarize."

        structured_prompt = (
            "You are an expert research librarian and news analysis expert. "
            "Analyze the following article text from the Internet.\n\n"
            "STRICT FILTERING & SUMMARIZATION RULES:\n"
            "1. Read the text carefully.\n"
            "2. If the article is clickbait, political controversy, or irrelevant, return 'IRRELEVANT_ARTICLE'.\n"
            "3. For VALID high-quality articles, write a summary in English as a short paragraph (the main event) "
            "followed by 3 key details in bullet points.\n"
            "4. Output format MUST be plain text (the short paragraph followed by the bullets).\n\n"
            f"Article text:\n{article_text}"
        )
        
        response, used_model = self._generate_with_fallback(structured_prompt)

        if response and response.text:
            logger.info(f"Successfully generated summary using model: {used_model}")
            return response.text.strip()
        else:
            logger.error("Failed to get response text from Gemini.")
            return "Gemini AI is too busy. Summary unavailable."