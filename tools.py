import os
import google.generativeai as genai
from supabase import create_client, Client
from datetime import datetime
from preference_matcher import match_preferences
import requests
import json
import random
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
- weekly_meal_planner
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

    url = f"{BASE_URL}/recipes/complexSearch"
    params = {
        "includeIngredients": ",".join(user_context.get("includeIngredients", [])),
        "diet": ",".join(user_context.get("diet", [])),
        "maxReadyTime": user_context.get("maxReadyTime", 30),
        "excludeIngredients": ",".join(user_context.get("exclude", [])),
        "targetCalories": user_context.get("targetCalories", ""),
        "number": 3,
        "cuisine": ",".join(user_context.get("cuisine", [])),
        "apiKey": SPOONACULAR_API_KEY
    }


    response = requests.get(url, params=params)
    if response.status_code == 200:
        meal_data = response.json().get('results', [])
        if not meal_data:
            return f"❌ No recipes found for your preferred cuisine ({', '.join(user_context['cuisine'])}). Please try adjusting your preferences."
        
        recipes = []
        for recipe in meal_data:
            recipe_id = recipe["id"]
            recipe_url = f"{BASE_URL}/recipes/{recipe_id}/information"
            recipe_details = requests.get(recipe_url, params={"apiKey": SPOONACULAR_API_KEY}).json()
            formatted_recipe = {
                "id": recipe_details["id"],
                "title": recipe_details["title"],
                "image": recipe_details["image"],
                "ingredients": [ingredient["name"] for ingredient in recipe_details["extendedIngredients"]],
                "instructions": recipe_details["instructions"]
            }
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


def fetch_nutritional_data(food_description: str) -> str:
    """
    Fetch nutritional data for a given food item from the Spoonacular API.

    :param food_description: The name of the food to fetch nutrition data for.
    :return: A string containing the nutritional breakdown.
    """
    # URL for the food nutrition endpoint
    url = f"{BASE_URL}/food/ingredients/{food_description}/nutritionWidget.json"

    # Parameters to pass to the API
    params = {
        "apiKey": SPOONACULAR_API_KEY
    }

    # Make the request to the Spoonacular API
    response = requests.get(url, params=params)

    if response.status_code == 200:
        nutrition_data = response.json()

        # Extracting relevant nutritional data
        nutritional_breakdown = f"""
        **Nutritional Information for {food_description}:**
        - Calories: {nutrition_data['calories']} kcal
        - Protein: {nutrition_data['protein']} g
        - Carbs: {nutrition_data['carbs']} g
        - Fat: {nutrition_data['fat']} g
        - Fiber: {nutrition_data['fiber']} g
        - Sugars: {nutrition_data['sugars']} g
        - Sodium: {nutrition_data['sodium']} mg
        """
        return nutritional_breakdown
    else:
        return f"❌ Failed to fetch nutritional data for {food_description}. Please try again later."
    
def food_health_explainer(food_description, health_context):
    # Step 1: Use API for nutritional data
    nutrition_data = fetch_nutritional_data(food_description)  # API call
    
    # Step 2: Use Gemini for Ayurvedic/Health context
    gemini_prompt = f"""
    Explain how {food_description} affects {health_context}. 
    Nutritional info: {nutrition_data}
    Provide Ayurvedic interpretation and health benefits.
    """
    gemini_response = model.generate_content(gemini_prompt)
    
    # Combine both results
    final_explanation = f"Nutrition: {nutrition_data}\n\n{gemini_response.text.strip()}"
    return final_explanation

# Call Spoonacular Meal Planner API
def weekly_meal_planner(user_context):
    print("Generating your weekly meal plan...")
    
    # Fetch meals based on preferences
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    meals_for_the_week = {}
    
    for i, day in enumerate(days_of_week): # Loop over each day of the week (0 - 6)
        daily_meals = []
        print(f"Figuring out 'your kinda' meal for {day}")
        
        # Meal types: breakfast, lunch, dinner, snack
        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            # Check user's meal preferences
            print(f"Your {meal_type} is in the oven.")
            meal_preferences = {
                "diet": ",".join(user_context.get("diet", [])),
                "goal": ",".join(user_context.get("goal", [])),
                "cuisine": ",".join(user_context.get("cuisine", [])),
                "excludeIngredients": ",".join(user_context.get("exclude", [])),
                "includeIngredients": ",".join(user_context.get("includeIngredients", [])),
                "maxReadyTime": user_context.get("maxReadyTime", 30),  # fallback to 30 mins
                "mealType": meal_type,
                "cookingStyle": ",".join(user_context.get("cookingStyle", [])),
                "appliance": ",".join(user_context.get("appliance", [])),
                "spiceLevel": ",".join(user_context.get("spiceLevel", [])),
                "budget": ",".join(user_context.get("budget", [])),
                "apiKey": SPOONACULAR_API_KEY
            }
            

            # Adjust preferences further based on the day (optional: you could make meals rotate)
            daily_meals.append(get_meal_for_day(meal_preferences))
        
        # Add the daily meals to the weekly plan
        meals_for_the_week[day] = {"meals": daily_meals}
    
    return meals_for_the_week

def get_meal_for_day(meal_preferences):
    # Sample request to Spoonacular API or similar service with dynamic preferences
    url = f"{BASE_URL}/recipes/complexSearch"
    response = requests.get(url, params=meal_preferences)
    
    if response.status_code == 200:
        meal_data = response.json().get('results', [])
        if not meal_data:
            return {"error": "No meals found for today's preferences from spoonacular API."}
        
        # Select a random meal (you can apply further logic for this)
        recipe = random.choice(meal_data)
        recipe_id = recipe["id"]
        recipe_url = f"{BASE_URL}/recipes/{recipe_id}/information"
        recipe_details = requests.get(recipe_url, params={"apiKey": SPOONACULAR_API_KEY}).json()
        
        formatted_recipe = {
            "title": recipe_details["title"],
            "readyInMinutes": recipe_details.get("readyInMinutes", "-"),
            "sourceUrl": recipe_details.get("sourceUrl", "#"),
            "image": recipe_details["image"],
            "ingredients": [ingredient["name"] for ingredient in recipe_details["extendedIngredients"]],
            "instructions": recipe_details["instructions"]
        }
        return formatted_recipe
    else:
        return {"error": "Failed to fetch meal suggestions for this day from spoonacular API."}


# Format the meal plan output
def format_meal_plan(week_data, meals_per_day=3):
    if not week_data:
        return "😞 No meal plan found for your preferences."

    output = f"📅 **Your Weekly Meal Plan** ({meals_per_day} meals/day):\n"
    for day, info in week_data.items():
        output += f"\n**{day.capitalize()}**:\n"
        for meal in info["meals"]:
            output += f"- 🍽️ {meal['title']} ({meal['readyInMinutes']} mins) → [View Recipe]({meal['sourceUrl']})\n"
    return output


def fetch_substitutes_from_api(ingredient: str) -> str:
    """
    Fetch ingredient substitutes from the Spoonacular API.

    :param ingredient: The ingredient for which substitutes are needed.
    :return: A string with suggested substitutes and their details.
    """
    # URL for the ingredient substitution endpoint
    url = f"{BASE_URL}/food/ingredients/substitute"

    # Parameters to pass to the API
    params = {
        "ingredientName": ingredient,
        "apiKey": SPOONACULAR_API_KEY
    }

    # Make the request to the Spoonacular API
    response = requests.get(url, params=params)

    if response.status_code == 200:
        substitutes_data = response.json()

        # Check if substitutes are found
        if 'substitutes' in substitutes_data and substitutes_data['substitutes']:
            substitutes = substitutes_data['substitutes']
            substitute_list = "\n".join([f"- {substitute}" for substitute in substitutes])
            return f"**Substitutes for {ingredient}:**\n{substitute_list}"
        else:
            return f"❌ No substitutes found for {ingredient}. Please try again later."
    else:
        return f"❌ Failed to fetch substitutes for {ingredient}. Please try again later."

def get_substitute_suggestions(ingredient: str, reason: str = "general") -> str:
    # Step 1: Use API for ingredient substitutes
    substitute_data = fetch_substitutes_from_api(ingredient)  # API call
    
    # Step 2: Use Gemini to explain benefits
    gemini_prompt = f"""
    Suggest replacements for {ingredient} considering {reason}.
    Substitutes: {substitute_data}
    Explain the health benefits of each, including Ayurvedic compatibility.
    """
    gemini_response = model.generate_content(gemini_prompt)
    
    # Combine both results
    final_suggestions = f"Substitutes: {substitute_data}\n\n{gemini_response.text.strip()}"
    return final_suggestions


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
