import os
import google.generativeai as genai
from supabase_client import save_user_preferences,insert_chat_log,get_user_preferences
from supabase import create_client, Client
from preference_matcher import match_preferences
import asyncio
from debug2_2 import search_recipes
from tools import (
    get_substitute_suggestions, extract_ingredient_and_reason,
    fetch_nutritional_data, detect_tool_llm
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
def summarize_context(ctx):
    return "\n".join(f"{k}: {', '.join(v) if isinstance(v, list) else v}" for k, v in ctx.items())

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
    context_window = " ".join(chat_history[-20:])
    tool = detect_tool_llm(user_input, context_window) or "general_chat"


    """response = ""
    liked_recipes = supabase.table("liked_recipes") \
    .select("*") \
    .eq("user_id", user_id) \
    .execute()""" 

# Access the result
    """recipes_data = liked_recipes.data"""
    #print("\nBased on your prompt,tool selected:\n")
    #print(tool)
    # Save only if tool requires preference update
    prefs = match_preferences(context_window)
    if not prefs:
        print("No preferences matched")
    else:
        
        print("\npreference\n")
        print(prefs)
    if tool not in ["general chat", "chat", "food_health_explainer"] and user_id:
        new_keys = False
        for k, v in prefs.items():
            if k not in user_context or set(v) - set(user_context.get(k, [])):
                new_keys = True
                break

        if new_keys:
            print("💾 Detected new preferences. Saving to Supabase...")
            await save_user_preferences(user_id, prefs)
        else:
            
            print("🧠 No new preferences to save.\n")
    for k, v in prefs.items():
        if not v:
            continue
        if k not in user_context:
            user_context[k] = v
        elif isinstance(v, list):
            user_context[k] = list(set(user_context[k] + v))
        else:
            user_context[k] = v
            
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
- If the user asks something about old chat, utilise recent chat history(named as context window) to respond.
- If you think user has asked something which requires context and your chat history and user context is not enough to answer that, let user know that our memory management automatically trims very old or irrelevant preferences.
- If the user says something like “Hi” or asks general questions like “how are you?”, respond casually.
- If the user says “what are my preferences?”, summarize the values from `user_context` clearly.
- If the user provides cooking preferences like “I want vegetarian food” or “I can’t eat dairy”, acknowledge them and say: “Got it! I’ve noted that down. If you want a recipe or meal plan, just ask!” and make sure your prompt has 'UPDATED PREFERENCES' in capital, so that I can trigger function to update preferences
- If the user asks a question not related to food, politely say: “I'm focused on food and nutrition. Try asking about meals, ingredients, or your diet preferences.”
- If the user seems unsure, help them rephrase. Example: “If you want me to plan your meals, try saying ‘Plan a week of vegetarian meals for me’.”

Be friendly, helpful, and responsive. You are a supportive food assistant.
        """
        user_preferences=get_user_preferences(user_id)
        context_summary = summarize_context(user_context)
        full_prompt=f"{new_prompt}\nContext:\n{context_summary}\n\nUser Input:\n{user_input}\n\n ,context window: {context_window},user_preferences={user_preferences}"
        try:
            response = model.generate_content(full_prompt).text
            if "UPDATED PREFERENCES" in response.upper():
                await save_user_preferences(user_id, prefs)
                
        except Exception as e:
            print("Oops I think I am slow:", e)
    elif tool == "quick_meal_finder" or tool == "weekly_meal_planner":
        # Search for recipes based on preferences and input
        recipes = await search_recipes(user_context, user_input)
        
        response = f"Here are some recipe suggestions: {recipes}"

    elif tool == "substitute_finder":
        ingredient =await extract_ingredient_and_reason(user_input)
        subs =await get_substitute_suggestions(ingredient,user_input)
        response = f"🧪 Substitutes: {subs}"

    elif tool == "food_health_explainer":
        ingredient=await extract_ingredient_and_reason(user_input)
        explainer = await fetch_nutritional_data(ingredient,user_input)
        response = f"💡 Explainer: {explainer}"

    else:
        response = "💬 Bot: I'm still learning! Feel free to ask more!"

    # Save chat logs in Supabase
    if user_id:
        await insert_chat_log(user_id, chat_id=chat_id, role="user", message=user_input)
        await insert_chat_log(user_id, chat_id=chat_id, role="bot", message=response)

    return response
