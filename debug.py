import uuid
import random
import requests
from sklearn.metrics.pairwise import cosine_similarity

# Mocking the PREFERENCE_LABELS to simulate your environment
PREFERENCE_LABELS = {
    "exclude": ["dairy", "gluten", "sugar", "nuts", "egg", "soy", "red meat", "seafood", "shellfish", "pork", "corn", "alcohol", "spicy", "caffeine", "mushrooms", "onions", "garlic"],
    "diet": ["vegan", "vegetarian", "pescatarian", "paleo", "keto", "low carb", "low fat", "high protein", "whole30", "flexitarian", "diabetic", "dash diet", "raw", "intermittent fasting", "mediterranean"],
    "goal": ["weight loss", "lose weight", "cutting", "slim down", "fat loss", "muscle gain", "bulk up", "maintenance", "improve energy", "balance hormones", "reduce inflammation", "detox"],
    "cuisine": ["indian", "north indian", "south indian", "italian", "mexican", "chinese", "thai", "japanese", "korean", "french", "greek", "mediterranean", "american", "middle eastern", "spanish", "lebanese"],
    "includeIngredients": ["chicken", "mutton", "beef", "paneer", "tofu", "lentils", "beans", "quinoa", "rice", "broccoli", "spinach", "cauliflower", "sweet potato", "avocado", "eggs", "milk", "cheese", "nuts", "seeds", "banana", "apple", "berries", "mango", "yogurt", "oats", "chia seeds"],
    "mealType": ["breakfast", "lunch", "dinner", "snack", "brunch", "dessert", "post workout", "pre workout", "light meal", "heavy meal"],
    "cookingStyle": ["grilled", "baked", "steamed", "fried", "raw", "sautéed", "pressure cooked", "slow cooked", "stir fried", "roasted", "air fried"],
    "allergy": ["gluten", "dairy", "egg", "soy", "nuts", "seafood", "shellfish", "sesame", "mustard", "sulfites", "lupin"],
    "spiceLevel": ["mild", "medium", "spicy", "extra spicy"],
    "budget": ["low budget", "affordable", "cheap meals", "moderate budget", "premium meals", "no budget limit"],
    "time": ["quick meals", "15 minutes", "30 minutes", "1 hour", "slow cooked", "instant", "overnight"],
    "appliance": ["oven", "air fryer", "instant pot", "pressure cooker", "stove top", "microwave", "blender", "no cook"]
}

# Sample embedding function (mock)
def get_embedding(text):
    # For this test, simply return a fixed value (a mock embedding)
    return [random.random() for _ in range(300)]

# Mock match_preferences function
def match_preferences(user_input: str) -> dict:
    print("\n--- Debugging match_preferences ---")
    user_embedding = get_embedding(user_input)
    preferences = {}
    
    for pref_type, values in PREFERENCE_LABELS.items():
        for value in values:
            sim = cosine_similarity([user_embedding], [get_embedding(value)])[0][0]
            if sim > 0.65:  # Adjust threshold if needed
                if pref_type not in preferences:
                    preferences[pref_type] = []
                preferences[pref_type].append(value)
    
    print(f"Preferences found: {preferences}")
    return preferences

# Debug process_input function
def process_input(user_input, user_email=None, user_id=None): 
    print("\n--- Debugging process_input ---")
    chat_history = []
    user_context = {}
    
    # Handle new chat command
    if user_input.lower() == "new chat":
        print("Starting a new chat session.")
        new_id = str(uuid.uuid4())
        return f"✨ Started a new chat session: {new_id[:8]}..."
    
    # Set chat_id if not already set
    if "chat_id" not in user_context:
        user_context["chat_id"] = str(uuid.uuid4())
    
    chat_id = user_context["chat_id"]
    chat_history.append(f"User: {user_input}")
    context_window = " ".join(chat_history[-10:])
    
    print(f"Context Window: {context_window}")
    
    prefs = match_preferences(context_window)
    
    print(f"Preferences from match_preferences: {prefs}")
    if not isinstance(prefs, dict):
        print("ERROR: prefs is not a dictionary!")
    
    # Save extracted preferences
    if user_id:
        print(f"Saving preferences for user: {user_id}")
        # save_user_preferences(user_id, prefs)  # Simulate saving

    for k, v in prefs.items():
        if not v:
            continue
        if k not in user_context:
            user_context[k] = v
        elif isinstance(v, list):
            user_context[k] = list(set(user_context[k] + v))
        else:
            user_context[k] = v

    print(f"User context after processing preferences: {user_context}")
    response = "✅ Preferences processed successfully."
    
    return response

# Main function to test the flow
def main():
    # Test case
    user_input = "I want vegan and gluten-free meals for weight loss"
    
    # Test the flow with sample user input
    response = process_input(user_input)
    print(f"Response: {response}")

if __name__ == "__main__":
    main()
