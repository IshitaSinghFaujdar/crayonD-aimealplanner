import os
import re
import json
import random
import asyncio
import requests
from typing import Tuple
from datetime import datetime
from supabase import create_client, Client
import google.generativeai as genai
from config import SUPABASE_KEY, SUPABASE_URL, GOOGLE_API_KEY, SPOONACULAR_API_KEY

# Initialize API Keys
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_URL = "https://api.spoonacular.com"

# Use an in-memory cache to store preferences and results temporarily
preferences_cache = {}

def detect_tool_llm(prompt: str, context: str) -> str:
    system_prompt = """
You are an intelligent tool router for a chatbot. Based on user input and recent context, respond with one of the following tools ONLY:
- weekly_meal_planner
- substitute_finder
- quick_meal_finder
- food_health_explainer
- general chat

Guidelines:
- If the user is saying things like "hi", "hello", "what's up", or wants to chat casually or ask what you can do, return 'general chat'.
- If the user gives preferences only (like 'I want vegetarian food'), return 'general chat' so the assistant can guide the user to rephrase or store this information.
- Do NOT guess or invent a tool name. Use only the above.
Return ONLY the tool name. No extra text.
    """
    full_prompt = f"{system_prompt}\nContext:\n{context}\n\nUser Input:\n{prompt}"
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip().lower()
    except Exception as e:
        print("Oops,Looks like our server is down!:", e)
        return "chat"

async def fetch_quick_meals(user_context):
    meal_type = input("What meal is this? (breakfast/lunch/dinner/snack) ").lower()
    meal_preferences = build_meal_preferences(user_context, meal_type)
    meal = await get_meal_for_day(meal_preferences)
    # Humanize the final meal suggestion
    return await humanize_response(meal)


async def quick_meal_finder(user_context):
    
    # Fetch a single quick recipe based on the user's preferences
    quick_recipe = await fetch_quick_meals(user_context)
    
    # If the response is valid, format the recipe and return it
    if quick_recipe:
        return quick_recipe
    else:
        return {"error": "No quick recipe found for the given preferences."}


async def fetch_nutritional_data(food_description: str) -> str:
    url = f"{BASE_URL}/food/ingredients/{food_description}/nutritionWidget.json"
    params = {"apiKey": SPOONACULAR_API_KEY}
    response = await asyncio.to_thread(requests.get, url, params=params)

    if response.status_code == 200:
        nutrition_data = response.json()
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

async def food_health_explainer(user_context):
    food_name = user_context.get('food_name', '')
    nutrition_data = await fetch_nutritional_data(food_name)
    return await humanize_response(nutrition_data)



async def fetch_substitutes_from_api(ingredient: str) -> str:
    url = f"{BASE_URL}/food/ingredients/substitute"
    params = {"ingredientName": ingredient, "apiKey": SPOONACULAR_API_KEY}
    response = await asyncio.to_thread(requests.get, url, params=params)

    if response.status_code == 200:
        substitutes_data = response.json()
        if 'substitutes' in substitutes_data and substitutes_data['substitutes']:
            substitutes = substitutes_data['substitutes']
            substitute_list = "\n".join([f"- {substitute}" for substitute in substitutes])
            return f"**Substitutes for {ingredient}:**\n{substitute_list}"
        else:
            return f"❌ No substitutes found for {ingredient}. Please try again later."
    else:
        return f"❌ Failed to fetch substitutes for {ingredient}. Please try again later."

async def get_substitute_suggestions(ingredient: str, reason: str = "general") -> str:
    substitute_data = await fetch_substitutes_from_api(ingredient)
    gemini_prompt = f"""
    Suggest replacements for {ingredient} considering {reason}.
    Substitutes: {substitute_data}
    Explain the health benefits of each, including Ayurvedic compatibility.
    """
    gemini_response = model.generate_content(gemini_prompt)
    final_suggestions = f"Substitutes: {substitute_data}\n\n{gemini_response.text.strip()}"
    return await humanize_response(final_suggestions)


async def weekly_meal_planner(user_context):
    # Fetch all the meal data as usual
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    meals_for_the_week = {}
    tasks = [get_daily_meal_plan_for_day(user_context, day) for day in days_of_week]
    daily_meals = await asyncio.gather(*tasks)
    for day, meals in zip(days_of_week, daily_meals):
        meals_for_the_week[day] = {"meals": meals}

    # Pass the weekly meal plan to Gemini for humanization
    return await humanize_response(meals_for_the_week)


async def get_daily_meal_plan_for_day(user_context, day):
    daily_meals = []
    for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
        meal_preferences = build_meal_preferences(user_context, meal_type)
        daily_meals.append(await get_meal_for_day(meal_preferences))
    return daily_meals



def build_meal_preferences(user_context, meal_type):
    return {
        "diet": ",".join(user_context.get("diet", [])),
        "goal": ",".join(user_context.get("goal", [])),
        "cuisine": ",".join(user_context.get("cuisine", [])),
        "excludeIngredients": ",".join(user_context.get("exclude", [])),
        "includeIngredients": ",".join(user_context.get("includeIngredients", [])),
        "maxReadyTime": user_context.get("maxReadyTime", 30),
        "mealType": meal_type,
        "cookingStyle": ",".join(user_context.get("cookingStyle", [])),
        "appliance": ",".join(user_context.get("appliance", [])),
        "spiceLevel": ",".join(user_context.get("spiceLevel", [])),
        "budget": ",".join(user_context.get("budget", [])),
        "apiKey": SPOONACULAR_API_KEY
    }

async def get_meal_for_day(meal_preferences):
    url = f"{BASE_URL}/recipes/complexSearch"
    meal_preferences["apiKey"] = SPOONACULAR_API_KEY
    response = await asyncio.to_thread(requests.get, url, params=meal_preferences)
    
    if response.status_code == 200:
        meal_data = response.json().get('results', [])
        
        if not meal_data:
            return {"error": "No meals found for this day's preferences from spoonacular API."}

        recipe = random.choice(meal_data)
        recipe_id = recipe["id"]
        if not recipe_id:
            return {"error": "Recipe ID missing in Spoonacular response."}
        recipe_url = f"{BASE_URL}/recipes/{recipe_id}/information"
        recipe_response = await asyncio.to_thread(requests.get, recipe_url, params={"apiKey": SPOONACULAR_API_KEY})
        if recipe_response.status_code != 200:
            return {"error": f"Failed to fetch recipe details for ID {recipe_id} from Spoonacular API."}

        recipe_details = recipe_response.json()
        formatted_recipe = {
            "title": recipe_details["title","Unknown Recipe"],
            "readyInMinutes": recipe_details.get("readyInMinutes", "-"),
            "sourceUrl": recipe_details.get("sourceUrl", "#"),
            "image": recipe_details["image",""],
            "ingredients": [
                ingredient.get("name", "") 
                for ingredient in recipe_details.get("extendedIngredients", [])
            ],
            "instructions": recipe_details.get("instructions") or "Instructions not available."
        }
        return formatted_recipe
    else:
        return {"error": "Failed to fetch meal suggestions for this day from spoonacular API."}

async def extract_ingredient_and_reason(user_input: str) -> Tuple[str, str]:
    system_prompt = """
You are a food and health assistant.
Given a user's question, extract two things:
1. The food item or ingredient they're asking about (e.g., "papaya", "milk", "paneer")
2. The health-related reason or context if mentioned (e.g., "PCOD", "weight loss", "allergy")

Only return a dictionary like:
{"ingredient": "papaya", "reason": "PCOD"}

If the reason is not mentioned, just say:
{"ingredient": "papaya", "reason": "general"}
"""

    gemini_response = await model.generate_content_async(
        system_prompt + "\n\nUser: " + user_input
    )

    try:
        data = eval(gemini_response.text.strip())
        return data.get("ingredient", "unknown").lower(), data.get("reason", "general").lower()
    except Exception as e:
        print("Failed to parse Gemini response:", e)
        return "unknown", "general"


def detect_save_phrase(user_input: str) -> bool:
    # List of phrases to trigger saving the recipe
    save_phrases = ["i like this", "save this", "bookmark this", "save recipe", "like this"]
    
    # Check if any of the save phrases match the user input
    for phrase in save_phrases:
        if re.search(r"\b" + re.escape(phrase) + r"\b", user_input.lower()):
            return True
    return False


async def humanize_response(raw_data: dict) -> str:
    # Construct the prompt for Gemini to humanize the data
    prompt = f"""
Task: You are an AI assistant tasked with generating a structured, engaging, and conversational response that combines both user input and tool output. Please structure your response as follows:

1. **User Input**: The original user query or request.
2. **Tool Output**: The relevant information or result generated by the tool.

Make sure the final output is clear, well-organized, and easy to read. Use headings, bullet points, and clear explanations when necessary. Ensure that the output is user-friendly and contains all the important details.

Here’s the raw data to humanize:

{json.dumps(raw_data, indent=2)}

Response:
"""
    
    # Generate the response from Gemini
    try:
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error during humanization: {e}")
        return "Sorry, there was an issue generating the response."