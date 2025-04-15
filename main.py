import os
import google.generativeai as genai
from supabase_client import save_user_preferences,insert_chat_log
from supabase import create_client, Client
from preference_matcher import match_preferences
import asyncio
from tools import (
    quick_meal_finder, 
    weekly_meal_planner,
    get_substitute_suggestions, extract_ingredient_and_reason,
    food_health_explainer, detect_tool_llm
)
import uuid
# Config
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")
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

async def process_input(user_input, user_email=None, user_id=None):
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

    #print(f"Type of prefs: {type(prefs)}")
    #print(f"Prefs: {prefs}")

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
    liked_recipes = supabase.table("liked_recipes") \
    .select("*") \
    .eq("user_id", user_id) \
    .execute()

# Access the result
    recipes_data = liked_recipes.data
    print("\nBased on your prompt,tool selected:\n")
    print(tool)
    if tool not in ["general chat", "chat"] and prefs and user_id:
        new_keys = any(k for k, v in prefs.items() if k not in user_context or v != user_context[k])
        if new_keys:
            await save_user_preferences(user_id, prefs)
    if tool =="general chat":
        new_prompt="""
ou are the general fallback assistant in a food and meal planning chatbot.

You can do the following:
- Chat casually with the user.
- Answer food and nutrition-related questions.
- Tell the user their preferences from `user_context`.
- Return their liked recipes from `liked_recipes`.
- Guide the user to use one of the following tools:
  - weekly_meal_planner
  - quick_meal_finder
  - substitute_finder
  - food_health_explainer

Instructions:
- If the user says something like “Hi” or asks general questions like “how are you?”, respond casually.
- If the user says “what are my preferences?”, summarize the values from `user_context` clearly.
- If the user says “what recipes did I like?”, return the `liked_recipes`. If the list is empty, say: "Oops! Looks like I couldn't fetch your liked recipes. Try liking a few recipes or updating them!"
- If the user provides cooking preferences like “I want vegetarian food” or “I can’t eat dairy”, acknowledge them and say: “Got it! I’ve noted that down. If you want a recipe or meal plan, just ask!” and make sure your prompt has 'UPDATED PREFERENCES' in capital, so that I can trigger function to update preferences
- If the user asks a question not related to food, politely say: “I'm focused on food and nutrition. Try asking about meals, ingredients, or your diet preferences.”
- If the user seems unsure, help them rephrase. Example: “If you want me to plan your meals, try saying ‘Plan a week of vegetarian meals for me’.”

Be friendly, helpful, and responsive. You are a supportive food assistant.
        """
        full_prompt=f"{new_prompt}\nContext:\n{user_context}\n\nUser Input:\n{user_input}\n\n liked_recipes:{recipes_data}"
        try:
            response = model.generate_content(full_prompt).text
            if "UPDATED PREFERENCES" in response.upper():
                await save_user_preferences(user_id, prefs)
                
        except Exception as e:
            print("Oops I think I am slow:", e)
    elif tool == "quick_meal_finder":
        if "maxReadyTime" not in user_context:
            time = input("⏱️ How many minutes do you have to cook? ")
            try:
                user_context["maxReadyTime"] = int(time)
            except:
                user_context["maxReadyTime"] = 45

        if "cooking_skill" not in user_context:
            skill = input("👩‍🍳 What's your cooking skill level? (beginner/intermediate/expert): ").lower()
            user_context["cooking_skill"] = skill

        meals = await quick_meal_finder(user_context)
        response = meals

    elif tool == "weekly_meal_planner":
        if "meals_per_day" not in user_context:
            mpd = input("🍽️ How many meals per day? (2/3): ")
            user_context["meals_per_day"] = int(mpd) if mpd.isdigit() else 3

        plan = await weekly_meal_planner(user_context)
        response = plan

    elif tool == "substitute_finder":
        ingredient, reason =await extract_ingredient_and_reason(user_input)
        subs =await get_substitute_suggestions(ingredient, reason)
        response = f"🧪 Substitutes: {subs}"

    elif tool == "food_health_explainer":
        ingredient, reason =await extract_ingredient_and_reason(user_input)
        explainer = await food_health_explainer(ingredient, reason)
        response = f"💡 Explainer: {explainer}"

    else:
        response = "💬 Bot: I'm still learning! Feel free to ask more!"

    # Save chat logs in Supabase
    if user_id:
        insert_chat_log(user_id, chat_id=chat_id, role="user", message=user_input)
        insert_chat_log(user_id, chat_id=chat_id, role="bot", message=response)

    return response