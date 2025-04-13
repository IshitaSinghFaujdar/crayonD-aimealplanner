from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from preference_matcher import get_embedding
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

def save_user_preferences(user_id, preferences):
    for pref_type, values in preferences.items():
        if isinstance(values, list):
            for val in values:
                embedding = get_embedding(val)  # whatever method you're using
                supabase.table("user_preferences").insert({
                    "user_id": user_id,
                    "preference_type": pref_type,
                    "preference_value": val,
                    "embedding": embedding
                }).execute()
        else:
            embedding = get_embedding(values)
            supabase.table("user_preferences").insert({
                "user_id": user_id,
                "preference_type": pref_type,
                "preference_value": values,
                "embedding": embedding
            }).execute()


def get_user_preferences(user_id):
    res = supabase.table("user_preferences").select("preferences").eq("user_id", user_id).execute()
    if res.data:
        return res.data[-1]["preferences"]
    return None
