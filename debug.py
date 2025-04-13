import os
import google.generativeai as genai
from supabase import create_client, Client
from datetime import datetime
from preference_matcher import match_preferences
import requests
import json
from tools import format_quick_meals, quick_meal_finder, get_meal_plan, format_meal_plan, get_substitute_suggestions, food_health_explainer, extract_ingredient_and_reason

# Initialize API Keys (Use your environment variables or mock for testing)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro-002")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_URL = "https://api.spoonacular.com"
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Mock user preferences (for testing)
user_context = {
    "diet": ["vegan"],
    "maxReadyTime": 30,
    "includeIngredients": ["tomato", "onion", "garlic"],
    "targetCalories": 1200,
    "exclude": ["cheese"],
    "health_context": "PCOD"
}

# Mock user inputs to simulate interactions
def test_quick_meal_finder():
    print("Testing Quick Meal Finder...")
    user_input = "I want quick meals with tomatoes, onion, and garlic."
    print(f"User Input: {user_input}")
    result = quick_meal_finder(user_context)
    print(f"Quick Meal Finder Results: {result}")
    print("-" * 40)

def test_meal_planner():
    print("Testing Meal Planner...")
    user_input = "Can you give me a weekly meal plan with vegan meals, excluding cheese, and targeting 1200 calories?"
    print(f"User Input: {user_input}")
    result = get_meal_plan(user_context)
    print(f"Meal Planner Results: {result}")
    print("-" * 40)

def test_substitute_finder():
    print("Testing Substitute Finder...")

    # Simulating user input asking for milk substitute
    user_input = "What can I use instead of milk for my diet?"
    print(f"User Input: {user_input}")
    
    # Extract ingredient and reason
    ingredient, reason = extract_ingredient_and_reason(user_input)
    print(f"Extracted Ingredient: {ingredient}, Extracted Reason: {reason}")
    
    # Get substitute suggestions
    result = get_substitute_suggestions(ingredient, reason)
    print(f"Substitute Suggestions: {result}")
    print("-" * 40)

def test_food_health_explainer():
    print("Testing Food Health Explainer...")
    # Simulating user asking about the effect of avocado on PCOD
    user_input = "How does avocado affect PCOD?"
    print(f"User Input: {user_input}")
    
    # Get health explanation
    result = food_health_explainer("avocado", "PCOD")
    print(f"Food Health Explanation: {result}")
    print("-" * 40)

def test_extract_ingredient_and_reason():
    print("Testing Extract Ingredient and Reason...")

    # Testing the ingredient extraction function with different user inputs

    # Input 1: Milk substitute
    user_input_1 = "What can I use instead of milk for my diet?"
    print(f"User Input: {user_input_1}")
    ingredient_1, reason_1 = extract_ingredient_and_reason(user_input_1)
    print(f"Extracted Ingredient: {ingredient_1}, Extracted Reason: {reason_1}")

    # Input 2: Ingredient for PCOD
    user_input_2 = "How does avocado affect PCOD?"
    print(f"User Input: {user_input_2}")
    ingredient_2, reason_2 = extract_ingredient_and_reason(user_input_2)
    print(f"Extracted Ingredient: {ingredient_2}, Extracted Reason: {reason_2}")

    # Input 3: Replace sugar
    user_input_3 = "What can I use instead of sugar for my diet?"
    print(f"User Input: {user_input_3}")
    ingredient_3, reason_3 = extract_ingredient_and_reason(user_input_3)
    print(f"Extracted Ingredient: {ingredient_3}, Extracted Reason: {reason_3}")

    # Input 4: Replace gluten
    user_input_4 = "Can I replace gluten with something for a gluten-free diet?"
    print(f"User Input: {user_input_4}")
    ingredient_4, reason_4 = extract_ingredient_and_reason(user_input_4)
    print(f"Extracted Ingredient: {ingredient_4}, Extracted Reason: {reason_4}")
    print("-" * 40)

def main():
    print("Debugging Chatbot Functionalities")

    # Run tests for each function
    test_quick_meal_finder()
    test_meal_planner()
    test_substitute_finder()
    test_food_health_explainer()
    test_extract_ingredient_and_reason()

if __name__ == "__main__":
    main()
