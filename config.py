import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
EDAMAM_ID=os.getenv("EDAMAM_ID")
EDAMAM_KEY=os.getenv("EDAMAM_KEY")
SERPER_URL=os.getenv("SERPER_URL")
SERPER_KEY=os.getenv("SERPER_KEY")
