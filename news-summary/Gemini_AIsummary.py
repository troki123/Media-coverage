# import os  # Uncomment when using API_KEY as envirovental variable (on Windows)
from google import genai
from google.genai import types

# Inicijalizacija klijenta
client = genai.Client(api_key="API_KEY_HERE")
# client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",   # If error 503, replace with "gemini-2.5-flash-lite"
                                    # because a response object is guaranteed most times 
        contents="Napravi mi cvijet, ali sa ASCII znakovima"
    )
    
    if response.text:
        print("Uspjeh! AI kaže:")
        print(response.text)
    else:
        print("Odgovor je prazan (moguće zbog sigurnosnih filtera).")

except Exception as e:
    print(f"Greška: {e}")