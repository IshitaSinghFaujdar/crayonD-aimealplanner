from supabase import create_client
import os
import asyncio
from main import process_input,start_new_chat # Import the main function from main.py
from config import SUPABASE_KEY,SUPABASE_URL
from supabase_client import store_liked_recipe
from preference_matcher import cache_label_embeddings
from tools import detect_save_phrase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
cache_label_embeddings()
def start_chat(email, user_id):
    print("\n🤖 ChatBot: Hello! Ask me anything (type 'exit' to quit, 'menu' to go back, or 'new chat' to reset)\nI have the following tools\n-Weekly Meal Planner\n-Quick meal recipes\n-Ingredient Substituter\n-Item Nutrition info.\nIf at any point you like any of the recipes I gave, you could use phrases like 'i like this', 'save this', 'bookmark this', 'save recipe', 'like this'. \nEnjoy chatting.\n")
    start_new_chat()
    current_recipe = None  # Store the current recipe in context
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break
        elif user_input.lower() == "menu":
            print("🔙 Returning to menu...")
            break
        else:
            try:
                # Call the main function to process user input and get the response
                response = asyncio.run(process_input(user_input, user_email=email, user_id=user_id))
                print(f"🤖 ChatBot: {response}")
                
                # Check if response contains recipes (e.g., Weekly Meal Planner or other meal tools)
                if "recipes" in response:  # Adjust the key to whatever you use for storing recipes
                    current_recipe = response["recipes"]  # Store the list of recipes returned
                    print("🤖 ChatBot: I found multiple recipes for you. Please pick one by providing the Recipe ID or URL:")
                    
                    # Display the recipes to the user with IDs or URLs
                    for idx, recipe in enumerate(current_recipe):
                        print(f"{idx + 1}. {recipe['title']} (ID: {recipe['id']}, URL: {recipe['url']})")
                    
                # Check if the user indicates they like a recipe
                if current_recipe and detect_save_phrase(user_input):  # Detect phrases like "I like this"
                    print("🤖 ChatBot: Please provide the Recipe ID or URL of the recipe you like:")
                    
                    # Wait for user to input the recipe ID or URL
                    recipe_input = input("You: ")
                    
                    # Match the input (Recipe ID or URL) to find the correct recipe
                    liked_recipe = next((recipe for recipe in current_recipe if recipe['id'] == recipe_input or recipe['url'] == recipe_input), None)
                    
                    if liked_recipe:
                        # Store the liked recipe in the database
                        store_liked_recipe(user_id, liked_recipe)
                        print("✅ Recipe saved to your liked recipes!")
                    else:
                        print("⚠️ Couldn't find a recipe with that ID/URL. Please try again.")
            
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
        start_chat(email,user_id)
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
            break
        else:
            print("Invalid input. Try again.")
            
            


# In the part where you handle the user's message


if __name__ == "__main__":
    menu()
