import os
import google.generativeai as genai
from supabase import create_client, Client
from datetime import datetime
from preference_matcher import match_preferences
import requests
import json
from preference_matcher import get_embedding,cosine_similarity
from typing import Tuple

# Initialize API Keys
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro-002")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_URL = "https://api.spoonacular.com"
SPOONACULAR_API_KEY=os.getenv("SPOONACULAR_API_KEY")

def quick_meal_finder(preferences):
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 3,
    }
    if "includeIngredients" in preferences:
        params["includeIngredients"] = ",".join(preferences["includeIngredients"])
    if "diet" in preferences:
        params["diet"] = preferences["diet"][0]  # Assuming one diet preference
    if "maxReadyTime" in preferences:
        params["maxReadyTime"] = preferences["maxReadyTime"]

    response = requests.get(f"{BASE_URL}/recipes/complexSearch", params=params)
    if response.status_code == 200:
        recipes = response.json().get("results", [])
        return format_quick_meals(recipes)
    else:
        return f"❌ Failed to find quick meals: {response.text}"

def format_quick_meals(recipes):
    if not recipes:
        return "😔 No meals found for your criteria."
    output = "⏱️ **Quick Meal Suggestions**:\n"
    for r in recipes:
        output += f"- 🍲 {r['title']} (ID: {r['id']})\n"
    output += "\n💡 Use the recipe ID to fetch full instructions if needed."
    return output


def food_health_explainer(food_description, health_context):
    prompt = f"""
Explain how the following food affects the body, especially considering {health_context if health_context else 'general health'}:
Food: {food_description}

Include:
- Nutritional breakdown
- Ayurvedic interpretation (Vata/Pitta/Kapha, heating vs cooling)
- How it helps or harms the health context
- Suggestions to improve or tweak it
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Failed to explain food health context: {e}"

# Call Spoonacular Meal Planner API
def get_meal_plan(preferences):
    params = {
        "timeFrame": "week",
        "apiKey": SPOONACULAR_API_KEY
    }

    if "targetCalories" in preferences:
        params["targetCalories"] = preferences["targetCalories"]
    if "exclude" in preferences:
        params["exclude"] = ",".join(preferences["exclude"])
    if "diet" in preferences:
        params["diet"] = preferences["diet"][0]  # Spoonacular only takes one
    if "cuisine" in preferences:
        params["cuisine"] = preferences["cuisine"][0]
    if "includeIngredients" in preferences:
        params["includeIngredients"] = ",".join(preferences["includeIngredients"])

    print("📦 Requesting meal plan with:", params)  # For debugging

    response = requests.get(f"{BASE_URL}/mealplanner/generate", params=params)
    if response.status_code == 200:
        data = response.json()
        return format_meal_plan(data)
    else:
        return f"❌ Failed to get meal plan: {response.text}"


# Format the meal plan output
def format_meal_plan(data):
    response = "📅 **Weekly Meal Plan**:\n"
    for day in data["week"]:
        day_data = data["week"][day]
        response += f"\n📆 {day.capitalize()}:\n"
        for meal in day_data["meals"]:
            response += f"- 🍽️ {meal['title']} (ready in {meal['readyInMinutes']} mins)\n"
    return response

def get_substitute_suggestions(ingredient: str, reason: str = "general") -> str:
    prompt = f"""
You are a smart ingredient substitution expert for recipes. Suggest replacements for the ingredient: **{ingredient}**

Reason: {reason}

Include:
- 2 to 3 substitution options
- How each one affects **taste**, **nutrition**, and **cooking process**
- Whether it's suitable for hormone balance / PCOD (if applicable)
- Ayurvedic compatibility (heating/cooling, Vata/Pitta/Kapha)

Make it concise, easy to understand, and helpful for someone cooking at home.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Failed to fetch substitutes: {e}"


import re

def extract_ingredient_and_reason(user_input: str) -> Tuple[str, str]:
    # Use embeddings to extract ingredient and reason (if possible)
    user_embedding = get_embedding(user_input)  # Get user input embedding

    # Predefined ingredient-related words
    ingredient_keywords = ["milk", "flour", "sugar", "butter", "chicken", "egg", "peanut", "soy", "avocado"]
    reason_keywords = ["allergy", "diet", "budget", "availability", "health", "PCOD", "hormonal imbalance"]

    # Find closest match for ingredient using cosine similarity
    closest_ingredient = None
    closest_reason = None
    max_similarity = 0
    max_reason_similarity = 0

    # Check ingredients
    for ingredient in ingredient_keywords:
        ingredient_embedding = get_embedding(ingredient)
        similarity = cosine_similarity(user_embedding, ingredient_embedding)
        if similarity > max_similarity:
            closest_ingredient = ingredient
            max_similarity = similarity

    # Check reason
    for reason in reason_keywords:
        reason_embedding = get_embedding(reason)
        similarity = cosine_similarity(user_embedding, reason_embedding)
        if similarity > max_reason_similarity:
            closest_reason = reason
            max_reason_similarity = similarity

    # Fallback to simple regex-based extraction (if embeddings are not clear)
    if not closest_ingredient:
        ingredient_match = re.search(r"(milk|flour|sugar|butter|chicken|egg|peanut|soy|avocado)", user_input, re.IGNORECASE)
        if ingredient_match:
            closest_ingredient = ingredient_match.group(0).lower()

    if not closest_reason:
        reason_match = re.search(r"(allergy|diet|budget|availability|health|pcod|hormonal imbalance)", user_input, re.IGNORECASE)
        if reason_match:
            closest_reason = reason_match.group(0).lower()

    return closest_ingredient, closest_reason
