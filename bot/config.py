import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://audrianna-overbrave-presumingly.ngrok-free.dev/")