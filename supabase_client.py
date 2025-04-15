from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from preference_matcher import get_batch_embeddings,cosine_similarity,PREFERENCE_LABELS
from fastapi.concurrency import run_in_threadpool
import numpy as np
import json

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def is_similar(embedding1, embedding2, threshold=0.95):
    return cosine_similarity(embedding1, embedding2) > threshold

def insert_chat_log(user_id, chat_id, role, message):
    supabase.table("chat_logs").insert({
        "user_id": user_id,
        "chat_id": chat_id,
        "role": role,
        "message": message
    }).execute()

def get_chat_history(user_id):
    response = supabase.table("chat_logs").select("*").eq("user_id", user_id).order("timestamp").execute()
    return response.data

def delete_chat(user_id, chat_id):
    supabase.table("chat_logs").delete().eq("user_id", user_id).eq("chat_id", chat_id).execute()
    
async def trim_old_preferences(user_id, max_per_type=20):
    for pref_type in PREFERENCE_LABELS.keys():
        response = supabase.table("user_preferences").select("*")\
            .eq("user_id", user_id).eq("preference_type", pref_type)\
            .order("created_at", desc=True).execute()
        
        data = response.data if response else []
        if len(data) > max_per_type:
            # Delete oldest
            to_delete_ids = [pref["id"] for pref in data[max_per_type:]]
            for pref_id in to_delete_ids:
                supabase.table("user_preferences").delete().eq("id", pref_id).execute()

async def save_user_preferences(user_id, preferences):
    await trim_old_preferences(user_id)
    inserts = []
    
    # Fetch current user preferences
    current_prefs_resp = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
    current_prefs = current_prefs_resp.data if current_prefs_resp else []

    for pref_type, values in preferences.items():
        if not isinstance(values, list):
            values = [values]
        embeddings = get_batch_embeddings(values)

        for val, emb in zip(values, embeddings):
            should_add = True
            for existing in current_prefs:
                if existing["preference_type"] == pref_type:
                    embedding_raw=existing["embedding"]
                    if isinstance(embedding_raw,str):
                        embedding_raw= json.loads(embedding_raw)
                    existing_emb = np.array(embedding_raw, dtype=np.float32)
                    if is_similar(existing_emb, emb):
                        should_add = False
                        break
            if should_add:
                inserts.append({
                    "user_id": user_id,
                    "preference_type": pref_type,
                    "preference_value": val,
                    "embedding": emb
                })

    if inserts:
        await run_in_threadpool(lambda: supabase.table("user_preferences").insert(inserts).execute())
        print("Preferences updated...")
    else:
        print("No new preferences to insert.")



def get_user_preferences(user_id):
    # Fetch all rows for the user
    res = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()

    # If data exists, process it into a structured dictionary for easy access
    if res.data:
        preferences = {}
        for row in res.data:
            pref_type = row["preference_type"]
            pref_value = row["preference_value"]
            if pref_type not in preferences:
                preferences[pref_type] = []
            preferences[pref_type].append(pref_value)
        return preferences
    return None

def store_liked_recipe(user_id, formatted_recipe):
    # Check if the recipe is already liked by this user
    existing_recipe = supabase.table("liked_recipes").select("id").eq("user_id", user_id).eq("recipe_id", formatted_recipe["id"]).execute()

    if existing_recipe.data:
        print("This recipe is already in your liked recipes.")
    else:
        # Store the liked recipe in the liked_recipes table in Supabase
        supabase.table("liked_recipes").insert({
            "user_id": user_id,
            "recipe_id": formatted_recipe["id"],  # Use the recipe ID from the formatted recipe
            "title": formatted_recipe["title"],
            "image_url": formatted_recipe["image"],
            "ingredients": formatted_recipe["ingredients"],
            "instructions": formatted_recipe["instructions"]
        }).execute()
        print("✅ Recipe saved to your liked recipes!")


