import requests
from config import SPOONACULAR_API_KEY,EDAMAM_ID,EDAMAM_KEY
#TASTY_API_URL = "https://rapidapi.com/apidojo/api/tasty/"

import requests

# Constants
TASTY_API_URL = "https://tasty-api1.p.rapidapi.com/recipe/search"
RAPIDAPI_KEY = "973cfbb0ffmsh14789a1b91ec389p15f0e2jsn91b22b26d6ab"
RAPIDAPI_HOST = "tasty-api1.p.rapidapi.com"

def quick_meal_finder(query="chicken", page=1, per_page=5):
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    params = {
        "query": query,
        "page": str(page),
        "perPage": str(per_page)
    }

    response = requests.get(TASTY_API_URL, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json().get("data", [])
        if not data:
            print("No recipes found for the query.")
            return []

        # Format and return key info
        formatted = [
            {
                "title": item.get("title"),
                "cook_time": item.get("cookTime"),
                "image_url": item.get("thumbnail_url") or item.get("image_url"),
                "url": item.get("canonical_url") or f"https://tasty.co/recipe/{item.get('slug')}"
            }
            for item in data
        ]
        return formatted
    else:
        print("Tasty API Error:", response.status_code, response.text)
        return []
# === 1. Weekly Meal Planner using Spoonacular ===

def weekly_meal_planner(diet=None, cuisine=None, exclude_ingredients=None):
    url = "https://api.spoonacular.com/mealplanner/generate"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "timeFrame": "week",
        "diet": diet,
        "exclude": exclude_ingredients,
        "cuisine": cuisine
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["week"]
    else:
        print("Spoonacular Error:", response.text)
        return None



def fetch_from_tasty(query="chicken", max_time=20):
    # Tasty API parameters for recipe search
    params = {
        "query": query,
        "time": max_time,  # Assuming Tasty uses a "time" parameter, adjust as needed
        "limit": 5  # Limit to 5 recipes
    }
    
    # Send a GET request to the Tasty API with the search parameters
    response = requests.get(TASTY_API_URL, params=params)
    
    if response.status_code == 200:
        results = response.json()
        hits = results.get("results", [])
        
        # Check if any results were found
        if hits:
            # Format the results as needed (assumed structure based on typical APIs)
            formatted_results = [
                {
                    "title": hit["name"],
                    "image_url": hit["thumbnail_url"],
                    "prep_time": hit["total_time"],
                    "url": f"https://tasty.co/recipe/{hit['slug']}"
                }
                for hit in hits
            ]
            return formatted_results
        else:
            print("Tasty returned no results.")
            return []
    else:
        print("Tasty API Error:", response.text)
        return []

def quick_meal_finder(query="chicken", max_time=20):
    # Start by trying Tasty API directly (since you want it to fetch from Tasty)
    return fetch_from_tasty(query, max_time)

# === 3. Substitute Finder using Open Food Facts ===
def substitute_finder(ingredient="milk"):
    url = f"https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": ingredient,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 10
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        products = response.json().get("products", [])
        return [p["product_name"] for p in products if "product_name" in p]
    else:
        print("Open Food Facts Error:", response.text)
        return []


# === 4. Food + Health Explainer using Open Food Facts ===
def food_health_explainer(ingredient="sugar"):
    url = f"https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": ingredient,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        products = response.json().get("products", [])
        explain = []
        for p in products:
            name = p.get("product_name", "Unnamed")
            grade = p.get("nutriscore_grade", "unknown")
            warning = "⚠️ High in sugar or additives" if grade in ["d", "e"] else "✅ Looks healthy"
            explain.append(f"{name} → Nutriscore: {grade.upper()} | {warning}")
        return explain
    else:
        print("Open Food Facts Error:", response.text)
        return []
 
 
import requests

SPOONACULAR_API_KEY = "973cfbb0ffmsh14789a1b91ec389p15f0e2jsn91b22b26d6ab"
SPOONACULAR_HOST = "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"

def quick_meal_finder1(
    query="burger",
    diet=None,
    exclude_ingredients=None,
    intolerances=None,
    meal_type="main course",
    cuisine=None,
    number=5,
    offset=0
):
    url = f"https://{SPOONACULAR_HOST}/recipes/search"

    params = {
        "query": query,
        "number": number,
        "offset": offset,
        "type": meal_type,
    }
    
    # Optional filters
    if diet:
        params["diet"] = diet
    if exclude_ingredients:
        params["excludeIngredients"] = exclude_ingredients
    if intolerances:
        params["intolerances"] = intolerances
    if cuisine:
        params["cuisine"] = cuisine

    headers = {
        "x-rapidapi-key": SPOONACULAR_API_KEY,
        "x-rapidapi-host": SPOONACULAR_HOST
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        results = response.json().get("results", [])
        if not results:
            print("No recipes found.")
            return []

        # Format and return
        formatted = [
            {
                "title": recipe.get("title"),
                "ready_in_minutes": recipe.get("readyInMinutes"),
                "servings": recipe.get("servings"),
                "image_url": f"https://spoonacular.com/recipeImages/{recipe.get('image')}" if recipe.get("image") else None,
                "source_url": recipe.get("sourceUrl") or f"https://spoonacular.com/recipes/{recipe.get('title').replace(' ', '-').lower()}-{recipe.get('id')}"
            }
            for recipe in results
        ]
        return formatted
    else:
        print("Error:", response.status_code, response.text)
        return []
    
    
"""# Spoonacular weekly plan
week_plan = weekly_meal_planner(diet="vegetarian")
print("Weekly Meal Plan:", week_plan)

# Edamam quick meals
quick_meals = quick_meal_finder1("eggs", max_time=15)
print("Quick Meals:", [m['label'] for m in quick_meals])"""

"""# Open Food Facts substitutes
subs = substitute_finder("butter")
print("Substitutes for Butter:", subs)

# Ingredient Health Explanation
health_info = food_health_explainer("oil")
for line in health_info:
    print(line)"""
    
import requests

# Constants
SPOONACULAR_API_KEY = "973cfbb0ffmsh14789a1b91ec389p15f0e2jsn91b22b26d6ab"
SPOONACULAR_HOST = "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"

# Function to fetch quick meals
def quick_meal_finder2(
    query="burger",
    diet=None,
    exclude_ingredients=None,
    intolerances=None,
    meal_type="main course",
    cuisine=None,
    number=5,
    offset=0
):
    url = f"https://{SPOONACULAR_HOST}/recipes/search"

    params = {
        "query": query,
        "number": number,
        "offset": offset,
        "type": meal_type,
    }

    # Optional filters
    if diet:
        params["diet"] = diet
    if exclude_ingredients:
        params["excludeIngredients"] = exclude_ingredients
    if intolerances:
        params["intolerances"] = intolerances
    if cuisine:
        params["cuisine"] = cuisine

    headers = {
        "x-rapidapi-key": SPOONACULAR_API_KEY,
        "x-rapidapi-host": SPOONACULAR_HOST
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        results = response.json().get("results", [])
        if not results:
            print("No recipes found.")
            return []

        # Format and return
        formatted = [
            {
                "title": recipe.get("title"),
                "ready_in_minutes": recipe.get("readyInMinutes"),
                "servings": recipe.get("servings"),
                "image_url": f"https://spoonacular.com/recipeImages/{recipe.get('image')}" if recipe.get("image") else None,
                "source_url": recipe.get("sourceUrl") or f"https://spoonacular.com/recipes/{recipe.get('title').replace(' ', '-').lower()}-{recipe.get('id')}"
            }
            for recipe in results
        ]
        return formatted
    else:
        print("Error:", response.status_code, response.text)
        return []

# Test the function
if __name__ == "__main__":
    test_results = quick_meal_finder2(
        query="pasta",
        diet="vegetarian",
        exclude_ingredients="mushroom",
        intolerances="gluten",
        cuisine="italian",
        meal_type="main course",
        number=5
    )

    print("\n🧪 Test Results:\n")
    print(test_results)
    for r in test_results:
        
        print("🍽️", r["title"])
        print("⏱️ Ready in:", r["ready_in_minutes"], "mins")
        print("👥 Servings:", r["servings"])
        print("🖼️ Image URL:", r["image_url"])
        print("🔗 Recipe URL:", r["source_url"])
        print("-" * 50)


