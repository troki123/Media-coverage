import os  # Uncomment when using API_KEY as envirovental variable (on Windows)
from google import genai
from google.genai import types

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
            return response

        except Exception as e:
            # Provjera je li 503 greška
            if "503" in str(e):
                print("503 greška na {self.primary_model} — prebacujem na gemini-2.5-flash-lite...")

                try:
                    response = self.client.models.generate_content(
                        model=self.fallback_model,
                        contents=prompt
                    )
                    return response
                except Exception as e2:
                    print(f"Fallback model {self.fallback_model} također nije uspio: {e2}")
                    return None
            else:
                print(f"Druga greška: {e}")
                return None

    def get_summary(self,  article_text: str = None) -> str:
        """
        structured_prompt = (
            "Ti si stručni asistent za analizu vijesti. Sažmi sljedeći tekst s interneta "
            "u obliku kratkog paragrafa (glavni događaj), a zatim izdvoji 3 ključna detalja u natuknicama. "
            "Odgovor mora biti na hrvatskom jeziku.\n\n"
            f"Tekst članka:\n{article_text}"
        )
        """

        structured_prompt = "Napravi mi cvijet, ali sa ASCII znakovima"

        response = self._generate_with_fallback(structured_prompt)

        if response and response.text:
            return(response.text)
        else:
            return "Odgovor nije dobiven."
