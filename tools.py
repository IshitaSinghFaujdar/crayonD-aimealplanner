import os
import google.generativeai as genai
from supabase import create_client, Client
from datetime import datetime
from preference_matcher import match_preferences
import requests
import json
from preference_matcher import get_embedding,cosine_similarity
from typing import Tuple
from config import SUPABASE_KEY,SUPABASE_URL,GOOGLE_API_KEY,SPOONACULAR_API_KEY
# Initialize API Keys
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro-002")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_URL = "https://api.spoonacular.com"

def detect_tool_llm(prompt: str, context: str) -> str:
    system_prompt = """
You are an intelligent tool router for a chatbot. Based on user input and recent context, respond with one of the following tools ONLY:
- meal_planner
- substitute_finder
- quick_meal_finder
- food_health_explainer
- chat

Return ONLY the tool name. Do NOT include explanations.
"""
    full_prompt = f"{system_prompt}\nContext:\n{context}\n\nUser Input:\n{prompt}"
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip().lower()
    except Exception as e:
        print("Tool detection error:", e)
        return "chat"


def quick_meal_finder(user_context):
    print("Fetching quick meal suggestions...")

    # Build query for Spoonacular API with user preferences
    url = f"{BASE_URL}/recipes/complexSearch"
    params = {
        "includeIngredients": ",".join(user_context["includeIngredients"]),
        "diet": ",".join(user_context["diet"]),
        "maxReadyTime": user_context["maxReadyTime"],
        "excludeIngredients": ",".join(user_context["exclude"]),
        "targetCalories": user_context["targetCalories"],
        "number": 3,
        "apiKey": SPOONACULAR_API_KEY
    }
    print("\nFetching recipes.")
    response = requests.get(url, params=params)
    if response.status_code == 200:
        meal_data = response.json().get('results', [])
        recipes = []
        print("\nRecieved recipes.")

        # Get full details of each recipe
        for recipe in meal_data:
            recipe_id = recipe["id"]
            recipe_url = f"{BASE_URL}/recipes/{recipe_id}/information"
            recipe_details = requests.get(recipe_url, params={"apiKey": SPOONACULAR_API_KEY}).json()
            print("\nfetching full recipe.")
            # Format the recipe details
            formatted_recipe = {
                "title": recipe_details["title"],
                "image": recipe_details["image"],
                "ingredients": [ingredient["name"] for ingredient in recipe_details["extendedIngredients"]],
                "instructions": recipe_details["instructions"]
            }
            print("formatting..")
            recipes.append(formatted_recipe)

        return recipes
    else:
        return {"error": "Failed to fetch meal suggestions."}



def format_quick_meals(recipes):
    if not recipes:
        return "😔 No meals found for your criteria."
    output = "⏱️ **Quick Meal Suggestions**:\n"
    for r in recipes:
        output += f"- 🍲 {r['title']} (ID: {r['id']}) - [View Recipe](https://spoonacular.com/recipes/{r['id']})\n"
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
def get_meal_plan(user_context):
    print("Fetching weekly meal plan...")

    url = f"{BASE_URL}/mealplanner/generate"
    params = {
        "timeFrame": "week",
        "diet": ",".join(user_context.get("diet", [])),  # e.g., vegan
        "exclude": ",".join(user_context.get("exclude", [])),  # e.g., cheese
        "targetCalories": user_context.get("targetCalories", 2000),
        "apiKey": SPOONACULAR_API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("week", {})  # return weekly plan
    else:
        print("Error:", response.text)
        return {"error": "Failed to fetch meal plan."}

# Format the meal plan output
def format_meal_plan(week_data):
    if not week_data:
        return "😞 No meal plan found for your preferences."

    output = "📅 **Your Weekly Meal Plan**:\n"
    for day, info in week_data.items():
        output += f"\n**{day.capitalize()}**:\n"
        for meal in info["meals"]:
            output += f"- 🍽️ {meal['title']} ({meal['readyInMinutes']} mins) → [View Recipe]({meal['sourceUrl']})\n"
    return output



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
