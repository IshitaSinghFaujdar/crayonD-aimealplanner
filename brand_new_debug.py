from tools import humanize_response
import json, requests, asyncio, random
from main import user_context
user_context={'diet': ['low fat'], 'includeIngredients': ['milk', 'cheese']}
SPOONACULAR_API_KEY = "973cfbb0ffmsh14789a1b91ec389p15f0e2jsn91b22b26d6ab"
SPOONACULAR_HOST = "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
BASE_URL = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/"

# -------------------- QUICK MEAL FINDER --------------------
async def quick_meal_finder(user_context, user_input):
    quick_recipe = await fetch_quick_meals(user_context, user_input)
    if quick_recipe:
        return quick_recipe
    else:
        return {"error": "No quick recipe found for the given preferences."}

async def fetch_quick_meals(user_context, user_input):
    quick_meals = {}
    for meal_type in ["breakfast", "main course", "appetizer"]:
        preferences = build_meal_preferences(user_context, meal_type, user_input, number=5)
        quick_meals[meal_type] = await get_multiple_meals(preferences)
    return quick_meals

# -------------------- WEEKLY MEAL PLANNER --------------------

async def weekly_meal_planner(user_context, user_input):
    meals = {
        "breakfast": await get_multiple_meals(build_meal_preferences(user_context, "breakfast", user_input, number=7)),
        "main_course": await get_multiple_meals(build_meal_preferences(user_context, "main course", user_input, number=14)),
        "appetizer": await get_multiple_meals(build_meal_preferences(user_context, "appetizer", user_input, number=7)),
    }

    weekly_plan = {}
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(days):
        try:
            weekly_plan[day] = {
                "meals": [
                    meals["breakfast"][i] if i < len(meals["breakfast"]) else {"error": "No breakfast"},
                    meals["main_course"][2 * i] if 2 * i < len(meals["main_course"]) else {"error": "No main course 1"},
                    meals["main_course"][2 * i + 1] if 2 * i + 1 < len(meals["main_course"]) else {"error": "No main course 2"},
                    meals["appetizer"][i] if i < len(meals["appetizer"]) else {"error": "No appetizer"},
                ]
            }
        except Exception as e:
            weekly_plan[day]={"error": f"Meal assignment failed: {str(e)}"}

    return weekly_plan  # or await humanize_response(weekly_plan, user_input)

# -------------------- API WRAPPER --------------------

async def get_multiple_meals(meal_preferences):
    url = f"https://{SPOONACULAR_HOST}/recipes/complexSearch"
    headers = {
        "x-rapidapi-key": SPOONACULAR_API_KEY,
        "x-rapidapi-host": SPOONACULAR_HOST
    }

    response = await asyncio.to_thread(requests.get, url, headers=headers, params=meal_preferences)
    print("Response")
    print(response)
    print(response.json())  # DEBUG PRINT

    if response.status_code == 200:
        meal_data = response.json().get('results', [])
        formatted = []
        for meal in meal_data:
            formatted.append({
                "title": meal.get("title", "Unknown Recipe"),
                "readyInMinutes": meal.get("readyInMinutes", "-"),
                "source_url": f"https://spoonacular.com/recipes/{meal.get('title', '').replace(' ', '-').lower()}-{meal.get('id')}",
                "image_url": meal.get("image") if meal.get("image") else None,
            })
        return formatted
    else:
        print("API Error:", response.status_code, response.text)
        return [{"error": "Failed to fetch meal suggestions from Spoonacular API."}]

# -------------------- PREFERENCE BUILDER --------------------

def build_meal_preferences(user_context, meal_type, user_input=None, number=1):
    query = user_input if user_input else ""
    print(query)
    return {
        "query": query,
        "diet": ",".join(user_context.get("diet", [])),
        "cuisine": ",".join(user_context.get("cuisine", [])),
        "excludeIngredients": ",".join(user_context.get("exclude", [])),
        "intolerances": ",".join(user_context.get("intolerances", [])),
        "type": meal_type,
        "instructionsRequired": True,
        "addRecipeInformation": True,
        "number": number
    }

# -------------------- TESTING --------------------

if __name__ == "__main__":
    user_input = "Give me a vegetarian meal plan"
    print(user_input)
    response = asyncio.run(fetch_quick_meals(user_context, user_input)) 
    print(json.dumps(response, indent=2))

    user_input = "Give me a weekly meal plan"
    print(user_input)
    response = asyncio.run(weekly_meal_planner(user_context, user_input))
    print(json.dumps(response, indent=2))
