from google import genai
from google.genai import types
from fastapi import FastAPI
import numpy as np
import os
from typing import List, Tuple
from fastapi.concurrency import run_in_threadpool
client= genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))  # Set env var
app = FastAPI()


# Predefined preference labels and matching phrases
PREFERENCE_LABELS = {
    "exclude": [
        "dairy", "gluten", "sugar", "nuts", "egg", "soy", "red meat", "seafood",
        "shellfish", "pork", "corn", "alcohol", "spicy", "caffeine", "mushrooms", "onions", "garlic"
    ],
    "diet": [
        "vegan", "vegetarian", "pescatarian", "paleo", "keto", "low carb", "low fat", 
        "high protein", "whole30", "flexitarian", "diabetic", "dash diet", "raw", 
        "intermittent fasting", "mediterranean"
    ],
    "goal": [
        "weight loss", "lose weight", "cutting", "slim down", "fat loss", 
        "muscle gain", "bulk up", "maintenance", "improve energy", 
        "balance hormones", "reduce inflammation", "detox"
    ],
    "cuisine": [
        "indian", "north indian", "south indian", "italian", "mexican", 
        "chinese", "thai", "japanese", "korean", "french", "greek", 
        "mediterranean", "american", "middle eastern", "spanish", "lebanese"
    ],
    "includeIngredients": [
        "chicken", "mutton", "beef", "paneer", "tofu", "lentils", "beans", 
        "quinoa", "rice", "broccoli", "spinach", "cauliflower", "sweet potato", 
        "avocado", "eggs", "milk", "cheese", "nuts", "seeds", "banana", 
        "apple", "berries", "mango", "yogurt", "oats", "chia seeds"
    ],
    "mealType": [
        "breakfast", "lunch", "dinner", "snack", "brunch", "dessert", 
        "post workout", "pre workout", "light meal", "heavy meal"
    ],
    "cookingStyle": [
        "grilled", "baked", "steamed", "fried", "raw", "sautéed", 
        "pressure cooked", "slow cooked", "stir fried", "roasted", "air fried"
    ],
    "allergy": [
        "gluten", "dairy", "egg", "soy", "nuts", "seafood", "shellfish", 
        "sesame", "mustard", "sulfites", "lupin"
    ],
    "spiceLevel": [
        "mild", "medium", "spicy", "extra spicy"
    ],
    "budget": [
        "low budget", "affordable", "cheap meals", "moderate budget", 
        "premium meals", "no budget limit"
    ],
    "time": [
        "quick meals", "15 minutes", "30 minutes", "1 hour", 
        "slow cooked", "instant", "overnight"
    ],
    "appliance": [
        "oven", "air fryer", "instant pot", "pressure cooker", "stove top", 
        "microwave", "blender", "no cook"
    ]
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
    print("Fetching your preferences...")
    user_embedding = get_embedding(user_input)
    preferences = {}

    for pref_type, values in PREFERENCE_LABELS.items():
        for value in values:
            sim = cosine_similarity(user_embedding, get_embedding(value))
            if sim > 0.652:  # tweak threshold if needed
                if pref_type not in preferences:
                    preferences[pref_type] = []
                preferences[pref_type].append(value)
    return preferences
