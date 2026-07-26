"""
Gemini 1.5 Pro Processor — Per-article deep analysis for UPSC notes.
"""

import os
import json
import time
import re
from typing import List, Dict, Any
from config import GEMINI_API_KEY, GEMINI_MODEL, ENABLE_GEMINI, MAX_GEMINI_ARTICLES

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiProcessor:
    """
    Processes EACH article individually with Gemini 1.5 Pro for maximum quality.
    Falls back to smart keyword logic if Gemini fails or is disabled.
    """

    GS_COLORS = {
        "GS1": "#c62828", "GS2": "#1565c0", "GS3": "#2e7d32",
        "GS4": "#6a1b9a", "Essay": "#e65100",
        "General": "#455a64", "Skip": "#757575"
    }

    # URL patterns that instantly kill an article
    URL_BLOCKS = [
        r"/sponsored", r"/videos/", r"/horoscope", r"/astrology",
        r"/rashifal", r"/sports/", r"/cricket/", r"/ipl/",
        r"/entertainment/", r"/lifestyle/", r"/fashion/",
        r"/recipe/", r"/movie-", r"/film-", r"/bollywood/",
        r"/brand-studio/", r"/partner-content/"
    ]

    # Title/text patterns that instantly kill an article
    CONTENT_BLOCKS = [
        "sponsored", "brand studio", "partner content", "promoted by",
        "movie review", "film review", "cricket", "ipl ", "football match",
        "horoscope", "rashifal", "rashiphal", "astrology", "zodiac",
        "recipe", "fashion", "wedding", "birthday", "anniversary",
        "tarot", "palmistry", "numerology", "vaastu", "vastu",
        "box office", "red carpet", "celebrity", "actor", "actress",
        "opinions editor", "from the opinions editor",  # low-yield opinion columns
        "editorial:", "op-ed:", "letter to the editor"
    ]

    def __init__(self):
        self.enabled = ENABLE_GEMINI and GEMINI_API_KEY and GENAI_AVAILABLE
        self.model = None
        self.processed_count = 0

        if self.enabled:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(GEMINI_MODEL)
                print(f"🤖 Gemini 1.5 Pro ready (max {MAX_GEMINI_ARTICLES} articles)")
            except Exception as e:
                print(f"⚠️  Gemini init failed: {e}")
                self.enabled = False
        else:
            print("🤖 Gemini OFF — using smart keyword fallback")

    def _is_garbage(self, article: Dict) -> bool:
        """Aggressive pre-filter before wasting API calls."""
        title = article.get("title", "").lower()
        text = article.get("text", "").lower()[:600]
        url = article.get("url", "").lower()

        # URL-based kill
        for pattern in self.URL_BLOCKS:
            if re.search(pattern, url):
                print(f"   ✗ URL-filtered ({pattern.strip('/')}): {article['title'][:45]}...")
                return True

        # Content-based kill
        for block in self.CONTENT_BLOCKS:
            if block in title or block in text:
                print(f"   ✗ Content-filtered ({block}): {article['title'][:45]}...")
                return True

        # Length check
        if len(article.get("text", "")) < 500:
            return True

        return False

    def _build_prompt(self, article: Dict) -> str:
        """Surgical prompt that forces structured, factual output."""
        text = article.get("text", "")[:3500]
        title = article.get("title", "")
        source = article.get("source", "")
        url = article.get("url", "")

        prompt = f"""You are a senior UPSC CSE faculty (15+ years) and former interview board member. Convert this news article into structured exam notes.

ARTICLE METADATA:
- Title: {title}
- Source: {source}
- URL: {url}

ARTICLE TEXT:
{text}

TASK: Return ONLY a valid JSON object. No markdown, no explanation, no code blocks.

JSON SCHEMA:
{{
  "gs_paper": "GS1"|"GS2"|"GS3"|"GS4"|"Essay"|"Skip",
  "sub_topic": "Specific sub-topic. Examples: 'International Relations', 'Indian Economy', 'Environment & Ecology', 'Science & Technology', 'Polity', 'Governance', 'Social Justice', 'Internal Security'",
  "syllabus_tag": "Precise mapping. Example: 'GS2 - Polity - Parliament & State Legislatures - Anti-Defection' or 'GS3 - Economy - Monetary Policy - RBI - Repo Rate'",
  "relevance_score": integer 0-10,
  "key_bullets": [
    "Exactly 5-7 factual bullets. EACH must contain a specific name, number, date, institution, law, or constitutional article.",
    "BAD example: 'The government is taking steps to improve the economy.'",
    "GOOD example: 'The RBI, in its August 2024 MPC meeting, kept the repo rate unchanged at 6.50% for the 9th consecutive time, citing CPI inflation at 4.75%.'"
  ],
  "quick_note": "2-3 sentences. First sentence: what happened. Second sentence: why it matters for UPSC. Third sentence: policy/exam implication.",
  "keywords": ["8-12 terms: schemes, laws, articles, committees, organizations, reports, indices"],
  "prelims_angle": "One concrete prelims fact formatted as: 'Prelims: [Specific fact that can be asked as MCQ]'",
  "mains_angle": "One analytical mains question. Format: 'Mains: [Question] (150/250 words)'",
  "should_include": true|false,
  "skip_reason": "If false, one-word reason: 'sponsored'|'sports'|'entertainment'|'opinion'|'local_news'|'not_syllabus'"
}}

RULES:
1. STRICT FILTER: Skip sponsored content, brand promotions, pure opinion columns, sports, entertainment, astrology, crime gossip, local city news without national impact.
2. Skip articles that are just opinion/editorial without concrete policy, data, or institutional action.
3. "key_bullets" MUST be factual. Every bullet needs a name, number, or date.
4. "mains_angle" must be analytical — not 'What is X?' but 'Critically examine X in light of Y.'
5. "prelims_angle" must be a specific fact, not a generic topic.

JSON ONLY:"""

        return prompt

    def _extract_json(self, text: str) -> Dict:
        """Bulletproof JSON extraction."""
        text = text.strip()

        # Remove markdown fences
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*```$', '', text)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Find outermost braces
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass

        raise ValueError("JSON extraction failed")

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini with retry."""
        for attempt in range(2):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.15,
                        max_output_tokens=4096,
                    )
                )
                return response.text
            except Exception as e:
                wait = 2 ** attempt
                print(f"   ⚠️  Gemini retry {attempt+1}/2 in {wait}s: {e}")
                time.sleep(wait)
        raise Exception("Gemini API exhausted")

    def _validate_result(self, result: Dict, article: Dict) -> bool:
        """Ensure Gemini output is actually useful."""
        if not result.get("should_include"):
            return False

        # Bullets quality check
        bullets = result.get("key_bullets", [])
        if len(bullets) < 3:
            return False

        # Check if bullets are actually factual (contain numbers, dates, or capitalized proper nouns)
        factual_count = 0
        for b in bullets:
            if re.search(r'\b(?:19|20)\d{2}\b', b):  # Year
                factual_count += 1
            elif re.search(r'\b(?:Rs\.?|₹| crore | lakh | percent|%)', b):  # Numbers/money
                factual_count += 1
            elif re.search(r'\b[A-Z][a-zA-Z]+ (?:Act|Bill|Scheme|Mission|Policy|Committee|Report|Index|Organization|Bank|Court|Commission|Ministry|Department)\b', b):
                factual_count += 1

        if factual_count < 2:
            print(f"   ⚠️  Low-quality bullets for: {article['title'][:40]}... — using fallback")
            return False

        return True

    def analyze_article(self, article: Dict) -> Dict:
        """Deep analysis of a single article."""
        if not self.enabled:
            return self._fallback_single(article)

        if self._is_garbage(article):
            return None

        if self.processed_count >= MAX_GEMINI_ARTICLES:
            print(f"   ⏭️  Gemini cap reached ({MAX_GEMINI_ARTICLES}), using fallback")
            return self._fallback_single(article)

        try:
            prompt = self._build_prompt(article)
            print(f"   🧠 Gemini analyzing: {article['title'][:55]}...")

            response_text = self._call_gemini(prompt)
            result = self._extract_json(response_text)

            self.processed_count += 1

            if not result.get("should_include"):
                print(f"   ✗ Gemini skipped: {result.get('skip_reason', 'unknown')}")
                return None

            if not self._validate_result(result, article):
                return self._fallback_single(article)

            # Clean bullets
            bullets = [b.strip() for b in result.get("key_bullets", []) if len(b.strip()) > 25]
            bullets = [b for b in bullets if not b.lower().startswith(("bad example", "good example", "example:"))]

            return {
                **article,
                "gs_paper": result.get("gs_paper", "General"),
                "sub_topic": result.get("sub_topic", "General Current Affairs"),
                "syllabus_tag": result.get("syllabus_tag", ""),
                "relevance_score": min(10, max(1, result.get("relevance_score", 5))),
                "key_bullets": bullets[:7],
                "quick_note": result.get("quick_note", ""),
                "keywords": result.get("keywords", [])[:12],
                "prelims_angle": result.get("prelims_angle", ""),
                "mains_angle": result.get("mains_angle", ""),
                "gemini_processed": True,
                "gs_color": self.GS_COLORS.get(result.get("gs_paper", "General"), "#455a64")
            }

        except Exception as e:
            print(f"   ❌ Gemini failed on '{article['title'][:40]}...': {e}")
            return self._fallback_single(article)

    def analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process all articles. Returns only included, enriched ones."""
        if not self.enabled:
            print("🤖 Gemini disabled — running smart keyword fallback")
            return self._fallback_all(articles)

        enriched = []
        for art in articles:
            result = self.analyze_article(art)
            if result:
                enriched.append(result)
            time.sleep(0.6)  # Rate limit

        gemini_count = sum(1 for a in enriched if a.get("gemini_processed"))
        print(f"\n📊 Gemini stats: {gemini_count}/{len(enriched)} articles AI-analyzed")
        return enriched

    # ─── Fallback Methods ─────────────────────────────────────────────

    def _fallback_single(self, article: Dict) -> Dict:
        """High-quality keyword fallback with structured bullets."""
        if self._is_garbage(article):
            return None

        from config import TOPIC_CATEGORIES

        title = article.get("title", "").lower()
        text = article.get("text", "").lower()
        combined = (title + " " + text[:2000])

        best_topic = None
        best_score = 0
        matched_keywords = []

        for topic, keywords in TOPIC_CATEGORIES.items():
            score = 0
            matched = []
            for kw in keywords:
                if kw in combined:
                    if kw in title:
                        score += 3
                    else:
                        score += 1
                    matched.append(kw)
            if score > best_score:
                best_score = score
                best_topic = topic
                matched_keywords = matched

        if best_score < 4:
            return None

        # Generate structured bullets from text
        raw_text = article.get("text", "")
        sentences = re.split(r'(?<=[.!?])\s+', raw_text)
        bullets = []
        for s in sentences:
            s = s.strip()
            if 40 < len(s) < 180 and any(c.isdigit() for c in s):
                bullets.append(s)
            if len(bullets) >= 5:
                break

        if len(bullets) < 3:
            # Fallback: just take first few meaningful sentences
            bullets = [s.strip() for s in sentences[:4] if 30 < len(s.strip()) < 200]

        gs = self._map_topic_to_gs(best_topic)
        clean_topic = re.sub(r'[^\w\s&]', '', best_topic).strip()

        return {
            **article,
            "gs_paper": gs,
            "sub_topic": clean_topic,
            "syllabus_tag": f"{gs} - {clean_topic}",
            "relevance_score": min(10, best_score),
            "key_bullets": bullets[:6] if bullets else [raw_text[:120] + "..."],
            "quick_note": raw_text[:280] if raw_text else "",
            "keywords": matched_keywords[:10],
            "prelims_angle": "",
            "mains_angle": "",
            "gemini_processed": False,
            "gs_color": self.GS_COLORS.get(gs, "#455a64")
        }

    def _fallback_all(self, articles: List[Dict]) -> List[Dict]:
        results = []
        for art in articles:
            r = self._fallback_single(art)
            if r:
                results.append(r)
        return results

    def _map_topic_to_gs(self, topic: str) -> str:
        t = topic.lower()
        if any(x in t for x in ["polity", "governance", "international", "law", "judiciary"]):
            return "GS2"
        elif any(x in t for x in ["economy", "finance", "defence", "security", "science", "technology", "environment", "ecology", "infrastructure"]):
            return "GS3"
        elif any(x in t for x in ["social", "history", "culture"]):
            return "GS1"
        return "General"
