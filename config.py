"""
Configuration file for Newspaper Scraper Bot.
Fill in your Telegram Bot Token and Chat ID.
"""

import os

# ─── Telegram Settings ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

# ─── Newspaper Sources ──────────────────────────────────────────────
# You can customize the number of articles per source
NEWSPAPER_CONFIG = {
    "The Hindu": {
        "url": "https://www.thehindu.com/",
        "max_articles": 5,
        "language": "en"
    },
    "Indian Express": {
        "url": "https://indianexpress.com/",
        "max_articles": 5,
        "language": "en"
    },
    "Lokmat": {
        "url": "https://www.lokmat.com/",
        "max_articles": 5,
        "language": "mr"  # Marathi
    },
    "Loksatta": {
        "url": "https://www.loksatta.com/",
        "max_articles": 5,
        "language": "mr"  # Marathi
    },
    "eSakal": {
        "url": "https://www.esakal.com/",
        "max_articles": 5,
        "language": "mr"  # Marathi
    }
}

# ─── PDF Settings ───────────────────────────────────────────────────
PDF_OUTPUT_PATH = "daily_newspaper.pdf"
PDF_TITLE = "Daily Newspaper Digest"
MAX_ARTICLES_PER_SOURCE = 5

