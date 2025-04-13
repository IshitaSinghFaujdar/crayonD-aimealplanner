import os
import google.generativeai as genai
from supabase import create_client, Client
from datetime import datetime
from preference_matcher import match_preferences
import requests
import json
from tools import format_quick_meals,quick_meal_finder,get_meal_plan,format_meal_plan,get_substitute_suggestions,food_health_explainer,extract_ingredient_and_reason
# Initialize API Keys
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro-002")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BASE_URL = "https://api.spoonacular.com"
SPOONACULAR_API_KEY=os.getenv("SPOONACULAR_API_KEY")
# Session memory
user_context = {}
chat_history = []

# Simple tool detector
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

    full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser Input:\n{prompt}\n\nWhat tool should be activated?"

    try:
        response = model.generate_content(full_prompt)
        tool = response.text.strip().lower()
        if tool in ["meal_planner", "substitute_finder", "chat"]:
            return tool
        else:
            return "chat"
    except Exception as e:
        print("Tool detection error:", e)
        return "chat"



# Main chat loop
def main():
    print("🤖 ChatBot: Hello! Ask me anything (type 'exit' to quit).")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        
        # Add user input to chat history
        chat_history.append(f"User: {user_input}")

        # Combine recent history for context-aware preference extraction
        context_input = " ".join(chat_history[-10:])  # Adjust number as needed
        prefs = match_preferences(context_input)

# Merge extracted preferences into user_context
        for k, v in prefs.items():
            if k not in user_context:
                user_context[k] = v
            else:
                for item in v:
                    if item not in user_context[k]:
                        user_context[k].append(item)

# Decide which tool to use based on prompt + memory
        context_window = " ".join(chat_history[-10:])
        tool = detect_tool_llm(user_input, context_window)


        if tool == "meal_planner":
            result = get_meal_plan(user_context)
            print("Bot:", result)

        elif tool == "substitute_finder":
            # Use the smart extraction logic for ingredient and reason
            ingredient, reason = extract_ingredient_and_reason(user_input)
            result = get_substitute_suggestions(ingredient, reason)
            print("Bot:", result)



        elif tool == "quick_meal_finder":
            result = quick_meal_finder(user_context)
            print("Bot:", result)

        elif tool == "food_health_explainer":
            # You may extract more context-aware inputs
            health = user_context.get("health_context", "PCOD")
            food = user_input  # assuming user describes food in their message
            result = food_health_explainer(food, health)
            print("Bot:", result)

        else:
            print("Bot: I'm still learning! Soon I'll answer this too 😊")

if __name__ == "__main__":
    main()