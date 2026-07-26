"""
Enhanced Exam News Scraper — with Gemini AI classification and GKToday support.
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
    """
    Strict scraper with AI-powered classification for exam-relevant news.
    """

    # STRICT block list — any match = instant reject before Gemini
    BLOCK_WORDS = [
        "movie review", "film review", "movie rating", "bollywood", "hollywood",
        "actor", "actress", "celebrity", "red carpet", "premiere", "box office",
        "oscar", "grammy", "emmy", "filmfare", "star", "hero", "heroine",
        "director", "producer", "sequel", "remake", "biopic",
        "cricket", "ipl", "football", "fifa", "world cup", "match", "score",
        "player", "team", "captain", "coach", "tournament", "championship",
        "sports", "athlete", "medal", "olympics", "badminton", "tennis",
        "fashion", "lifestyle", "recipe", "food", "cook", "restaurant", "cafe",
        "travel", "tourism", "hotel", "resort", "vacation", "holiday",
        "wedding", "marriage", "birthday", "anniversary", "party",
        "horoscope", "astrology", "zodiac", "rashifal", "rashiphal",
        "daily horoscope", "weekly horoscope", "tarot", "palmistry",
        "numerology", "vaastu", "vastu",
        "real estate", "property", "flat", "apartment", "rent", "lease",
        "plot", "land for sale", "commercial space", "office space",
        "obscene video", "sex scandal", "affair", "divorce", "custody battle",
        "murder mystery", "crime thriller", "serial killer",
        "turkey", "school shooting", "us shooting", "mass shooting",
        "code of ethics", "privacy policy", "terms of service", "about us",
        "contact us", "career", "job opening", "vacancy",
        "trending", "viral", "must watch", "must read", "top 10", "top 5",
        "how to", "tips and tricks", "life hacks", "diy"
    ]

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
        self.gemini = GeminiProcessor()
        print("\n⚡ AI-Enhanced Exam News Scraper initialized")
        print("   Pipeline: Scrape → Filter → Gemini AI → HTML Notes → Telegram\n")

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
        date_str = article.get("publish_date", "")
        if not date_str or date_str == "Today":
            return True
        try:
            pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
            age = datetime.now() - pub_date
            return age.days <= 5  # Slightly relaxed for weekly digests
        except:
            return True

    def _is_valid_article(self, article: dict) -> bool:
        title = article.get("title", "").lower()
        text = article.get("text", "")

        for block in self.TITLE_BLOCK:
            if block in title:
                return False

        for block in self.BLOCK_WORDS:
            if block in title or block in text.lower()[:800]:
                return False

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

        if len(text) < 400:
            return False
        if len(article.get("title", "")) < 20:
            return False

        if not self._is_fresh_news(article):
            return False

        return True

    def _classify_article(self, title: str, text: str) -> dict:
        """
        Fallback keyword classification (used when Gemini is disabled).
        Kept for backward compatibility.
        """
        from config import TOPIC_CATEGORIES

        combined = (title + " " + text[:1500]).lower()
        title_lower = title.lower()

        for block in self.BLOCK_WORDS:
            if block in title_lower:
                return {"is_exam_relevant": False, "topic": None, "confidence": 0, "score": 0}

        best_topic = None
        best_score = 0
        matched_keywords = []

        for topic, keywords in TOPIC_CATEGORIES.items():
            score = 0
            matched = []
            for keyword in keywords:
                if keyword in combined:
                    if keyword in title_lower:
                        score += 2
                    else:
                        score += 1
                    matched.append(keyword)

            if score > best_score:
                best_score = score
                best_topic = topic
                matched_keywords = matched

        if best_score < 3:
            return {"is_exam_relevant": False, "topic": None, "confidence": 0, "score": 0}

        normalized_score = min(10, int(best_score))
        confidence = min(0.95, 0.5 + (len(matched_keywords) * 0.05))

        return {
            "is_exam_relevant": True,
            "topic": best_topic,
            "confidence": confidence,
            "score": normalized_score
        }

    def _normalize_title(self, title: str) -> str:
        """Normalize title for deduplication."""
        title = title.lower()
        title = re.sub(r'[^\w\s]', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        # Remove common suffixes
        title = re.sub(r'\s+(the hindu|indian express|lokmat|loksatta|esakal|gktoday)$', '', title)
        return title

    def _deduplicate(self, articles: List[dict]) -> List[dict]:
        """Remove duplicate stories from different sources."""
        seen = {}
        unique = []

        for art in articles:
            norm = self._normalize_title(art.get("title", ""))
            if not norm or len(norm) < 15:
                unique.append(art)
                continue

            # Check similarity with existing
            is_dup = False
            for existing_norm in seen:
                # Simple containment check + length similarity
                if norm in existing_norm or existing_norm in norm:
                    if abs(len(norm) - len(existing_norm)) < 20:
                        is_dup = True
                        break

            if not is_dup:
                seen[norm] = art
                unique.append(art)

        print(f"   🔄 Deduplication: {len(articles)} → {len(unique)} articles")
        return unique

    def scrape_source(self, source_name: str, url: str,
                      max_articles: int, language: str) -> List[dict]:
        articles = []

        try:
            config = Config()
            config.browser_user_agent = random.choice(self.user_agents)
            config.request_timeout = 30

            paper = newspaper.build(url, config=config, memoize_articles=False)
            print(f"[{source_name}] Found {len(paper.articles)} raw articles")

            for article in paper.articles[:max_articles * 6]:
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
                        "publish_date": str(article.publish_date)[:10] if article.publish_date else datetime.now().strftime("%Y-%m-%d"),
                        "authors": ", ".join(article.authors) if article.authors else source_name,
                        "language": language
                    }

                    if not self._is_valid_article(art):
                        continue

                    articles.append(art)
                    time.sleep(random.uniform(0.2, 0.5))

                except Exception:
                    continue

        except Exception as e:
            print(f"[{source_name}] Error: {e}")

        return articles

    def scrape_all(self, sources_config=None) -> Dict[str, List[dict]]:
        from config import SOURCES as sources_config

        all_raw_articles = []

        for source_name, config in sources_config.items():
            print(f"\n{'='*55}")
            print(f"📰 {source_name}")
            print(f"{'='*55}")

            if config.get("type") == "gktoday":
                gk_scraper = GKTodayScraper()
                articles = gk_scraper.scrape(max_articles=config.get("max_articles", 15))
            else:
                articles = self.scrape_source(
                    source_name,
                    config["url"],
                    config.get("max_articles", 10),
                    config.get("language", "en")
                )

            all_raw_articles.extend(articles)
            print(f"[{source_name}] Kept {len(articles)} articles")

        # Deduplicate before AI processing
        all_raw_articles = self._deduplicate(all_raw_articles)

        # Send to Gemini for intelligent analysis
        print(f"\n🧠 Sending {len(all_raw_articles)} articles to Gemini 1.5 Pro...")
        enriched_articles = self.gemini.analyze_articles_batch(all_raw_articles)

        # Categorize by GS Paper first, then sub-topic
        categorized = defaultdict(list)
        for art in enriched_articles:
            gs = art.get("gs_paper", "General")
            sub = art.get("sub_topic", "General")
            key = f"{gs} — {sub}"
            categorized[key].append(art)

        # Sort within each category by relevance score
        for topic in categorized:
            categorized[topic].sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return dict(categorized)
