import os
import re
import json
import random
import asyncio
import requests
import aiohttp
from typing import Tuple
from datetime import datetime
from supabase import create_client, Client
import google.generativeai as genai
from config import SUPABASE_KEY, SUPABASE_URL, GOOGLE_API_KEY, SPOONACULAR_API_KEY
import requests
import urllib.parse
import asyncio
from config import SERPER_URL as BASE_URL
from config import SERPER_KEY as API_KEY
# Initialize API Keys
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_URL = "https://api.spoonacular.com"
TASTY_API_URL = "https://api.tasty.co/api/v1/recipes/list"

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
        print(f"ingredient found:{response.text.strip().lower()}")
        return response.text.strip().lower()
    except Exception as e:
        print("Oops,Looks like our server is down!:", e)
        return "chat"
#-----
#TOOL 1
#-----
async def fetch_nutritional_data(ingredient,user_input):
    url = f"https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": ingredient,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:

            if response.status== 200:
                data = await response.json()
                products = data.get("products", [])
                explain = []
                for p in products:
                    name = p.get("product_name", "Unnamed")
                    grade = p.get("nutriscore_grade", "unknown")
                    warning = "⚠️ High in sugar or additives" if grade in ["d", "e"] else "✅ Looks healthy"
                    explain.append(f"{name} → Nutriscore: {grade.upper()} | {warning}")
                return await humanize_response(explain,user_input)
            else:
                print("Open Food Facts Error:", response.text)
                return []

#-----
#TOOL 2
#-----
async def get_substitute_suggestions(ingredient: str,user_input) -> str:
    url = f"https://world.openfoodfacts.org/cgi/search.pl"
    params = {
            "search_terms": ingredient,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 10
        }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        products = response.json().get("products", [])
        final_suggestions = [p["product_name"] for p in products if "product_name" in p]
    else:
        print("Open Food Facts Error:", response.text)
    return await humanize_response(final_suggestions,user_input)

#-----
#TOOL 3 AND 4
#-----
def build_search_query(user_context, user_input):
    # Start with user input (e.g., "vegetarian meal plan")
    query = user_input
    
    # Add user context to refine search (e.g., "low fat", "milk", "cheese")
    if user_context.get("diet"):
        query += " " + " ".join(user_context["diet"])
    if user_context.get("includeIngredients"):
        query += " " + " ".join(user_context["includeIngredients"])

    # URL encode the query to make it safe for the API request
    return urllib.parse.quote(query)

# Function to search for recipes using the Serper API
async def search_recipes(user_context, user_input):
    # Build the search query
    search_query = build_search_query(user_context, user_input)
    
    # Construct the full URL with the search query
    url = f"{BASE_URL}?q={search_query}&apiKey={API_KEY}"
    
    # Send the GET request
    response = requests.get(url)
    
    # Check the status code and handle response
    if response.status_code == 200:
        # Parse and return the response data (e.g., recipes)
        return await humanize_response(response.json(),user_input)
    else:
        # If there’s an error, return the status code and message
        return {"error": f"Failed to fetch recipes. Status code: {response.status_code}"}



#-----
#HELPER FUNCTIONS
#-----

async def extract_ingredient_and_reason(user_input: str) -> str:
    system_prompt = """
You are a food and health assistant.
Given a user's question, extract the following:
1. The food item or ingredient they're asking about (e.g., "papaya", "milk", "paneer")

Only return a string input like:"papaya"

If you can not extract the item/ingredient whose substitute is being asked, return "unknown"
"""

    gemini_response = await model.generate_content_async(f"{system_prompt} \n\nUser:{user_input}")

    try:
        ingredient = gemini_response.text.strip().strip('"').lower()
        return ingredient
    except Exception as e:
        print("Failed to parse Gemini response:", e)
        return "unknown"


def detect_save_phrase(user_input: str) -> bool:
    # List of phrases to trigger saving the recipe
    save_phrases = ["i like this", "save this", "bookmark this", "save recipe", "like this"]
    
    # Check if any of the save phrases match the user input
    for phrase in save_phrases:
        if re.search(r"\b" + re.escape(phrase) + r"\b", user_input.lower()):
            return True
    return False


async def humanize_response(raw_data: dict,user_input) -> str:
    # Construct the prompt for Gemini to humanize the data
    prompt = f"""
Task: You are an AI assistant tasked with generating a structured, engaging, and conversational response. Please structure your response as follows:

1. **User Input**: The original user query or request. {user_input}
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