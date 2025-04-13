from google import genai
from google.genai import types
import numpy as np
import os
from typing import List, Tuple

client= genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))  # Set env var

# Predefined preference labels and matching phrases
PREFERENCE_LABELS = {
    "exclude": ["dairy", "gluten", "sugar", "nuts", "egg", "soy"],
    "diet": ["low carb", "high protein", "vegan", "keto", "vegetarian"],
    "goal": ["weight loss", "muscle gain", "maintenance"],
    "cuisine": ["indian", "italian", "mexican", "chinese", "mediterranean"],
    "includeIngredients": ["milk", "paneer", "cheese", "lentils", "spinach"]
}


def get_embedding(text: str) -> List[float]:
    response = client.models.embed_content(
        model="models/embedding-001",
        contents=[text],
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")  # <-- this line is key!
    )
    return response.embeddings[0].values

def cosine_similarity(vec1, vec2) -> float:
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def match_preferences(user_input: str) -> dict:
    user_embedding = get_embedding(user_input)
    preferences = {}

    for pref_type, values in PREFERENCE_LABELS.items():
        for value in values:
            sim = cosine_similarity(user_embedding, get_embedding(value))
            if sim > 0.80:  # tweak threshold if needed
                if pref_type not in preferences:
                    preferences[pref_type] = []
                preferences[pref_type].append(value)
    return preferences
