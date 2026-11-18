import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    # Base paths
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    STYLE_PROFILE_PATH = DATA_DIR / "style_profile.json"
    CONVERSATION_HISTORY_PATH = DATA_DIR / "chat_history.db"

    # AI Model Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    # Default to current generation fast model
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Meta Graph API / Instagram Settings
    INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    INSTAGRAM_VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN", "my_secret_verify_token")
    INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v21.0")

    # Reply Automation Behavior
    # 'co-pilot': drafts replies and requires manual confirmation or logs drafts
    # 'autonomous': immediately sends replies matching style
    REPLY_MODE = os.getenv("REPLY_MODE", "co-pilot").lower()

    # Human-like delay simulation (seconds)
    MIN_DELAY_SECONDS = int(os.getenv("MIN_DELAY_SECONDS", "3"))
    MAX_DELAY_SECONDS = int(os.getenv("MAX_DELAY_SECONDS", "8"))

    # Sensitive topics that automatically trigger manual review instead of auto-sending
    SENSITIVE_TOPICS = [
        "money", "pay", "bank", "credit card", "password", "otp", "code",
        "ssn", "address", "meet up", "where are you", "contract", "legal",
        "emergency", "urgent", "call me", "whatsapp"
    ]

    # Webhook server settings
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# Ensure directories exist
Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
Config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
