"""
Strict Exam News Scraper - Filters out garbage aggressively.
"""

import newspaper
from newspaper import Article, Config
import time
import random
import re
from typing import Dict, List
from collections import defaultdict
from datetime import datetime, timedelta


class AIExamNewsScraper:
    """
    Strict scraper with aggressive filtering for exam-relevant news only.
    """

    TOPIC_DEFINITIONS = {
        "🏛️ Polity & Governance": [
            ("parliament", 3), ("constitution", 3), ("amendment", 3), ("bill", 2), ("act", 2),
            ("supreme court", 3), ("high court", 2), ("election", 2), ("commission", 2),
            ("governor", 2), ("president", 2), ("cabinet", 2), ("ministry", 2), ("policy", 2),
            ("governance", 2), ("judicial", 2), ("legislation", 2), ("ordinance", 2),
            ("delimitation", 3), ("federalism", 2), ("panchayat", 2), ("municipal", 1),
            ("anti-defection", 2), ("fundamental right", 2), ("directive principle", 2),
            ("lok sabha", 2), ("rajya sabha", 2), ("mp", 1), ("mla", 1),
            ("bjp", 1), ("congress", 1), ("modi", 1), ("rahul gandhi", 1),
            ("opposition", 1), ("government", 1), ("cabinet", 2)
        ],
        "💰 Economy & Finance": [
            ("gdp", 3), ("inflation", 3), ("rbi", 3), ("reserve bank", 3), ("monetary policy", 3),
            ("fiscal", 2), ("budget", 3), ("tax", 2), ("gst", 3), ("trade", 2),
            ("export", 2), ("import", 2), ("fdi", 2), ("fii", 2), ("stock market", 2),
            ("sensex", 2), ("nifty", 2), ("banking", 2), ("insurance", 2), ("sebi", 2),
            ("imf", 2), ("world bank", 2), ("wto", 2), ("tariff", 2), ("subsidy", 2),
            ("msme", 2), ("startup", 2), ("digital payment", 2), ("upi", 2),
            ("cryptocurrency", 2), ("rupee", 2), ("fiscal deficit", 3), ("repo rate", 3),
            ("interest rate", 2), ("forex", 2), ("foreign exchange", 2)
        ],
        "🌍 International Relations": [
            ("bilateral", 2), ("multilateral", 2), ("summit", 2), ("g20", 3), ("g7", 2),
            ("brics", 3), ("saarc", 2), ("un", 2), ("unsc", 3), ("nato", 2),
            ("asean", 2), ("eu", 2), ("treaty", 2), ("agreement", 2), ("mou", 2),
            ("diplomatic", 2), ("embassy", 2), ("border dispute", 3), ("foreign policy", 2),
            ("defence deal", 2), ("india-china", 3), ("india-us", 2), ("india-russia", 2),
            ("pakistan", 2), ("afghanistan", 2), ("myanmar", 2), ("bangladesh", 2),
            ("nepal", 2), ("sri lanka", 2), ("maldives", 2), ("israel", 2),
            ("iran", 2), ("china", 1), ("america", 1), ("biden", 1), ("putin", 1)
        ],
        "🛡️ Defence & Security": [
            ("defence", 2), ("military", 2), ("army", 2), ("navy", 2), ("air force", 2),
            ("coast guard", 2), ("paramilitary", 2), ("crpf", 2), ("bsf", 2), ("itbp", 2),
            ("missile", 3), ("drdo", 3), ("isro", 3), ("space mission", 3), ("satellite", 2),
            ("nuclear", 2), ("terrorism", 2), ("naxal", 2), ("maoist", 2), ("insurgency", 2),
            ("cyber security", 3), ("border security", 2), ("internal security", 2),
            ("intelligence", 2), ("raw", 2), ("ib", 2), ("agniveer", 2), ("tejas", 2),
            ("agni", 2), ("prithvi", 2), ("akash", 2), ("brahmos", 2),
            ("gaganyaan", 3), ("chandrayaan", 3), ("rocket", 2), ("launch", 2)
        ],
        "🔬 Science & Technology": [
            ("isro", 3), ("space mission", 3), ("rocket", 2), ("satellite", 2), ("mars", 2),
            ("moon", 2), ("gaganyaan", 3), ("chandrayaan", 3), ("agnikul", 2), ("skyroot", 2),
            ("drdo", 2), ("ai", 2), ("artificial intelligence", 3), ("machine learning", 2),
            ("quantum", 2), ("biotechnology", 2), ("genome", 2), ("vaccine", 2),
            ("renewable energy", 2), ("solar", 2), ("hydrogen", 2),
            ("electric vehicle", 2), ("semiconductor", 3), ("chip", 2), ("5g", 2), ("6g", 2),
            ("telecom", 2), ("digital india", 2), ("innovation", 1),
            ("research", 1), ("scientist", 1), ("discovery", 1)
        ],
        "🌿 Environment & Ecology": [
            ("climate change", 3), ("global warming", 3), ("cop", 2), ("paris agreement", 3),
            ("biodiversity", 2), ("species", 1), ("endangered", 2), ("extinction", 2),
            ("wildlife", 2), ("tiger", 2), ("elephant", 2), ("lion", 2), ("rhino", 2),
            ("forest", 2), ("deforestation", 2), ("afforestation", 2), ("wetland", 2),
            ("ramsar", 3), ("pollution", 2), ("air quality", 2), ("water quality", 2),
            ("waste management", 2), ("renewable", 2), ("sustainable", 2), ("green energy", 2),
            ("carbon", 2), ("net zero", 3), ("national park", 2), ("sanctuary", 2),
            ("biosphere", 2), ("tiger reserve", 2), ("coral", 1), ("glacier", 2),
            ("cyclone", 2), ("flood", 2), ("drought", 2), ("earthquake", 2)
        ],
        "👥 Social Issues": [
            ("education", 2), ("health", 2), ("healthcare", 2), ("hospital", 1),
            ("poverty", 2), ("inequality", 2), ("caste", 2), ("tribe", 2),
            ("scheduled caste", 3), ("scheduled tribe", 3), ("women empowerment", 3),
            ("gender", 2), ("child rights", 2), ("juvenile", 2), ("labour", 2),
            ("migrant", 2), ("unemployment", 2), ("job", 1),
            ("nutrition", 2), ("mid-day meal", 2), ("anganwadi", 2), ("pension", 2),
            ("scheme", 2), ("yojana", 3), ("mission", 2), ("programme", 2), ("welfare", 2),
            ("neet", 2), ("upsc", 2), ("ssc", 2), ("exam", 1), ("paper leak", 2)
        ],
        "📜 History & Culture": [
            ("archaeological", 2), ("excavation", 2), ("heritage", 2), ("monument", 2),
            ("museum", 2), ("artifact", 2), ("manuscript", 2), ("inscription", 2),
            ("festival", 1), ("art form", 2), ("handloom", 2), ("unesco", 3),
            ("world heritage", 3), ("gi tag", 3), ("cultural", 1), ("civilization", 2),
            ("freedom struggle", 3), ("independence", 2), ("gandhi", 1), ("nehru", 1)
        ],
        "⚖️ Law & Judiciary": [
            ("supreme court", 3), ("high court", 2), ("judgment", 2), ("verdict", 2),
            ("petition", 2), ("constitutional", 2), ("fundamental right", 3),
            ("ipc", 2), ("crpc", 2), ("bns", 2), ("bnss", 2), ("bharatiya nyaya", 3),
            ("criminal law", 2), ("ed", 2), ("cbi", 2), ("nia", 2),
            ("enforcement directorate", 3), ("investigation", 1), ("bail", 1),
            ("conviction", 1), ("acquittal", 1), ("sentencing", 1), ("death penalty", 2),
            ("pocso", 2), ("rape", 1), ("murder", 1)
        ],
        "🏗️ Infrastructure": [
            ("highway", 2), ("expressway", 2), ("railway", 2), ("metro", 2),
            ("bullet train", 3), ("airport", 2), ("port", 2), ("shipping", 2),
            ("inland waterway", 2), ("logistics", 2), ("smart city", 3),
            ("urban", 1), ("rural", 1), ("connectivity", 2), ("bridge", 1),
            ("tunnel", 2), ("dam", 2), ("canal", 2), ("irrigation", 2),
            ("power plant", 2), ("renewable energy", 2), ("grid", 2), ("transmission", 2)
        ]
    }

    # STRICT block list - any match = instant reject
    BLOCK_WORDS = [
        # Entertainment
        "movie review", "film review", "movie rating", "bollywood", "hollywood",
        "actor", "actress", "celebrity", "red carpet", "premiere", "box office",
        "oscar", "grammy", "emmy", "filmfare", "star", "hero", "heroine",
        "director", "producer", "sequel", "remake", "biopic",

        # Sports
        "cricket", "ipl", "football", "fifa", "world cup", "match", "score",
        "player", "team", "captain", "coach", "tournament", "championship",
        "sports", "athlete", "medal", "olympics", "badminton", "tennis",

        # Lifestyle
        "fashion", "lifestyle", "recipe", "food", "cook", "restaurant", "cafe",
        "travel", "tourism", "hotel", "resort", "vacation", "holiday",
        "wedding", "marriage", "birthday", "anniversary", "party",

        # Astrology
        "horoscope", "astrology", "zodiac", "rashifal", "rashiphal",
        "daily horoscope", "weekly horoscope", "tarot", "palmistry",
        "numerology", "vaastu", "vastu",

        # Real estate / Ads
        "real estate", "property", "flat", "apartment", "rent", "lease",
        "plot", "land for sale", "commercial space", "office space",

        # Crime/Gossip (not exam relevant)
        "obscene video", "sex scandal", "affair", "divorce", "custody battle",
        "murder mystery", "crime thriller", "serial killer",

        # Foreign local news
        "turkey", "school shooting", "us shooting", "mass shooting",

        # Static pages
        "code of ethics", "privacy policy", "terms of service", "about us",
        "contact us", "career", "job opening", "vacancy",

        # Generic filler
        "trending", "viral", "must watch", "must read", "top 10", "top 5",
        "how to", "tips and tricks", "life hacks", "diy"
    ]

    # Block if title contains these
    TITLE_BLOCK = [
        "review", "rating", "horoscope", "rashifal", "rashiphal",
        "movie", "film", "cricket", "ipl", "football match",
        "recipe", "fashion", "wedding", "birthday", "anniversary",
        "tarot", "astrology", "zodiac", "code of ethics",
        "privacy policy", "terms of use", "about us"
    ]

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        print("\n⚡ Strict Exam News Scraper initialized")
        print("   Filters: Entertainment, Sports, Astrology, Crime-gossip, Old news\n")

    def _get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7',
        }

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        junk_patterns = [
            r"Advertisement\s+", r"Story continues below this ad",
            r"Also Read \|.*?\n", r"Must Read \|.*?\n",
            r"View this post on Instagram.*?\n", r"A post shared by.*?\n",
            r"\(Photo:.*?\)", r"\(Express Photo.*?\)",
            r"Read More", r"Xwelcome Back.*?\n", r"Show Password.*?\n",
            r"Sign In.*?\n", r"Create Your Account.*?\n",
            r"Validate Otp.*?\n", r"Registeralready Have An Account.*?\n",
            r"Sso_Social_Box.*?\n", r"Var Template_Content.*?\n",
            r"Var Follow_Widget_Data.*?\n", r"Af_Article_Count.*?\n",
            r"Ie_Mobile_Check.*?\n", r"Sign In Withgmailfacebookapple.*?\n",
            r"Var Template_Content,Sso_Login_Box.*?\n",
        ]
        for pattern in junk_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        return text.strip()

    def _is_fresh_news(self, article: dict) -> bool:
        """Reject articles older than 3 days."""
        date_str = article.get("publish_date", "")
        if not date_str or date_str == "Today":
            return True
        try:
            pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
            age = datetime.now() - pub_date
            return age.days <= 3
        except:
            return True

    def _is_valid_article(self, article: dict) -> bool:
        title = article.get("title", "").lower()
        text = article.get("text", "")

        # STRICT: Block by title keywords
        for block in self.TITLE_BLOCK:
            if block in title:
                return False

        # Block by any block word
        for block in self.BLOCK_WORDS:
            if block in title or block in text.lower()[:800]:
                return False

        # Block garbage UI text
        garbage = [
            "newsletter", "subscribe", "sign up", "login", "sso_",
            "welcome back", "create your account", "show password",
            "validate otp", "register already", "sign in with",
            "advertisement", "trending", "must read", "also read",
            "story continues", "continue reading", "read more",
            "template_content", "follow_widget", "af_article",
            "ie_mobile", "sso_login", "sso_social", "var template"
        ]
        for g in garbage:
            if g in title or g in text.lower()[:500]:
                return False

        # Must have substantial content
        if len(text) < 400:
            return False
        if len(article.get("title", "")) < 20:
            return False

        # Must be fresh
        if not self._is_fresh_news(article):
            return False

        return True

    def _classify_article(self, title: str, text: str) -> dict:
        combined = (title + " " + text[:1500]).lower()
        title_lower = title.lower()

        # Quick reject: block words
        for block in self.BLOCK_WORDS:
            if block in title_lower:
                return {"is_exam_relevant": False, "topic": None, "confidence": 0, "score": 0}

        best_topic = None
        best_score = 0
        matched_keywords = []

        for topic, keywords in self.TOPIC_DEFINITIONS.items():
            score = 0
            matched = []
            for keyword, weight in keywords:
                if keyword in combined:
                    if keyword in title_lower:
                        score += weight * 2
                    else:
                        score += weight
                    matched.append(keyword)

            if score > best_score:
                best_score = score
                best_topic = topic
                matched_keywords = matched

        # STRICT: Need higher score to pass
        if best_score < 4:
            return {"is_exam_relevant": False, "topic": None, "confidence": 0, "score": 0}

        normalized_score = min(10, int(best_score / 2))
        confidence = min(0.95, 0.5 + (len(matched_keywords) * 0.05))

        return {
            "is_exam_relevant": True,
            "topic": best_topic,
            "confidence": confidence,
            "score": normalized_score
        }

    def scrape_source(self, source_name: str, url: str, 
                      max_articles: int, language: str) -> List[dict]:
        articles = []

        try:
            config = Config()
            config.browser_user_agent = random.choice(self.user_agents)
            config.request_timeout = 30

            paper = newspaper.build(url, config=config, memoize_articles=False)
            print(f"[{source_name}] Found {len(paper.articles)} raw articles")

            for article in paper.articles[:max_articles * 5]:
                try:
                    article.download()
                    article.parse()

                    if not article.text or len(article.text) < 400:
                        continue

                    cleaned_text = self._clean_text(article.text)

                    art = {
                        "title": article.title or "Untitled",
                        "text": cleaned_text,
                        "url": article.url,
                        "source": source_name,
                        "publish_date": str(article.publish_date)[:10] if article.publish_date else "Today",
                        "authors": ", ".join(article.authors) if article.authors else source_name,
                        "language": language
                    }

                    if not self._is_valid_article(art):
                        continue

                    result = self._classify_article(art["title"], art["text"])

                    if not result["is_exam_relevant"]:
                        print(f"  ✗ {art['title'][:55]}...")
                        continue

                    art["topic"] = result["topic"]
                    art["confidence"] = result["confidence"]
                    art["score"] = result["score"]

                    articles.append(art)
                    print(f"  ✓ [{art['score']}/10] {art['topic'][:22]} | {art['title'][:45]}...")

                    time.sleep(random.uniform(0.3, 0.6))

                except Exception as e:
                    continue

        except Exception as e:
            print(f"[{source_name}] Error: {e}")

        articles.sort(key=lambda x: x["score"], reverse=True)
        return articles[:max_articles]

    def scrape_all(self, sources_config=None) -> Dict[str, List[dict]]:
        if sources_config is None:
            from config import SOURCES as sources_config

        all_articles = []

        for source_name, config in sources_config.items():
            print(f"\n{'='*55}")
            print(f"📰 {source_name}")
            print(f"{'='*55}")

            articles = self.scrape_source(
                source_name,
                config["url"],
                config.get("max_articles", 10),
                config.get("language", "en")
            )
            all_articles.extend(articles)
            print(f"[{source_name}] Kept {len(articles)} articles")

        categorized = defaultdict(list)
        for art in all_articles:
            topic = art.get("topic", "General Current Affairs")
            categorized[topic].append(art)

        for topic in categorized:
            categorized[topic].sort(key=lambda x: x["score"], reverse=True)

        return dict(categorized)
