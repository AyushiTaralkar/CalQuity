import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

for model_name in models_to_test:
    print("\n" + "=" * 60)
    print(f"TESTING: {model_name}")
    print("=" * 60)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Reply with exactly: ParcelPilot fallback test successful",
        )

        print("SUCCESS")
        print("MODEL:", model_name)
        print("RESPONSE:", response.text)

    except Exception as e:
        print("FAILED")
        print("MODEL:", model_name)
        print("ERROR:", str(e))