from google.generativeai import genai
from google.genai import types
import os

# Ensure you have the correct environment variable set for your API key
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    result = client.models.embed_content(
        model="gemini-embedding-exp-03-07",
        contents=["What is the meaning of life?"],  # List format
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
    )
    print(result.embeddings)
except Exception as e:
    print(f"Error: {e}")
    
