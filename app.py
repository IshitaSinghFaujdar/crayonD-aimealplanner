import os
import uuid
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from preference_matcher import get_embedding
from tools import (
    quick_meal_finder,
    get_meal_plan,
    food_health_explainer,
    get_substitute_suggestions,
    extract_ingredient_and_reason,
    format_meal_plan,
)
from preference_matcher import match_preferences
from datetime import datetime
from config import SUPABASE_KEY,SUPABASE_URL

# Setup Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------- MODELS ----------------
class Message(BaseModel):
    user_id: str
    chat_id: str
    message: str

class AuthRequest(BaseModel):
    email: str
    password: str

class ResetRequest(BaseModel):
    email: str

# ------------- AUTH ----------------
@app.post("/signup")
def signup(auth: AuthRequest):
    response = supabase.auth.sign_up({"email": auth.email, "password": auth.password})
    if response.user:
        return {"message": "User created", "user_id": response.user.id}
    raise HTTPException(status_code=400, detail="Signup failed")

@app.post("/login")
def login(auth: AuthRequest):
    response = supabase.auth.sign_in_with_password({"email": auth.email, "password": auth.password})
    if response.user:
        return {"message": "Login successful", "user_id": response.user.id}
    raise HTTPException(status_code=401, detail="Login failed")

@app.post("/reset")
def reset_password(req: ResetRequest):
    res = supabase.auth.reset_password_email(req.email)
    return {"message": "Password reset email sent"}

# ------------- CHAT ----------------
@app.post("/chat")
def chat(msg: Message):
    user_input = msg.message
    user_id = msg.user_id
    chat_id = msg.chat_id or str(uuid.uuid4())

    # 1. Try to match preferences (using Gemini embedding)
    extracted_prefs = match_preferences(user_input)

    # 2. Save preferences
    for key, values in extracted_prefs.items():
        for value in values:
            supabase.table("user_preferences").insert({
                "user_id": user_id,
                "preference_type": key,
                "preference_value": value,
                "embedding": get_embedding(value)
            }).execute()

    # 3. Get all stored preferences for user
    prefs_res = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
    prefs_data = prefs_res.data if prefs_res.data else []
    context = {
        "diet": [p["preference_value"] for p in prefs_data if p["preference_type"] == "diet"],
        "exclude": [p["preference_value"] for p in prefs_data if p["preference_type"] == "exclude"],
        "includeIngredients": [p["preference_value"] for p in prefs_data if p["preference_type"] == "includeIngredients"],
        "targetCalories": 1800,
        "maxReadyTime": 30,
    }

    # 4. Decide which tool to use based on keywords
    response_text = "🤖 Sorry, I couldn't understand your request."

    if any(x in user_input.lower() for x in ["quick meal", "something fast", "30 min", "easy to cook"]):
        recipes = quick_meal_finder(context)
        if isinstance(recipes, dict) and "error" in recipes:
            response_text = "❌ Failed to fetch quick meal suggestions."
        else:
            response_text = "🍽️ Here are some quick meals:\n\n"
            for recipe in recipes:
                response_text += f"👉 {recipe['title']}\nInstructions: {recipe['instructions'][:200]}...\n\n"

    elif any(x in user_input.lower() for x in ["weekly meal plan", "plan my week", "week's diet"]):
        week_data = get_meal_plan(context)
        response_text = format_meal_plan(week_data)

    elif any(x in user_input.lower() for x in ["health", "is it good", "nutrition", "ayurveda"]):
        response_text = food_health_explainer(user_input, context.get("goal", "general"))

    elif any(x in user_input.lower() for x in ["substitute", "replace", "instead of"]):
        ingredient, reason = extract_ingredient_and_reason(user_input)
        if ingredient:
            response_text = get_substitute_suggestions(ingredient, reason or "general")
        else:
            response_text = "❌ I couldn't identify the ingredient you want to substitute."

    # 5. Save chat
    supabase.table("chat_logs").insert({
        "user_id": user_id,
        "chat_id": chat_id,
        "message": user_input,
        "response": response_text,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    return {"chat_id": chat_id, "response": response_text}

# ------------- CHAT MANAGEMENT -------------
@app.get("/chat/history/{user_id}")
def get_history(user_id: str):
    res = supabase.table("chat_logs").select("*").eq("user_id", user_id).order("timestamp", desc=True).execute()
    return res.data

@app.delete("/chat/{chat_id}")
def delete_chat(chat_id: str):
    supabase.table("chat_logs").delete().eq("chat_id", chat_id).execute()
    return {"message": "Chat deleted"}

@app.get("/newchat")
def new_chat():
    return {"chat_id": str(uuid.uuid4())}
