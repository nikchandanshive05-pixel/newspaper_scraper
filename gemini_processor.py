"""
Gemini Processor — Uses google-genai (official, non-deprecated).
Fallback topics embedded so no import errors ever.
"""

import os
import json
import time
import re
from typing import List, Dict

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# ─── Embedded fallback topics — zero external dependencies ──────────
FALLBACK_TOPICS = {
    "Polity & Governance": [
        "parliament", "constitution", "amendment", "bill", "act", "supreme court",
        "high court", "election", "commission", "governor", "president", "cabinet",
        "ministry", "policy", "governance", "judicial", "legislation", "ordinance",
        "delimitation", "federalism", "panchayat", "municipal", "anti-defection",
        "fundamental right", "directive principle", "lok sabha", "rajya sabha"
    ],
    "Economy & Finance": [
        "gdp", "inflation", "rbi", "reserve bank", "monetary policy", "fiscal",
        "budget", "tax", "gst", "trade", "export", "import", "fdi", "fii",
        "stock market", "sensex", "nifty", "banking", "insurance", "sebi",
        "imf", "world bank", "wto", "tariff", "subsidy", "msme", "startup",
        "digital payment", "upi", "cryptocurrency", "rupee", "fiscal deficit", "repo rate"
    ],
    "International Relations": [
        "bilateral", "multilateral", "summit", "g20", "g7", "brics", "saarc",
        "un", "unsc", "nato", "asean", "eu", "treaty", "agreement", "mou",
        "diplomatic", "embassy", "border dispute", "foreign policy", "defence deal",
        "india-china", "india-us", "india-russia", "pakistan", "afghanistan",
        "myanmar", "bangladesh", "nepal", "sri lanka", "maldives"
    ],
    "Defence & Security": [
        "defence", "military", "army", "navy", "air force", "coast guard",
        "paramilitary", "crpf", "bsf", "itbp", "missile", "drdo", "isro",
        "space mission", "satellite", "nuclear", "terrorism", "naxal", "maoist",
        "insurgency", "cyber security", "border security", "internal security"
    ],
    "Science & Technology": [
        "isro", "space mission", "rocket", "satellite", "mars", "moon",
        "gaganyaan", "chandrayaan", "agnikul", "skyroot", "drdo", "ai",
        "artificial intelligence", "machine learning", "quantum", "biotechnology",
        "genome", "vaccine", "renewable energy", "solar", "hydrogen",
        "electric vehicle", "semiconductor", "chip", "5g", "6g", "telecom", "digital india"
    ],
    "Environment & Ecology": [
        "climate change", "global warming", "cop", "paris agreement",
        "biodiversity", "species", "endangered", "extinction", "wildlife",
        "tiger", "elephant", "lion", "forest", "deforestation", "afforestation",
        "wetland", "ramsar", "pollution", "air quality", "waste management",
        "renewable", "sustainable", "green energy", "carbon", "net zero",
        "national park", "sanctuary", "biosphere", "tiger reserve"
    ],
    "Social Issues": [
        "education", "health", "healthcare", "poverty", "inequality", "caste", "tribe",
        "scheduled caste", "scheduled tribe", "women empowerment", "gender",
        "child rights", "juvenile", "labour", "migrant", "unemployment", "job",
        "nutrition", "mid-day meal", "anganwadi", "pension", "scheme", "yojana",
        "mission", "programme", "welfare"
    ],
    "History & Culture": [
        "archaeological", "excavation", "heritage", "monument", "museum",
        "artifact", "manuscript", "inscription", "festival", "art form",
        "handloom", "unesco", "world heritage", "gi tag", "cultural", "civilization",
        "freedom struggle", "independence", "gandhi", "nehru"
    ],
    "Law & Judiciary": [
        "supreme court", "high court", "judgment", "verdict", "petition",
        "constitutional", "fundamental right", "ipc", "crpc", "bns", "bnss",
        "bharatiya nyaya", "criminal law", "ed", "cbi", "nia",
        "enforcement directorate", "investigation", "bail", "conviction", "death penalty"
    ],
    "Infrastructure": [
        "highway", "expressway", "railway", "metro", "bullet train", "airport",
        "port", "shipping", "inland waterway", "logistics", "smart city",
        "urban", "rural", "connectivity", "bridge", "tunnel", "dam", "canal",
        "irrigation", "power plant", "renewable energy", "grid", "transmission"
    ]
}


class GeminiProcessor:

    GS_COLORS = {
        "GS1": "#c62828", "GS2": "#1565c0", "GS3": "#2e7d32",
        "GS4": "#6a1b9a", "Essay": "#e65100",
        "General": "#455a64", "Skip": "#757575"
    }

    URL_BLOCKS = [
        r"/sponsored", r"/videos/", r"/horoscope", r"/astrology",
        r"/rashifal", r"/sports/", r"/cricket/", r"/ipl/",
        r"/entertainment/", r"/lifestyle/", r"/fashion/",
        r"/recipe/", r"/movie-", r"/film-", r"/bollywood/",
        r"/brand-studio/", r"/partner-content/"
    ]

    CONTENT_BLOCKS = [
        "sponsored", "brand studio", "partner content", "promoted by",
        "movie review", "film review", "cricket", "ipl ", "football match",
        "horoscope", "rashifal", "rashiphal", "astrology", "zodiac",
        "recipe", "fashion", "wedding", "birthday", "anniversary",
        "tarot", "palmistry", "numerology", "vaastu", "vastu",
        "box office", "red carpet", "celebrity", "actor", "actress",
        "opinions editor", "from the opinions editor",
        "editorial:", "op-ed:", "letter to the editor"
    ]

    def __init__(self):
        self.enabled = False
        self.client = None
        self.processed_count = 0
        self.fallback_reason = ""
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        if not GENAI_AVAILABLE:
            self.fallback_reason = "google-genai not installed"
            print("🤖 Gemini disabled: Package not installed")
            return

        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            self.fallback_reason = "No GEMINI_API_KEY"
            print("🤖 Gemini disabled: No API key")
            return

        try:
            self.client = genai.Client(api_key=key)
            available = [m.name for m in self.client.models.list() if "gemini" in m.name.lower()]
            if not available:
                self.fallback_reason = "No Gemini models for this key"
                print(f"🤖 Gemini disabled: {self.fallback_reason}")
                return

            if self.model_name not in available:
                candidates = [
                    self.model_name,
                    f"models/{self.model_name}",
                    self.model_name.replace("models/", ""),
                    "gemini-2.5-flash", "gemini-2.5-flash-preview-05-20",
                    "gemini-1.5-pro", "gemini-1.5-flash",
                ]
                for c in candidates:
                    if c in available:
                        self.model_name = c
                        break
                else:
                    self.model_name = available[0]

            self.enabled = True
            print(f"🤖 Gemini ready: {self.model_name}")

        except Exception as e:
            self.fallback_reason = f"Init failed: {e}"
            print(f"🤖 Gemini disabled: {e}")

    def _is_garbage(self, article: Dict) -> bool:
        title = article.get("title", "").lower()
        text = article.get("text", "").lower()[:600]
        url = article.get("url", "").lower()

        for p in self.URL_BLOCKS:
            if re.search(p, url):
                return True
        for b in self.CONTENT_BLOCKS:
            if b in title or b in text:
                return True
        if len(article.get("text", "")) < 500:
            return True
        return False

    def _build_prompt(self, article: Dict) -> str:
        text = article.get("text", "")[:3500]
        title = article.get("title", "")
        source = article.get("source", "")

        return f"""You are a senior UPSC CSE faculty. Convert this news into structured exam notes.

ARTICLE:
Title: {title}
Source: {source}
Text: {text}

Return ONLY this JSON (no markdown, no explanation):
{{
  "gs_paper": "GS1"|"GS2"|"GS3"|"GS4"|"Essay"|"Skip",
  "sub_topic": "Specific sub-topic",
  "syllabus_tag": "GSX - Topic - Sub-topic",
  "relevance_score": 0-10,
  "key_bullets": ["5-7 factual bullets with names, numbers, dates, institutions"],
  "quick_note": "2-3 sentences: what happened + why it matters for UPSC",
  "keywords": ["8-12 terms: schemes, laws, articles, committees, reports"],
  "prelims_angle": "Prelims: [Specific MCQ-ready fact]",
  "mains_angle": "Mains: [Analytical question] (150/250 words)",
  "should_include": true|false,
  "skip_reason": "reason if false"
}}

RULES:
- Skip sponsored, opinion-only, sports, entertainment, astrology, local crime
- Every bullet must contain a specific name, number, date, or institution
- Mains angle must be analytical, not definitional

JSON ONLY:"""

    def _extract_json(self, text: str) -> Dict:
        text = text.strip()
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*```$', '', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        raise ValueError("JSON extraction failed")

    def _call_gemini(self, prompt: str) -> str:
        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.15,
                        max_output_tokens=4096,
                    )
                )
                return response.text
            except Exception as e:
                err_str = str(e).lower()
                if "404" in err_str or "403" in err_str or "not found" in err_str:
                    raise
                wait = 2 ** attempt
                print(f"   ⚠️  Retry {attempt+1}/2 in {wait}s: {e}")
                time.sleep(wait)
        raise Exception("API exhausted")

    def _validate_result(self, result: Dict, article: Dict) -> bool:
        if not result.get("should_include"):
            return False
        bullets = result.get("key_bullets", [])
        if len(bullets) < 3:
            return False
        factual = 0
        for b in bullets:
            if re.search(r'\b(?:19|20)\d{2}\b', b):
                factual += 1
            elif re.search(r'\b(?:Rs\.?|₹| crore | lakh | percent|%)\b', b):
                factual += 1
            elif re.search(r'\b[A-Z][a-zA-Z]+ (?:Act|Bill|Scheme|Mission|Policy|Committee|Report|Index|Organization|Bank|Court|Commission)\b', b):
                factual += 1
        return factual >= 2

    def analyze_article(self, article: Dict) -> Dict:
        if not self.enabled:
            return self._fallback_single(article)

        if self._is_garbage(article):
            return None

        max_articles = int(os.getenv("MAX_GEMINI_ARTICLES", "25"))
        if self.processed_count >= max_articles:
            return self._fallback_single(article)

        try:
            prompt = self._build_prompt(article)
            print(f"   🧠 Gemini: {article['title'][:55]}...")

            response_text = self._call_gemini(prompt)
            result = self._extract_json(response_text)
            self.processed_count += 1

            if not result.get("should_include"):
                print(f"   ✗ Skipped: {result.get('skip_reason', 'unknown')}")
                return None

            if not self._validate_result(result, article):
                print(f"   ⚠️  Low quality — fallback")
                return self._fallback_single(article)

            bullets = [b.strip() for b in result.get("key_bullets", []) if len(b.strip()) > 25]
            bullets = [b for b in bullets if not b.lower().startswith(("bad example", "good example"))]

            return {
                **article,
                "gs_paper": result.get("gs_paper", "General"),
                "sub_topic": result.get("sub_topic", "General"),
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
            print(f"   ❌ Gemini error: {e}")
            return self._fallback_single(article)

    def analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        if not self.enabled:
            print(f"🤖 {self.fallback_reason} — using keyword fallback")
            return self._fallback_all(articles)

        enriched = []
        for art in articles:
            result = self.analyze_article(art)
            if result:
                enriched.append(result)
            time.sleep(0.5)

        gemini_count = sum(1 for a in enriched if a.get("gemini_processed"))
        print(f"\n📊 Gemini: {gemini_count}/{len(enriched)} articles AI-analyzed")
        return enriched

    def _fallback_single(self, article: Dict) -> Dict:
        if self._is_garbage(article):
            return None

        title = article.get("title", "").lower()
        text = article.get("text", "").lower()
        combined = (title + " " + text[:2000])

        best_topic = None
        best_score = 0
        matched = []

        for topic, keywords in FALLBACK_TOPICS.items():
            score = 0
            local_matched = []
            for kw in keywords:
                if kw in combined:
                    score += 3 if kw in title else 1
                    local_matched.append(kw)
            if score > best_score:
                best_score = score
                best_topic = topic
                matched = local_matched

        if best_score < 4:
            return None

        raw = article.get("text", "")
        sentences = re.split(r'(?<=[.!?])\s+', raw)
        bullets = []
        for s in sentences:
            s = s.strip()
            if 40 < len(s) < 180 and any(c.isdigit() for c in s):
                bullets.append(s)
            if len(bullets) >= 5:
                break
        if len(bullets) < 3:
            bullets = [s.strip() for s in sentences[:4] if 30 < len(s.strip()) < 200]

        gs = self._map_topic_to_gs(best_topic)
        clean_topic = re.sub(r'[^\w\s&]', '', best_topic).strip()

        return {
            **article,
            "gs_paper": gs,
            "sub_topic": clean_topic,
            "syllabus_tag": f"{gs} - {clean_topic}",
            "relevance_score": min(10, best_score),
            "key_bullets": bullets[:6] if bullets else [raw[:120] + "..."],
            "quick_note": raw[:280] if raw else "",
            "keywords": matched[:10],
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
