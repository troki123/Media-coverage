import os  # Uncomment when using API_KEY as environmental variable (on Windows)
from google import genai
from google.genai import types
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class GeminiSumarize:
    def __init__(self):
        # api_key="API_KEY_HERE"
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        self.client = genai.Client(api_key=api_key)

        self.primary_model = "gemini-2.5-flash"
        self.fallback_model = "gemini-2.5-flash-lite"

    def _generate_with_fallback(self, prompt: str):
        try:
            # Primary model
            logger.info(f"Sending prompt to primary model: {self.primary_model}")

            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt
            )
            return response, self.primary_model

        except Exception as e:
            # Check if it is a 503 service unavailable error
            if "503" in str(e):
                logger.warning(f"503 Error on {self.primary_model} — switching to fallback model...")

                try:
                    response = self.client.models.generate_content(
                        model=self.fallback_model,
                        contents=prompt
                    )
                    return response, self.fallback_model
                except Exception as e2:
                    logger.error(f"Fallback model {self.fallback_model} also failed: {e2}", exc_info=True)
                    return None, None
            else:
                logger.error(f"Unexpected Gemini API error: {e}", exc_info=True)
                return None, None

    def get_summary(self, article_text: str = None) -> str:
        """
        structured_prompt = "Tell me about BMW"
        """

        structured_prompt = (
            "You are a news analysis expert. Summarize the following text from the Internet "
            "in the form of a short paragraph (the main event), then highlight 3 key details in bullet points. "
            "The answer must be in English and must only contain the summaries.\n\n"
            f"Article text:\n{article_text}"
        )
        
        response, used_model = self._generate_with_fallback(structured_prompt)

        if response and response.text:
            logger.info(f"Successfully generated summary using model: {used_model}")

            return response.text + "\n" + str(datetime.now(timezone.utc).strftime("%d-%m-%Y"))
        else:
            logger.error("Failed to get response text from Gemini.")
            return "Gemini AI is too busy. Try again later."