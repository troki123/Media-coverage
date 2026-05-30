import os  # Uncomment when using API_KEY as envirovental variable (on Windows)
from google import genai
import sqlite3
from google.genai import types
from datetime import datetime, timezone
import logging
import json
from pydantic import BaseModel, Field
from typing import List

logger = logging.getLogger(__name__)

# === RESPONSE STRUCTURE SCHEMAS (Pydantic) ===
class ArticleSummaryItem(BaseModel):
    row_id: int = Field(description="The exact row_id provided in the input payload.")
    summary: str = Field(description="Short paragraph of the main event and 3 bullet points of details.")

class BatchSummaryResponse(BaseModel):
    summaries: List[ArticleSummaryItem]

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

        self.db_path = "database/app.db"

    def _generate_with_fallback(self, prompt: str):
        """
        Attempts content generation using the primary model with a strict Pydantic schema.
        Switches to a lighter fallback model if a 503 Service Unavailable error occurs.
        """
        # Configuration forcing the model to return a structured JSON matching the Pydantic schema
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BatchSummaryResponse,
            temperature=0.2  # Lower temperature reduces creativity and ensures structural integrity
        )

        try:
            logger.info(f"Sending prompt to primary model: {self.primary_model}")

            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt,
                config=config
            )
            return response, self.primary_model

        except Exception as error:
            """
            Handle transient server-side unavailibility
            If primary model is too busy, switch to degraded model with higher response chance
            """
            if "503" in str(error):
                logger.warning(f"503 Error on {self.primary_model} — switching to fallback model...")

                try:
                    response = self.client.models.generate_content(
                        model=self.fallback_model,
                        contents=prompt,
                        config=config
                    )
                    return response, self.fallback_model
                
                except Exception as fallback_error:
                    logger.error(f"Fallback model {self.fallback_model} also failed: {fallback_error}", exc_info=True)
                    return None, None
            
            # Gemini returned some error we can not account for
            logger.error(f"Unexpected Gemini API error: {error}", exc_info=True)
            return None, None

    def get_summary(self,  search_id: int = None) -> str:
        """
        Fetches all unsummarized articles for a search_id, processes them 
        in micro-batches of up to 10 articles per Gemini API request, 
        and updates the database iteratively.
        """

        if search_id is None:
            return "No search_id provided."

        # ====== STEP 1: FETCH TARGET ARTICLES ======
        try:
            # Connection to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Searching for latest querry
            cursor.execute(
                "SELECT id, content FROM media_news WHERE search_id = ? AND (summary IS NULL OR summary = '')",
                (search_id,)
            )
            articles = cursor.fetchall()
            conn.close()

            if not articles:
                return f"All articles for search_id {search_id} are already summarized or none were found."
        
        except Exception as db_error:
            logger.error(f"Database extraction failed for search_id {search_id}: {db_error}", exc_info=True)
            return "Database retrieval failure."

        articles_payload = []
        for row_id, content in articles:
            # Safe boundary check to prevent pulling empty string segments into the LLM context
            article_text = content if content else "No content available for this record."
            articles_payload.append({
                "row_id": row_id,
                "text": article_text[:6000] # Chunk string length to prevent context explosion
            })
        
        # ====== STEP 2: CHUNKING & LIVE BATCH GENERATION (10 at a time) ======
        chunk_size = 10
        total_updated_count = 0
        current_date = datetime.now(timezone.utc).strftime("%d-%m-%Y")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        except Exception as db_init_error:
            logger.error(f"Failed to open database connection for updates: {db_init_error}")
            return "Database connection failure during processing."

        for i in range (0, len(articles_payload), chunk_size):
            current_chunk = articles_payload[i : i + chunk_size]
            logger.info(f"Processing chunk: articles {i + 1} to {min(i + chunk_size, len(articles_payload))} out of {len(articles_payload)}")
        
            structured_prompt = (
                "You are a news analysis expert. Your task is to summarize multiple articles at once.\n"
                "For each article, write a short paragraph of the main event and exactly 3 bullet points of details.\n"
                f"Articles to process in this batch:\n{json.dumps(current_chunk)}"
            )
    
            #structured_prompt = "Napravi mi samo jedan cvijet, ali sa ASCII znakovima"

            response, model_used = self._generate_with_fallback(structured_prompt)

            if not response or not response.text:
                logger.error(f"Skipping current chunk batch starting at index {i} due to API failure.")
                continue

            # === STEP 3: CACHE POPULATION ===
            try:
                # Structured Outputs ensure response.text contains valid JSON
                data = json.loads(response.text)
                
                # Extract the array corresponding to the 'summaries' property defined in BatchSummaryResponse
                summaries_data = data.get("summaries", [])

                for item in summaries_data:
                    row_id = item.get("row_id")
                    summary_text = item.get("summary")

                    if row_id and summary_text:
                        full_summary = f"{summary_text}\nGenerated on: {current_date} via {model_used}"

                        cursor.execute(
                            "UPDATE media_news SET summary = ? WHERE id = ?",
                            (full_summary, row_id)
                        )
                        total_updated_count += 1

                logger.info(f"Successfully processed chunk starting at index {i} in-memory.")
            
            except Exception as parse_error:
                logger.error(f"Failed to parse batch JSON response for chunk index {i}: {parse_error}. Raw response: {response.text}")
                # Continue loop to process remaining chunks even if one fails formatting bounds
                continue

        # Commit transaction and safely close database resources once all chunks are done
        try:
            conn.commit()
            conn.close()
            logger.info("Successfully committed all batches and closed database connection.")
        except Exception as db_commit_error:
            logger.error(f"Failed to commit final database changes: {db_commit_error}") 

        return f"Processing complete. Successfully summarized {total_updated_count} out of {len(articles_payload)} articles across dynamic chunks!"