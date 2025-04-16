import requests
import urllib.parse
from tools import humanize_response
import asyncio
from config import SERPER_URL as BASE_URL
from config import SERPER_KEY as API_KEY

# Function to build the search query
def build_search_query(user_context, user_input):
    # Start with user input (e.g., "vegetarian meal plan")
    query = user_input
    
    # Add user context to refine search (e.g., "low fat", "milk", "cheese")
    if user_context.get("diet"):
        query += " " + " ".join(user_context["diet"])
    if user_context.get("includeIngredients"):
        query += " " + " ".join(user_context["includeIngredients"])

    # URL encode the query to make it safe for the API request
    return urllib.parse.quote(query)

# Function to search for recipes using the Serper API
def search_recipes(user_context, user_input):
    # Build the search query
    search_query = build_search_query(user_context, user_input)
    
    # Construct the full URL with the search query
    url = f"{BASE_URL}?q={search_query}&apiKey={API_KEY}"
    
    # Send the GET request
    response = requests.get(url)
    
    # Check the status code and handle response
    if response.status_code == 200:
        # Parse and return the response data (e.g., recipes)
        return humanize_response(response.json(),user_input)
    else:
        # If there’s an error, return the status code and message
        return {"error": f"Failed to fetch recipes. Status code: {response.status_code}"}

