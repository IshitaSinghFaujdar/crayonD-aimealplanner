import time
import logging
from supabase_client import supabase
from auth import login, signup
from tools import quick_meal_finder, get_substitute_suggestions, get_meal_plan
from datetime import datetime

# Configure logging to file and console for debugging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(), logging.FileHandler("debug_log.txt", mode='w')])

# Replace these with your credentials for testing
email = "ishita85236@gmail.com"
password = "Ishita"

def test_login():
    try:
        logging.info("Attempting to login...")
        user_id = login(email, password)
        if user_id:
            logging.info(f"✅ Login successful. User ID: {user_id}")
            return user_id
        else:
            logging.error("❌ Login failed. Please check credentials or login function.")
            return None
    except Exception as e:
        logging.error(f"Error during login: {e}")
        return None

def test_tool(user_id):
    try:
        if user_id:
            logging.info("Testing tool: Get Substitute for Milk (diet reasons)...")
            response = get_substitute_suggestions("milk", "diet")
            logging.info(f"Bot Response: {response}")
        else:
            logging.warning("No user ID, skipping tool test.")
    except Exception as e:
        logging.error(f"Error during tool execution: {e}")

def test_weekly_meal_planner(user_id):
    try:
        if user_id:
            logging.info("Testing Weekly Meal Planner...")
            response = weekly_meal_planner(user_id, preferences={'time': '30 mins', 'diet': 'vegetarian'})
            logging.info(f"Weekly Meal Plan: {response}")
        else:
            logging.warning("No user ID, skipping weekly meal planner test.")
    except Exception as e:
        logging.error(f"Error during weekly meal planner: {e}")

def simulate_conversation():
    try:
        logging.info("Starting simulated conversation...")
        print("🤖 ChatBot: Hello! Ask me anything (type 'exit' to quit or 'menu' to manage chat).")
        
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                logging.info("User requested to exit.")
                print("❌ Exiting...")
                break
            elif user_input.lower() == "menu":
                print("🔧 Menu options: You can manage your chat here.")
            elif "substitute" in user_input.lower():
                logging.info(f"User asked for a substitute: {user_input}")
                print("\nBot: Fetching substitute suggestions...")
                response = get_substitute_suggestions("milk", "diet")
                logging.info(f"Bot Response: {response}")
                print("\nBot Response:", response)
            elif "meal plan" in user_input.lower():
                logging.info(f"User asked for a meal plan: {user_input}")
                response = weekly_meal_planner("user_id", preferences={'time': '30 mins', 'diet': 'vegetarian'})
                logging.info(f"Bot Response: {response}")
                print("\nBot Response:", response)
            else:
                logging.warning(f"User input unrecognized: {user_input}")
                print("🤖 Bot: Sorry, I didn't understand that.")
    except Exception as e:
        logging.error(f"Error during conversation simulation: {e}")

def main():
    logging.info("Starting the full application test...")
    
    # Step 1: User login
    user_id = test_login()
    
    # Step 2: Test tools with logged in user
    test_tool(user_id)
    
    # Step 3: Test weekly meal planner with logged in user
    test_weekly_meal_planner(user_id)

    # Step 4: Simulate conversation
    simulate_conversation()

    logging.info("Test completed.")

if __name__ == "__main__":
    main()
