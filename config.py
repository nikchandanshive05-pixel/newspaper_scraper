"""
Configuration - GitHub Actions secrets auto-override via env vars.
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

# ─── Sources ────────────────────────────────────────────────────────
SOURCES = {
    "The Hindu": {
        "url": "https://www.thehindu.com/",
        "max_articles": 15,
        "language": "en"
    },
    "Indian Express": {
        "url": "https://indianexpress.com/",
        "max_articles": 15,
        "language": "en"
    },
    "Lokmat": {
        "url": "https://www.lokmat.com/",
        "max_articles": 10,
        "language": "mr"
    },
    "Loksatta": {
        "url": "https://www.loksatta.com/",
        "max_articles": 10,
        "language": "mr"
    },
    "eSakal": {
        "url": "https://www.esakal.com/",
        "max_articles": 10,
        "language": "mr"
    }
}

# ─── Exam-Relevant Topic Keywords ───────────────────────────────────
# Articles are scored and categorized based on these keywords
TOPIC_CATEGORIES = {
    "🏛️ Polity & Governance": [
        "parliament", "constitution", "amendment", "bill", "act", "supreme court",
        "high court", "election", "commission", "governor", "president", "cabinet",
        "ministry", "policy", "governance", "judicial", "legislation", " ordinance",
        "delimitation", "federalism", "local government", "panchayat", "municipal",
        "anti-defection", "schedule", "article", "fundamental right", "directive principle"
    ],
    "💰 Economy & Finance": [
        "gdp", "inflation", "rbi", "reserve bank", "monetary policy", "fiscal",
        "budget", "tax", "gst", "trade", "export", "import", "fdi", "fii",
        "stock market", "sensex", "nifty", "banking", "insurance", "sebi",
        "imf", "world bank", "wto", "trade agreement", "tariff", "subsidy",
        "msme", "startup", "digital payment", "upi", "cryptocurrency", "rupee"
    ],
    "🌍 International Relations": [
        "bilateral", "multilateral", "summit", "g20", "g7", "brics", "saarc",
        "un", "unsc", "nato", "asean", "eu", "wto", "imf", "world bank",
        "treaty", "agreement", "moU", "diplomatic", "embassy", "consulate",
        "border dispute", "cross-border", "foreign policy", "defence deal",
        "india-china", "india-us", "india-russia", "india-israel", "pakistan",
        "afghanistan", "myanmar", "bangladesh", "nepal", "sri lanka", "maldives"
    ],
    "🛡️ Defence & Security": [
        "defence", "military", "army", "navy", "air force", "coast guard",
        "paramilitary", "crpf", "bsf", "itbp", "ssb", "assam rifles",
        "missile", "drdo", "isro", "space", "satellite", "nuclear",
        "terrorism", "naxal", "maoist", "insurgency", "cyber security",
        "border security", "coastal security", "internal security", "intelligence"
    ],
    "🔬 Science & Technology": [
        "isro", "space mission", "rocket", "satellite", "mars", "moon",
        "gaganyaan", "chandrayaan", "agnikul", "skyroot", "drdo", "defence research",
        "ai", "artificial intelligence", "machine learning", "quantum",
        "biotechnology", "genome", "crispr", "vaccine", "drug", "clinical trial",
        "renewable energy", "solar", "wind", "hydrogen", "electric vehicle",
        "semiconductor", "chip", "5g", "6g", "telecom", "digital india"
    ],
    "🌿 Environment & Ecology": [
        "climate change", "global warming", "cop", "paris agreement",
        "biodiversity", "species", "endangered", "extinction", "wildlife",
        "tiger", "elephant", "lion", "rhino", "turtle", "coral",
        "forest", "deforestation", "afforestation", "wetland", "ramsar",
        "pollution", "air quality", "water quality", "waste management",
        "renewable", "sustainable", "green energy", "carbon", "net zero",
        "national park", "sanctuary", "biosphere", "tiger reserve"
    ],
    "👥 Social Issues": [
        "education", "health", "healthcare", "hospital", "doctor", "nurse",
        "poverty", "inequality", "caste", "tribe", "scheduled caste", "scheduled tribe",
        "women empowerment", "gender", "child rights", "juvenile",
        "labour", "worker", "migrant", "unemployment", "job",
        "nutrition", "mid-day meal", "anganwadi", "pension",
        "scheme", "yojana", "mission", "programme", "welfare"
    ],
    "📜 History & Culture": [
        "archaeological", "excavation", "heritage", "monument", "temple",
        "museum", "artifact", "manuscript", "inscription", "rock art",
        "festival", "dance", "music", "art form", "craft", "handloom",
        "unesco", "world heritage", "gi tag", "cultural", "civilization",
        "freedom struggle", "independence", "gandhi", "nehru", "patel"
    ],
    "⚖️ Law & Judiciary": [
        "supreme court", "high court", "judgment", "verdict", "petition",
        " PIL ", "constitutional", "fundamental right", "article ", "section ",
        "ipc", "crpc", "bns", "bnss", "bharatiya nyaya", "criminal law",
        "ed", "cbi", "nIA", "enforcement directorate", "investigation",
        "bail", "conviction", "acquittal", "sentencing", "death penalty"
    ],
    "🏗️ Infrastructure": [
        "highway", "expressway", "railway", "metro", "bullet train",
        "airport", "port", "shipping", "inland waterway", "logistics",
        "smart city", "urban", "rural", "village", "connectivity",
        "bridge", "tunnel", "dam", "canal", "irrigation",
        "power plant", "renewable energy", "grid", "transmission"
    ]
}

# Minimum score for an article to be included (out of 10)
MIN_RELEVANCE_SCORE = 2

# ─── PDF Settings ───────────────────────────────────────────────────
PDF_OUTPUT_PATH = os.getenv("PDF_OUTPUT_PATH", "daily_newspaper.pdf")
PDF_TITLE = os.getenv("PDF_TITLE", "Daily Exam News Digest")
