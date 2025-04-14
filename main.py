import os
import google.generativeai as genai
from supabase_client import save_user_preferences,insert_chat_log
from supabase import create_client, Client
from preference_matcher import match_preferences
from tools import (
    quick_meal_finder, format_quick_meals,
    weekly_meal_planner, format_meal_plan,
    get_substitute_suggestions, extract_ingredient_and_reason,
    food_health_explainer, detect_tool_llm
)
import uuid
# Config
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro-002")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Session memory
user_context = {}
chat_history = []

def start_new_chat():
    chat_id = str(uuid.uuid4())
    user_context["chat_id"] = chat_id
    chat_history.clear()
    return chat_id

def process_input(user_input, user_email=None, user_id=None):
    global chat_history, user_context
       # Handle new chat command
    if user_input.lower() == "new chat":
        new_id = start_new_chat()
        return f"✨ Started a new chat session: {new_id[:8]}..."

    # Set chat_id if not already set
    if "chat_id" not in user_context:
        user_context["chat_id"] = str(uuid.uuid4())

    chat_id = user_context["chat_id"]
    chat_history.append(f"User: {user_input}")
    print("Fetching short term context...")
    context_window = " ".join(chat_history[-10:])
    prefs = match_preferences(context_window)
    print("\npreference\n")
    print(prefs)
    # Save extracted preferences
    if user_id:
        save_user_preferences(user_id, prefs)
    print(f"Type of prefs: {type(prefs)}")
    print(f"Prefs: {prefs}")

    for k, v in prefs.items():
        if not v:
            continue
        if k not in user_context:
            user_context[k] = v
        elif isinstance(v, list):
            user_context[k] = list(set(user_context[k] + v))

        else:
            user_context[k]=v
    tool = detect_tool_llm(user_input, context_window)

    # Initialize response variable
    response = ""
    print("\nBased on your prompt,tool selected:\n")
    print(tool)
    if tool == "quick_meal_finder":
        if "maxReadyTime" not in user_context:
            time = input("⏱️ How many minutes do you have to cook? ")
            try:
                user_context["maxReadyTime"] = int(time)
            except:
                user_context["maxReadyTime"] = 30

        if "cooking_skill" not in user_context:
            skill = input("👩‍🍳 What's your cooking skill level? (beginner/intermediate/expert): ").lower()
            user_context["cooking_skill"] = skill

        meals = quick_meal_finder(user_context)
        response = format_quick_meals(meals)

    elif tool == "weekly_meal_planner":
        if "meals_per_day" not in user_context:
            mpd = input("🍽️ How many meals per day? (2/3): ")
            user_context["meals_per_day"] = int(mpd) if mpd.isdigit() else 3

        plan = weekly_meal_planner(user_context)
        print("Just another minute, making sure you can read the recipes.😉")
        response = format_meal_plan(plan, user_context.get("meals_per_day", 3))

    elif tool == "substitute_finder":
        ingredient, reason = extract_ingredient_and_reason(user_input)
        subs = get_substitute_suggestions(ingredient, reason)
        response = f"🧪 Substitutes: {subs}"

    elif tool == "food_health_explainer":
        ingredient, reason = extract_ingredient_and_reason(user_input)
        explainer = food_health_explainer(ingredient, reason)
        response = f"💡 Explainer: {explainer}"

    else:
        response = "💬 Bot: I'm still learning! Feel free to ask more!"

    # Save chat logs in Supabase
    if user_id:
        insert_chat_log(user_id, chat_id=chat_id, role="user", message=user_input)
        insert_chat_log(user_id, chat_id=chat_id, role="bot", message=response)

    return response