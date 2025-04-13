import os
import google.generativeai as genai
from supabase import create_client, Client
from datetime import datetime

# Initialize API Keys
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Memory
chat_history = []
user_id = "default_user"

# Fetch stored long-term memory
def get_preferences():
    response = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
    prefs = [f"{item['preference_type']}: {item['value']}" for item in response.data]
    return prefs

# Save a new preference if not already present
def save_preference(pref_type, value):
    existing = supabase.table("user_preferences").select("*").eq("user_id", user_id).eq("preference_type", pref_type).eq("value", value).execute()
    if not existing.data:
        supabase.table("user_preferences").insert({
            "user_id": user_id,
            "preference_type": pref_type,
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

# Extract preferences from a message (basic example)
def extract_preferences(message):
    prefs = []
    if "no dairy" in message.lower():
        prefs.append(("diet", "no dairy"))
    if "lactose intolerant" in message.lower():
        prefs.append(("condition", "lactose intolerant"))
    if "calorie deficit" in message.lower():
        prefs.append(("goal", "calorie deficit"))
    for pref_type, value in prefs:
        save_preference(pref_type, value)

# Chat with Gemini/OpenAI
def chat_with_model(prompt, context):
    history = [{"role": "user", "parts": [msg]} for msg in context]
    convo = model.start_chat(history=history)
    response = convo.send_message(prompt)
    return response.text

# Main Loop
def run_chat():
    print("🍽️  Welcome to the Nutrition Chatbot CLI")
    prefs = get_preferences()
    if prefs:
        print("\n📌 Your known preferences:")
        for p in prefs:
            print(" -", p)

    print("\nType 'exit' to quit.")
    while True:
        tool = input("\n🛠️ Select tool (meal_plan / substitute / nutrition): ").strip().lower()
        user_input = input("👤 You: ")

        if user_input.lower() == "exit":
            break

        chat_history.append(user_input)
        extract_preferences(user_input)

        # Add context (LTM + STM)
        prompt_context = prefs + chat_history[-3:]  # LTM + last 3 messages
        response = chat_with_model(user_input, prompt_context)

        print("🤖 Bot:", response)

run_chat()
