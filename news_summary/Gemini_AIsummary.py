import os  # Uncomment when using API_KEY as envirovental variable (on Windows)
from google import genai
import sqlite3
from google.genai import types
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class GeminiSumarize:
    """
    Handles text summarization using Gemini AI with an integrated
    SQLite caching layer and an automatic model fallback mechanism.
    """

    def __init__(self):
        # api_key="API_KEY_HERE"
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        self.client = genai.Client(api_key=api_key)

        self.primary_model = "gemini-2.5-flash"
        self.fallback_model = "gemini-2.5-flash-lite"

        self.db_path = "database/app.py"

    def _generate_with_fallback(self, prompt: str):
        """
        Attempts content generation using the primary model.
        Switches to a lighter fallback model if a 503 Service Unavalible error occurs.
        """
        try:
            logger.info(f"Sending prompt to primary model: {self.primary_model}")

            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt
            )
            return response, self.primary_model

        except Exception as e:
            """
            Handle transient server-side unavailibility
            If primary model is too busy, switch to degraded model with higher response chance
            """
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
            
            # Gemini returned some error we can not account for
            logger.error(f"Unexpected Gemini API error: {e}", exc_info=True)
            return None, None

    def get_summary(self,  search_query: str = None) -> str:
        """
        Retrieves a summary for a given search querry
        Checks the local cache first; if missing, calls Gemini API and stores the result.
        """

        current_date = datetime.now(timezone.utc).strftime("%d-%m-%Y")

        # ====== STEP 1: CACHE CHECK ======
        try:
            # Connection to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Searching for latest querry
            cursor.execute(
                "SELECT summary_text FROM media_news WHERE querry =? ORDER BY created_at DESC LIMIT 1",
                (search_query,)
            )
            existing_summary = cursor.fetchone()
            conn.close()

            if existing_summary:
                logger.info(f"CACHE HIT: Found existing summary for querry '{search_querry}' in Database. Skipping Gemini API.")
                text_time = str(datetime.now(timezone.utc).strftime("%d-%m-%Y"))

                return existing_summary[0] + "\n" + text_time + " (From database)"

        except Exception as db_select_error:
            # DB failure should not block the API pipeline; log it and proceed
            logger.error(f"Database select failed: {db_select_error}", exc_info=True)
        
        # ====== STEP 2: LIVE GENERATION ======
        """
        structured_prompt = (
            You are a news analysis expert. Summarize the following text from the Internet"
            "in the form of a short paragraph (the main event), then highlight 3 key details in bullet points. "
            "The answer must be in English and must only contain the summaries.\n\n"
            f"Article text:\n{article_text}"
        )
        """

        structured_prompt = "Napravi mi samo jedan cvijet, ali sa ASCII znakovima"

        response, model_used = self._generate_with_fallback(structured_prompt)

        if not response or not response.text:
            logger.error("failed to retrieve a valid response text from Gemini API.")
            return "Gemini AI is too busy. Try again later."

        logger.info(f"Successfully generated summary using model: {model_used}")

        # === STEP 3: CACHE POPULATION ===
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO search_summaries (search_query, summary_text, model_used) VALUES (?, ?, ?)",
                (search_querry, response.text, model_used)
            )
            conn.commit()
            conn.close()
            logger.info(f"Cached new summary for query '{search_query}' to database.")
        except Exception as db_error:
            logger.error(f"Failed to cache new summary to database: {db_error}", exc_inf=True)

        return f"{response.text}\n{current_date}"
