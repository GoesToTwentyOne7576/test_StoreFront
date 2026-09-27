"""
Centralized config. Reads everything from environment variables (.env file
loaded via python-dotenv). Kept in one tiny file on purpose -- this is a PoC.
"""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Gemini model names (swap freely -- flash is cheap/fast, good for a PoC)
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.0-flash")
GEMINI_VISION_MODEL = os.getenv("GEMINI_VISION_MODEL", "gemini-2.0-flash")

# How many venue candidates to try before giving up on Step 4's fallback loop
MAX_CANDIDATES_TO_TRY = int(os.getenv("MAX_CANDIDATES_TO_TRY", "5"))

PLANTER_ASSET_PATH = os.path.join(
    os.path.dirname(__file__), "assets", "planter.png"
)

if not GEMINI_API_KEY:
    print("[config] WARNING: GEMINI_API_KEY is not set (put it in backend/.env)")
if not GOOGLE_MAPS_API_KEY:
    print("[config] WARNING: GOOGLE_MAPS_API_KEY is not set (put it in backend/.env)")
