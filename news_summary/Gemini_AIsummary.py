import os  # Uncomment when using API_KEY as envirovental variable (on Windows)
from google import genai
from google.genai import types
from datetime import datetime, timezone

class GeminiSumarize:
    def __init__(self):
        # api_key="API_KEY_HERE"
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        self.client = genai.Client(api_key=api_key)

        self.primary_model = "gemini-2.5-flash"
        self.fallback_model = "gemini-2.5-flash-lite"

    def _generate_with_fallback(self, prompt: str):
        try:
            # Primarni model
            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt
            )
            return response, self.primary_model

        except Exception as e:
            # Provjera je li 503 greška
            if "503" in str(e):
                print("503 error on {self.primary_model} — switching to gemini-2.5-flash-lite...")

                try:
                    response = self.client.models.generate_content(
                        model=self.fallback_model,
                        contents=prompt
                    )
                    return response, self.fallback_model
                except Exception as e2:
                    print(f"Fallback model {self.fallback_model} also failed: {e2}")
                    return None, None
            else:
                print(f"Error: {e}")
                return None, None

    def get_summary(self,  article_text: str = None) -> str:
        """
        structured_prompt = (
            You are a news analysis expert. Summarize the following text from the Internet"
            "in the form of a short paragraph (the main event), then highlight 3 key details in bullet points. "
            "The answer must be in English and must only contain the summaries.\n\n"
            f"Article text:\n{article_text}"
        )
        """

        structured_prompt = "Napravi mi samo jedan cvijet, ali sa ASCII znakovima"

        response, koristen_model = self._generate_with_fallback(structured_prompt)

        if response and response.text:
            print(f"\n[INFO] Succesfully generated with model: {koristen_model}")

            return response.text + "\n" + str(datetime.now(timezone.utc).strftime("%d-%m-%Y"))
        else:
            return "Answer not received."
