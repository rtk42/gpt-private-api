import openai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("OPENAI_API_KEY not found.")
else:
    try:
        client = openai.OpenAI(api_key=api_key)
        print("OpenAI client initialized successfully.")
    except Exception as e:
        print(f"Error initializing client: {e}")