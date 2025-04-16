from google import genai
from google.genai import types
from fastapi import FastAPI
import numpy as np
import os
from typing import List, Tuple
from fastapi.concurrency import run_in_threadpool
client= genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))  # Set env var
import json,asyncio

STATIC_EMBEDDINGS_FILE = "label_embeddings.json"

# Predefined preference labels and matching phrases
PREFERENCE_LABELS = {
    "exclude": [
        "dairy", "gluten", "sugar", "nuts", "egg", "soy", "red meat", "seafood",
        "shellfish", "pork", "corn", "alcohol", "spicy", "caffeine", "mushrooms", "onions", "garlic"
    ],
    "diet": [
        "vegan", "vegetarian", "pescatarian", "paleo", "keto", "low carb", "low fat", 
        "high protein", "whole30", "flexitarian", "diabetic", "dash diet", "raw", 
        "intermittent fasting", "mediterranean"
    ],
    "goal": [
        "weight loss", "lose weight", "cutting", "slim down", "fat loss", 
        "muscle gain", "bulk up", "maintenance", "improve energy", 
        "balance hormones", "reduce inflammation", "detox"
    ],
    "cuisine": [
        "indian", "north indian", "south indian", "italian", "mexican", 
        "chinese", "thai", "japanese", "korean", "french", "greek", 
        "mediterranean", "american", "middle eastern", "spanish", "lebanese"
    ],
    "includeIngredients": [
        "chicken", "mutton", "beef", "carrot","pork", "turkey", "duck", "salmon", "tuna", "shrimp", "crab", "lobster","capsicum"
        "paneer", "tofu", "tempeh", "seitan", "lentils", "black beans", "kidney beans", "chickpeas", "soybeans",
        "quinoa", "rice", "brown rice", "basmati rice", "jasmine rice", "wild rice", "barley", "millet", "bulgur",
        "oats", "steel-cut oats", "rolled oats", "chia seeds", "flax seeds", "hemp seeds", "pumpkin seeds", "sunflower seeds",
        "bread", "whole wheat bread", "sourdough", "naan", "pita", "tortilla", "pasta", "whole wheat pasta", "noodles", "ramen",
        "broccoli", "spinach", "kale", "collard greens", "swiss chard", "lettuce", "romaine", "arugula", "bok choy", "cabbage",
        "carrots", "potatoes", "sweet potatoes", "yams", "parsnips", "turnips", "radish", "beets", "onions", "red onions", 
        "shallots", "scallions", "leeks", "garlic", "ginger", "bell peppers", "red bell pepper", "green bell pepper", 
        "yellow bell pepper", "jalapeños", "chili peppers", "zucchini", "eggplant", "cucumber", "tomatoes", "cherry tomatoes",
        "avocado", "corn", "peas", "green beans", "snow peas", "asparagus", "brussels sprouts", "cauliflower", "mushrooms",
        "portobello mushrooms", "shiitake mushrooms", "button mushrooms", "okra", "artichokes", "fennel", "celery", "pumpkin",
        "squash", "butternut squash", "acorn squash", "spaghetti squash",
        "banana", "apple", "orange", "mandarin", "grapefruit", "pear", "plum", "peach", "nectarine", "mango",
        "papaya", "pineapple", "kiwi", "dragon fruit", "lychee", "passionfruit", "blueberries", "strawberries",
        "raspberries", "blackberries", "cranberries", "watermelon", "cantaloupe", "honeydew", "grapes", "cherries", "figs",
        "dates", "raisins", "apricots", "pomegranate",
        "yogurt", "greek yogurt", "milk", "almond milk", "soy milk", "oat milk", "coconut milk", "buttermilk", 
        "cheese", "mozzarella", "cheddar", "feta", "parmesan", "cream cheese", "ricotta", "paneer",
        "butter", "ghee", "olive oil", "vegetable oil", "canola oil", "coconut oil", "avocado oil",
        "eggs", "egg whites", "mayonnaise", "ketchup", "mustard", "soy sauce", "tamari", "vinegar", 
        "apple cider vinegar", "balsamic vinegar", "white vinegar", "rice vinegar",
        "salt", "pepper", "black pepper", "white pepper", "cinnamon", "nutmeg", "clove", "cardamom",
        "turmeric", "cumin", "coriander", "paprika", "smoked paprika", "chili powder", "red pepper flakes",
        "oregano", "basil", "thyme", "rosemary", "parsley", "cilantro", "mint", "dill", "bay leaf",
        "sugar", "brown sugar", "honey", "maple syrup", "molasses", "agave nectar",
        "nuts", "almonds", "walnuts", "cashews", "pecans", "macadamia nuts", "hazelnuts", "pistachios",
        "cocoa powder", "dark chocolate", "white chocolate", "chocolate chips",
        "flour", "whole wheat flour", "all-purpose flour", "almond flour", "coconut flour", "cornmeal",
        "baking powder", "baking soda", "yeast", "cornstarch", "gelatin",
        "stock", "vegetable broth", "chicken broth", "beef broth", "miso paste", "fish sauce",
        "sriracha", "hot sauce", "tahini", "peanut butter", "almond butter", "jam", "jelly", "pickles", "sauerkraut",
        "seaweed", "nori", "kimchi", "tofu skin", "tempeh", "edamame", "wasabi",
        "lemongrass", "galangal", "tamarind", "coconut", "coconut cream", "plantains", "jackfruit", "breadfruit"
    ],

    "mealType": [
        "breakfast", "lunch", "dinner", "snack", "brunch", "dessert", 
        "post workout", "pre workout", "light meal", "heavy meal"
    ],
    "cookingStyle": [
        "grilled", "baked", "steamed", "fried", "raw", "sautéed", 
        "pressure cooked", "slow cooked", "stir fried", "roasted", "air fried"
    ],
    "allergy": [
        "gluten", "dairy", "egg", "soy", "nuts", "seafood", "shellfish", 
        "sesame", "mustard", "sulfites", "lupin"
    ],
    "spiceLevel": [
        "mild", "medium", "spicy", "extra spicy"
    ],
    "budget": [
        "low budget", "affordable", "cheap meals", "moderate budget", 
        "premium meals", "no budget limit"
    ],
    "time": [
        "quick meals", "15 minutes", "30 minutes", "1 hour", 
        "slow cooked", "instant", "overnight"
    ],
    "appliance": [
        "oven", "air fryer", "instant pot", "pressure cooker", "stove top", 
        "microwave", "blender", "no cook"
    ]
}

def get_batch_embeddings(texts: List[str]) -> List[List[float]]:
    response = client.models.embed_content(
        model="models/embedding-001",
        contents=texts,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
    )
    return [e.values for e in response.embeddings]
async def get_batch_embeddings_async(texts: List[str]) -> List[List[float]]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: get_batch_embeddings(texts))

# Precompute only once and save to file
def cache_label_embeddings():
    if not os.path.exists(STATIC_EMBEDDINGS_FILE):
        print("Generating static label embeddings...")
        embeddings = {}
        for pref_type, values in PREFERENCE_LABELS.items():
            batch_embeddings = get_batch_embeddings(values)
            embeddings[pref_type] = dict(zip(values, batch_embeddings))
        with open(STATIC_EMBEDDINGS_FILE, "w") as f:
            json.dump(embeddings, f)
        print("Embeddings cached.")
    else:
        print("Embeddings already cached.")
# Load from cache only after ensuring it's generated


def load_label_embeddings():
    """Safely load the label embeddings from the cache."""
    if not os.path.exists(STATIC_EMBEDDINGS_FILE):
        raise FileNotFoundError(f"{STATIC_EMBEDDINGS_FILE} does not exist. Please run cache_label_embeddings() first.")
    with open(STATIC_EMBEDDINGS_FILE, "r") as f:
        return json.load(f)

# Call the cache function to ensure it's cached
cache_label_embeddings()

# Now, safely load the embeddings after cache
LABEL_EMBEDDINGS = load_label_embeddings()

def get_embedding(text):
    """Get the embedding for a single text."""
    return get_batch_embeddings([text])[0]

def cosine_similarity(vec1, vec2) -> float:
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def match_preferences(user_input: str) -> dict:
    user_embedding = get_embedding(user_input)
    SIMILARITY_THRESHOLD = 0.75
    #print("user embeddings")
    #print(user_embedding)
    preferences = {}
    for pref_type, val_embeds in LABEL_EMBEDDINGS.items():
        for value, embedding in val_embeds.items():
            sim = cosine_similarity(user_embedding, embedding)
            if sim > SIMILARITY_THRESHOLD :
                preferences.setdefault(pref_type, []).append(value)
    return preferences
