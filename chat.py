from supabase import create_client
import os
from main import process_input,start_new_chat # Import the main function from main.py
from config import SUPABASE_KEY,SUPABASE_URL
from supabase_client import store_liked_recipe
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def start_chat(email,user_id):
    print("\n🤖 ChatBot: Hello! Ask me anything (type 'exit' to quit, 'menu' to go back, or 'new chat' to reset).\n")
    start_new_chat()
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
                # Call the main function to process user input and get response
                response = process_input(user_input, user_email=email,user_id=user_id)
                print(response)

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
