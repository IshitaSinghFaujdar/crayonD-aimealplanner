from tools import humanize_response
import json,requests,asyncio,random
from main import user_context
SPOONACULAR_API_KEY = "973cfbb0ffmsh14789a1b91ec389p15f0e2jsn91b22b26d6ab"
SPOONACULAR_HOST = "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
BASE_URL="https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/"
user_context={'diet': ['low fat'], 'includeIngredients': ['milk', 'cheese']}
async def quick_meal_finder(user_context, user_input):
    quick_recipe = await fetch_quick_meals(user_context, user_input)
    if quick_recipe:
        return quick_recipe
    else:
        return {"error": "No quick recipe found for the given preferences."}
#TOOL 2
async def fetch_quick_meals(user_context, user_input):
    meal_preferences = build_meal_preferences(user_context, "main course", user_input)
    meal = await get_meal_for_day(meal_preferences)
    #return await humanize_response(meal, user_input)
    return "successfully implemented"


#THIS IS ACTUAL ONE WHICH GETS CALLED FROM MAIN.PY(TOOL 1)
async def weekly_meal_planner(user_context, user_input):
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    meals_for_the_week = {}
    tasks = [get_daily_meal_plan_for_day(user_context, day) for day in days_of_week]
    daily_meals = await asyncio.gather(*tasks)
    for day, meals in zip(days_of_week, daily_meals):
        meals_for_the_week[day] = {"meals": meals}

    # Pass the weekly meal plan to Gemini for humanization
    #return await humanize_response(meals_for_the_week, user_input)
    return "successfully implemented"
#THIS FUNCTION RUNS X no. OF MEALS PER DAY
async def get_daily_meal_plan_for_day(user_context, day):
    daily_meals = []
    for meal_type in ["breakfast", "main course", "main course", "appetizer"]:
        meal_preferences = build_meal_preferences(user_context, meal_type)
        daily_meals.append(await get_meal_for_day(meal_preferences))
    return daily_meals

#ACTUAAL API CALL HAPPENS HERE BUT 1 TIME
async def get_meal_for_day(meal_preferences):
    url = f"https://{SPOONACULAR_HOST}/recipes/search"
    headers = {
        "x-rapidapi-key": SPOONACULAR_API_KEY,
        "x-rapidapi-host": SPOONACULAR_HOST
    }
    response = await asyncio.to_thread(requests.get,url, headers=headers, params=meal_preferences)
    print("Response")
    print(response)
    if response.status_code == 200:
        print(response.json())
        meal_data = response.json().get('results', [])

        if not meal_data:
            return {"error": "No meals found from Spoonacular API."}

        print(meal_data)
        meal=meal_data[0]
        formatted_recipe = {
            "title": meal.get("title", "Unknown Recipe"),
            "readyInMinutes": meal.get("readyInMinutes", "-"),
            "source_url": meal.get("sourceUrl") or f"https://spoonacular.com/recipes/{meal_data.get('title').replace(' ', '-').lower()}-{meal_data.get('id')}",
            "image_url": f"https://spoonacular.com/recipeImages/{meal_data.get('image')}" if meal_data.get("image") else None,
        }
    
        
        return formatted_recipe
    else:
        print("ELSE BLOCK")
        return {"error": "Failed to fetch meal suggestions from Spoonacular API."}


def build_meal_preferences(user_context, meal_type,user_input=None):
    query = user_input if user_input else ""
    return {
        "query": query,
        "diet": ",".join(user_context.get("diet", [])),
        "cuisine": ",".join(user_context.get("cuisine", [])),
        "excludeIngredients": ",".join(user_context.get("exclude", [])),
        "type": meal_type,
        "instructionsRequired": True,
        "number": 1,
        "apiKey": SPOONACULAR_API_KEY
    }


user_input="Give me a vegetarian meal plan"
print(user_input)
response= asyncio.run(fetch_quick_meals(user_context,user_input)) 
print(response)
user_input="Give me a weekly meal plan"
print(user_input)
response=asyncio.run(weekly_meal_planner(user_context,user_input))
print(response)