from supabase import create_client
from config import SUPABASE_KEY, SUPABASE_URL
from main import process_input, start_new_chat
from supabase_client import store_liked_recipe
from preference_matcher import cache_label_embeddings
# from tools import detect_save_phrase  # Uncomment if using save detection

import asyncio,nest_asyncio

# Initialize Supabase and cache embeddings
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
cache_label_embeddings()

nest_asyncio.apply()  # Allows reuse of event loop

def run_async(func, *args, **kwargs):
    return asyncio.get_event_loop().run_until_complete(func(*args, **kwargs))





def start_chat(email, user_id):
    print("\n🤖 ChatBot: Hello! Ask me anything (type 'exit' to quit, 'menu' to go back, or 'new chat' to reset)\n"
          "I have the following tools:\n"
          "- Weekly Meal Planner\n"
          "- Quick Meal Recipes\n"
          "- Ingredient Substituter\n"
          "- Item Nutrition Info\n"
          "If at any point you like a recipe, you can say things like 'i like this', 'save this', 'bookmark this'.\n")

    start_new_chat()
    # current_recipe = None  # Uncomment and re-enable save flow when needed

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        elif user_input.lower() == "menu":
            print("🔙 Returning to menu...")
            break
        else:
            try:
                response = run_async(process_input, user_input, user_email=email, user_id=user_id)
                print(f"🤖 ChatBot: {response}")
                
                # TODO: Uncomment and expand this block to support saving liked recipes
                # if current_recipe and detect_save_phrase(user_input):
                #     print("🤖 ChatBot: Please provide the Recipe ID or URL:")
                #     recipe_input = input("You: ").strip()
                #     liked_recipe = next((r for r in current_recipe if r['id'] == recipe_input or r['url'] == recipe_input), None)
                #     if liked_recipe:
                #         store_liked_recipe(user_id, liked_recipe)
                #         print("✅ Recipe saved to your liked recipes!")
                #     else:
                #         print("⚠️ Couldn't find a recipe with that ID/URL.")

            except Exception as e:
                print(f"⚠️ Error: {e}")


def signup():
    email = input("Enter email: ")
    password = input("Enter password: ")
    res = supabase.auth.sign_up({"email": email, "password": password})
    if res.user:
        print("✅ Signed up successfully. Please login.")
    else:
        print("❌ Error during signup.")


def login():
    email = input("Enter email: ")
    password = input("Enter password: ")
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if res.user:
        user_id = res.user.id
        start_chat(email, user_id)
    else:
        print("❌ Invalid credentials.")


def reset_password():
    email = input("Enter email for password reset: ")
    supabase.auth.reset_password_email(email)
    print("📧 Password reset email sent.")


def menu():
    while True:
        print("\n🔐 Welcome! Please login or signup:")
        action = input("Type 'login', 'signup', 'reset', or 'exit': ").strip().lower()
        if action == "signup":
            signup()
        elif action == "login":
            login()
        elif action == "reset":
            reset_password()
        elif action == "exit":
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid input. Please try again.")


if __name__ == "__main__":
    menu()
 