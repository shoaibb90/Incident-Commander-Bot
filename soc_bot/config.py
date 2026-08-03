import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
DB_PATH = os.getenv("DB_PATH", "soc_commander.db")

# Roles, ranked by privilege level (higher = more access)
ROLE_LEVELS = {
    "pending": 0,
    "viewer": 1,
    "analyst": 2,
    "admin": 3,
}

SEVERITY_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
    "critical": "🔴",
}

STATUS_EMOJI = {
    "new": "🆕",
    "investigating": "🔎",
    "resolved": "✅",
}
