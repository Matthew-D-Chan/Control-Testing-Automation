import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()  # Loads .env file (lets us use whatever is in /env)

# Grabs the url and key from .env safely
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]

# Feeds our specific url and key to the supabase client to establish connection to our database 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)