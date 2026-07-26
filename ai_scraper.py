"""
Enhanced Exam News Scraper — Aggressive filtering + AI classification.
"""

import newspaper
from newspaper import Article, Config
import time
import random
import re
from typing import Dict, List
from collections import defaultdict
from datetime import datetime, timedelta

from gktoday_scraper import GKTodayScraper
from gemini_processor import GeminiProcessor


class AIExamNewsScraper:

    # Block words for title + early text
    BLOCK_WORDS = [
        "movie review", "film review", "bollywood", "hollywood",
        "actor", "actress", "celebrity", "box office", "oscar", "grammy",
        "cricket", "ipl", "football", "fifa", "world cup", "match", "score",
        "player", "team", "captain", "tournament", "sports", "athlete", "medal",
        "fashion", "lifestyle", "recipe", "food", "cook", "restaurant",
        "travel", "tourism", "hotel", "resort", "vacation",
        "wedding", "marriage", "birthday", "anniversary", "party",
        "horoscope", "astrology", "zodiac", "rashifal", "rashiphal",
        "tarot", "palmistry", "numerology", "vaastu", "vastu",
        "real estate", "property", "flat", "apartment", "rent",
        "obscene video", "sex scandal", "affair", "divorce",
        "trending", "viral", "must watch", "must read", "top 10", "top 5",
        "how to", "tips and tricks", "life hacks", "diy"
    ]

    # Block if in title
    TITLE_BLOCK = [
        "review", "rating", "horoscope", "rashifal", "rashiphal",
        "movie", "film", "cricket", "ipl", "football match",
        "recipe", "fashion", "wedding", "birthday", "anniversary",
        "tarot", "astrology", "zodiac", "code of ethics",
        "privacy policy", "terms of use", "about us", "opinions editor"
    ]

    # URL path blocks
    URL_BLOCKS = [
        r"/sponsored", r"/videos/", r"/horoscope", r"/astrology",
        r"/sports/", r"/cricket/", r"/entertainment/", r"/lifestyle/",
        r"/fashion/", r"/recipe/", r"/movie-", r"/film-"
    ]

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        self.gemini = GeminiProcessor()
        print("\n⚡ AI-Enhanced Exam News Scraper initialized")
        print("   Pipeline: Scrape → Aggressive Filter → Gemini AI → Structured Notes → Telegram\n")

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        junk = [
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
        ]
        for p in junk:
            text = re.sub(p, "", text, flags=re.IGNORECASE)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        return text.strip()

    def _is_fresh(self, article: dict) -> bool:
        date_str = article.get("publish_date", "")
        if not date_str or date_str == "Today":
            return True
        try:
            pub = datetime.strptime(date_str[:10], "%Y-%m-%d")
            return (datetime.now() - pub).days <= 5
        except:
            return True

    def _is_valid_article(self, article: dict) -> bool:
        title = article.get("title", "").lower()
        text = article.get("text", "")
        url = article.get("url", "").lower()

        # URL filter
        for pattern in self.URL_BLOCKS:
            if re.search(pattern, url):
                return False

        # Title blocks
        for block in self.TITLE_BLOCK:
            if block in title:
                return False

        # Content blocks
        for block in self.BLOCK_WORDS:
            if block in title or block in text.lower()[:800]:
                return False

        # UI garbage
        garbage = ["newsletter", "subscribe", "sign up", "login", "sso_",
                   "welcome back", "create your account", "show password",
                   "validate otp", "advertisement", "trending", "must read",
                   "story continues", "read more", "template_content"]
        for g in garbage:
            if g in title or g in text.lower()[:400]:
                return False

        if len(text) < 500:
            return False
        if len(article.get("title", "")) < 20:
            return False

        return self._is_fresh(article)

    def _normalize_title(self, title: str) -> str:
        title = title.lower()
        title = re.sub(r'[^\w\s]', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        title = re.sub(r'\s+(the hindu|indian express|lokmat|loksatta|esakal|gktoday)$', '', title)
        return title

    def _deduplicate(self, articles: List[dict]) -> List[dict]:
        seen = {}
        unique = []
        for art in articles:
            norm = self._normalize_title(art.get("title", ""))
            if not norm or len(norm) < 15:
                unique.append(art)
                continue

            is_dup = False
            for existing_norm in seen:
                if norm in existing_norm or existing_norm in norm:
                    if abs(len(norm) - len(existing_norm)) < 25:
                        is_dup = True
                        break

            if not is_dup:
                seen[norm] = art
                unique.append(art)

        print(f"   🔄 Deduplication: {len(articles)} → {len(unique)}")
        return unique

    def scrape_source(self, source_name: str, url: str,
                      max_articles: int, language: str) -> List[dict]:
        articles = []
        try:
            config = Config()
            config.browser_user_agent = random.choice(self.user_agents)
            config.request_timeout = 30

            paper = newspaper.build(url, config=config, memoize_articles=False)
            print(f"[{source_name}] Found {len(paper.articles)} raw links")

            for article in paper.articles[:max_articles * 6]:
                try:
                    article.download()
                    article.parse()

                    if not article.text or len(article.text) < 500:
                        continue

                    art = {
                        "title": article.title or "Untitled",
                        "text": self._clean_text(article.text),
                        "url": article.url,
                        "source": source_name,
                        "publish_date": str(article.publish_date)[:10] if article.publish_date else datetime.now().strftime("%Y-%m-%d"),
                        "authors": ", ".join(article.authors) if article.authors else source_name,
                        "language": language
                    }

                    if not self._is_valid_article(art):
                        continue

                    articles.append(art)
                    time.sleep(random.uniform(0.2, 0.4))

                except Exception:
                    continue

        except Exception as e:
            print(f"[{source_name}] Error: {e}")

        return articles

    def scrape_all(self, sources_config=None) -> Dict[str, List[dict]]:
        from config import SOURCES as sources_config

        all_raw = []

        for source_name, config in sources_config.items():
            print(f"\n{'='*55}")
            print(f"📰 {source_name}")
            print(f"{'='*55}")

            if config.get("type") == "gktoday":
                gk = GKTodayScraper()
                articles = gk.scrape(max_articles=config.get("max_articles", 15))
            else:
                articles = self.scrape_source(
                    source_name, config["url"],
                    config.get("max_articles", 10),
                    config.get("language", "en")
                )

            all_raw.extend(articles)
            print(f"[{source_name}] Kept {len(articles)} articles")

        # Deduplicate
        all_raw = self._deduplicate(all_raw)

        # AI Analysis
        print(f"\n🧠 Sending {len(all_raw)} articles to analysis pipeline...")
        enriched = self.gemini.analyze_articles(all_raw)

        # Categorize by GS Paper → Sub-topic
        categorized = defaultdict(list)
        for art in enriched:
            gs = art.get("gs_paper", "General")
            sub = art.get("sub_topic", "General")
            key = f"{gs} — {sub}"
            categorized[key].append(art)

        for topic in categorized:
            categorized[topic].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return dict(categorized)
