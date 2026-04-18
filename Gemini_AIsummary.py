#import os  # Uncomment when using API_KEY as envirovental variable (on Windows)
from google import genai
from google.genai import types

client = genai.Client(api_key="API_KEY_HERE")
# client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

prompt = "Napravi mi cvijet, ali sa ASCII znakovima"


def generate_with_fallback(prompt):
    try:
        # Primarni model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response

    except Exception as e:
        # Provjera je li 503 greška
        if "503" in str(e):
            print("503 greška — prebacujem na gemini-2.5-flash-lite...")

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt
                )
                return response
            except Exception as e2:
                print(f"Fallback također nije uspio: {e2}")
                return None
        else:
            print(f"Druga greška: {e}")
            return None


response = generate_with_fallback(prompt)

if response and response.text:
    print("Uspjeh! AI kaže:")
    print(response.text)
else:
    print("Odgovor nije dobiven.")