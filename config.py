"""
Configuration — GitHub Actions secrets auto-override via env vars.
"""

import os
import sys

# ─── Telegram ───────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not set!")
    sys.exit(1)
if not TELEGRAM_CHAT_ID:
    print("❌ TELEGRAM_CHAT_ID not set!")
    sys.exit(1)

# ─── Gemini AI ──────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
ENABLE_GEMINI = os.getenv("ENABLE_GEMINI", "true").lower() == "true"
MAX_GEMINI_ARTICLES = int(os.getenv("MAX_GEMINI_ARTICLES", "25"))  # Cost control

if ENABLE_GEMINI and not GEMINI_API_KEY:
    print("⚠️  GEMINI_API_KEY not set. Falling back to keyword classification.")

# ─── Sources ────────────────────────────────────────────────────────
SOURCES = {
    "GKToday": {
        "url": "https://www.gktoday.in/current-affairs/",
        "max_articles": 15,
        "language": "en",
        "type": "gktoday"
    },
    "The Hindu": {
        "url": "https://www.thehindu.com/",
        "max_articles": 10,
        "language": "en",
        "type": "newspaper"
    },
    "Indian Express": {
        "url": "https://indianexpress.com/",
        "max_articles": 10,
        "language": "en",
        "type": "newspaper"
    },
    "Lokmat": {
        "url": "https://www.lokmat.com/",
        "max_articles": 6,
        "language": "mr",
        "type": "newspaper"
    },
    "Loksatta": {
        "url": "https://www.loksatta.com/",
        "max_articles": 6,
        "language": "mr",
        "type": "newspaper"
    },
    "eSakal": {
        "url": "https://www.esakal.com/",
        "max_articles": 6,
        "language": "mr",
        "type": "newspaper"
    }
}

# ─── PDF Settings ───────────────────────────────────────────────────
HTML_OUTPUT_PATH = os.getenv("HTML_OUTPUT_PATH", "daily_exam_notes.html")
NOTES_TITLE = os.getenv("NOTES_TITLE", "UPSC Daily Exam Notes")
