"""
AI-Powered Exam News Scraper using Zero-Shot Classification.
Uses facebook/bart-large-mnli to intelligently categorize articles.
"""

import newspaper
from newspaper import Article, Config
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import Dict, List
from transformers import pipeline
from collections import defaultdict


class AIExamNewsScraper:
    """
    Smart scraper that uses AI (Zero-Shot Classification) to:
    1. Detect if an article is exam-relevant
    2. Categorize it into the right topic
    3. Score its importance for competitive exams
    """

    # Exam-relevant topic labels for zero-shot classification
    EXAM_TOPICS = [
        "Indian polity and governance",
        "Indian economy and finance",
        "International relations and diplomacy",
        "Defence and national security",
        "Science and technology",
        "Environment and ecology",
        "Social issues and welfare schemes",
        "Indian history and culture",
        "Law and judiciary",
        "Infrastructure and development"
    ]

    # What makes an article "NOT exam relevant"
    NON_EXAM_TOPICS = [
        "sports and cricket",
        "bollywood and entertainment",
        "celebrity gossip",
        "fashion and lifestyle",
        "food and recipes",
        "astrology and horoscope",
        "real estate listings",
        "job advertisements",
        "event announcements"
    ]

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]

        print("\n🤖 Loading AI classification model (facebook/bart-large-mnli)...")
        print("   This may take 1-2 minutes on first run...")

        # Load zero-shot classifier
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1
        )
        print("✅ AI model loaded successfully!\n")

    def _get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,mr;q=0.7',
        }

    def _clean_text(self, text: str) -> str:
        """Clean scraped text of junk."""
        if not text:
            return ""

        junk_patterns = [
            r"Advertisement\s+",
            r"Story continues below this ad",
            r"Also Read \|.*?\n",
            r"Must Read \|.*?\n",
            r"View this post on Instagram.*?\n",
            r"A post shared by.*?\n",
            r"\(Photo:.*?\)",
            r"\(Express Photo.*?\)",
            r"Read More",
            r"Xwelcome Back.*?\n",
            r"Show Password.*?\n",
            r"Sign In.*?\n",
            r"Create Your Account.*?\n",
            r"Validate Otp.*?\n",
            r"Registeralready Have An Account.*?\n",
            r"Sso_Social_Box.*?\n",
            r"Var Template_Content.*?\n",
            r"Var Follow_Widget_Data.*?\n",
            r"Af_Article_Count.*?\n",
            r"Ie_Mobile_Check.*?\n",
            r"Sign In Withgmailfacebookapple.*?\n",
            r"Var Template_Content,Sso_Login_Box.*?\n",
        ]

        for pattern in junk_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        return text.strip()

    def _is_valid_article(self, article: dict) -> bool:
        """Filter out garbage articles before AI classification."""
        title = article.get("title", "").lower()
        text = article.get("text", "")

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

        if len(text) < 300:
            return False
        if len(article.get("title", "")) < 15:
            return False

        return True

    def _classify_article(self, title: str, text: str) -> dict:
        """
        Use AI to classify article relevance and topic.
        Returns dict with: is_exam_relevant, topic, confidence, score
        """
        content = f"{title}. {text[:1000]}"

        # Step 1: Is this exam-relevant or non-exam content?
        exam_vs_non = self.classifier(
            content,
            candidate_labels=["exam relevant current affairs", "non-exam entertainment sports lifestyle"],
            multi_label=False
        )

        is_exam_relevant = (
            exam_vs_non['labels'][0] == "exam relevant current affairs" and 
            exam_vs_non['scores'][0] > 0.6
        )

        if not is_exam_relevant:
            return {
                "is_exam_relevant": False,
                "topic": None,
                "confidence": exam_vs_non['scores'][0],
                "score": 0
            }

        # Step 2: Classify into specific exam topic
        topic_result = self.classifier(
            content,
            candidate_labels=self.EXAM_TOPICS,
            multi_label=False
        )

        topic = topic_result['labels'][0]
        confidence = topic_result['scores'][0]

        # Calculate exam score (0-10)
        score = min(10, int(confidence * 10))

        # Boost score for high-impact keywords in title
        boost_keywords = [
            "supreme court", "parliament", "budget", "rbi", "president", "pm modi",
            "election", "policy", "scheme", "launch", "agreement", "treaty",
            "missile", "satellite", "isro", "drdo", "climate", "cop",
            "gdp", "inflation", "trade", "defence", "security", "border"
        ]
        title_lower = title.lower()
        for kw in boost_keywords:
            if kw in title_lower:
                score = min(10, score + 1)

        return {
            "is_exam_relevant": True,
            "topic": topic,
            "confidence": confidence,
            "score": score
        }

    def scrape_source(self, source_name: str, url: str, 
                      max_articles: int, language: str) -> List[dict]:
        """Scrape and AI-classify articles from one source."""
        articles = []

        try:
            config = Config()
            config.browser_user_agent = random.choice(self.user_agents)
            config.request_timeout = 30

            paper = newspaper.build(url, config=config, memoize_articles=False)
            print(f"[{source_name}] Found {len(paper.articles)} raw articles")

            for article in paper.articles[:max_articles * 4]:
                try:
                    article.download()
                    article.parse()

                    if not article.text or len(article.text) < 300:
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

                    # AI CLASSIFICATION
                    ai_result = self._classify_article(art["title"], art["text"])

                    if not ai_result["is_exam_relevant"]:
                        print(f"  ✗ SKIPPED (not exam-relevant): {art['title'][:60]}...")
                        continue

                    art["topic"] = ai_result["topic"]
                    art["confidence"] = ai_result["confidence"]
                    art["score"] = ai_result["score"]

                    articles.append(art)
                    print(f"  ✓ [{art['score']}/10] {art['topic'][:30]}... | {art['title'][:50]}...")

                    time.sleep(random.uniform(0.5, 1.0))

                except Exception as e:
                    continue

        except Exception as e:
            print(f"[{source_name}] Error: {e}")

        articles.sort(key=lambda x: x["score"], reverse=True)
        return articles[:max_articles]

    def scrape_all(self, sources_config=None) -> Dict[str, List[dict]]:
        """
        Scrape all sources and organize by AI-detected topic.
        If sources_config not provided, reads from config.SOURCES.
        """
        # Import here to avoid circular dependency
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
            print(f"[{source_name}] Kept {len(articles)} exam-relevant articles")

        # Organize by AI-detected topic
        categorized = defaultdict(list)

        for art in all_articles:
            topic = art.get("topic", "General Current Affairs")
            categorized[topic].append(art)

        for topic in categorized:
            categorized[topic].sort(key=lambda x: x["score"], reverse=True)

        return dict(categorized)
