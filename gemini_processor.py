"""
Gemini 1.5 Pro Processor — Intelligent article analysis for UPSC notes.
"""

import os
import json
import time
import re
from typing import List, Dict, Any
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_BATCH_SIZE, ENABLE_GEMINI

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiProcessor:
    """
    Uses Gemini 1.5 Pro to classify, summarize, and structure articles
    into exam-ready revision notes.
    """

    GS_COLORS = {
        "GS1": "#c62828",
        "GS2": "#1565c0",
        "GS3": "#2e7d32",
        "GS4": "#6a1b9a",
        "Essay": "#e65100",
        "Skip": "#757575",
        "General": "#455a64"
    }

    def __init__(self):
        self.enabled = ENABLE_GEMINI and GEMINI_API_KEY and GENAI_AVAILABLE
        self.model = None

        if self.enabled:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(GEMINI_MODEL)
                print("🤖 Gemini 1.5 Pro initialized")
            except Exception as e:
                print(f"⚠️  Gemini init failed: {e}")
                self.enabled = False
        else:
            print("🤖 Gemini disabled — using keyword fallback")

    def _build_prompt(self, articles: List[Dict]) -> str:
        """
        Build a strict prompt that forces Gemini to return pure JSON.
        """
        # Truncate article text to save tokens
        article_summaries = []
        for idx, art in enumerate(articles):
            text_preview = art.get("text", "")[:1800]
            article_summaries.append({
                "index": idx,
                "title": art.get("title", ""),
                "source": art.get("source", ""),
                "text_preview": text_preview
            })

        prompt = f"""You are an expert UPSC CSE (Prelims + Mains) Current Affairs analyst and exam strategist with 10+ years of experience.

Analyze the following news articles and return a JSON array. For EACH article, provide exactly these fields:

- "gs_paper": One of ["GS1","GS2","GS3","GS4","Essay","Skip"]
- "sub_topic": Specific sub-topic like "International Relations", "Indian Economy", "Environment", "Polity"
- "syllabus_tag": Precise syllabus mapping. Example: "GS2 - Polity - Parliament & State Legislatures" or "GS3 - Economy - Monetary Policy"
- "relevance_score": Integer 1-10. 10 = extremely important, likely to be asked. 1-3 = low priority. Use 0 for "Skip".
- "key_bullets": Array of 5-7 concise, factual bullet points for revision. Each bullet must be a complete fact.
- "quick_note": 2-3 sentence summary for last-minute revision. Exam-focused, not generic.
- "keywords": Array of important terms, schemes, constitutional articles, laws, committees, reports.
- "prelims_angle": One specific prelims-style fact or MCQ angle. Be precise.
- "mains_angle": One mains question framing. Example: "Discuss the implications of X on Y in the context of Z."
- "should_include": boolean. false for sports, entertainment, astrology, pure crime/gossip, celebrity news, movie reviews.

CRITICAL RULES:
1. Return ONLY a valid JSON array. No markdown code blocks. No extra text before or after.
2. The array must have exactly {len(articles)} objects, in the same order as the articles provided.
3. If an article is not exam-relevant, set "should_include": false and "gs_paper": "Skip".
4. Be strict — most articles should be filtered out. Only keep genuinely exam-relevant news.
5. For "key_bullets", include specific numbers, names, dates, and institutional details whenever possible.
6. "mains_angle" should be framed as a question or directive suitable for a 150-250 word answer.

Articles:
{json.dumps(article_summaries, ensure_ascii=False, indent=2)}

JSON array:"""

        return prompt

    def _extract_json(self, text: str) -> List[Dict]:
        """Robustly extract JSON array from Gemini response."""
        text = text.strip()

        # Try direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        patterns = [
            r'```(?:json)?\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\[\s*\{[\s\S]*\}\s*\]',  # JSON array pattern
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1) if match.groups() else match.group(0)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # Last resort: find first [ and last ]
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass

        raise ValueError("Could not extract valid JSON from Gemini response")

    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call Gemini API with exponential backoff."""
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=8192,
                    )
                )
                return response.text
            except Exception as e:
                wait_time = (2 ** attempt) + 1
                print(f"   ⚠️  Gemini attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

        raise Exception("Gemini API failed after all retries")

    def analyze_articles_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Send articles to Gemini for analysis. Returns enriched articles.
        If Gemini fails, returns original articles with fallback tags.
        """
        if not self.enabled or not articles:
            # Fallback: use keyword classification logic
            return self._fallback_classify(articles)

        enriched = []
        # Process in batches
        for i in range(0, len(articles), GEMINI_BATCH_SIZE):
            batch = articles[i:i + GEMINI_BATCH_SIZE]
            batch_indices = list(range(i, min(i + GEMINI_BATCH_SIZE, len(articles))))

            try:
                prompt = self._build_prompt(batch)
                print(f"   🧠 Analyzing batch {i//GEMINI_BATCH_SIZE + 1}/{(len(articles)-1)//GEMINI_BATCH_SIZE + 1} ({len(batch)} articles)...")

                response_text = self._call_gemini_with_retry(prompt)
                results = self._extract_json(response_text)

                if len(results) != len(batch):
                    print(f"   ⚠️  Gemini returned {len(results)} results for {len(batch)} articles. Using fallback for mismatch.")
                    raise ValueError("Batch size mismatch")

                for idx, result in enumerate(results):
                    original = batch[idx]
                    if not result.get("should_include", True):
                        print(f"   ✗ Gemini filtered: {original['title'][:50]}...")
                        continue

                    enriched_art = {
                        **original,
                        "gs_paper": result.get("gs_paper", "General"),
                        "sub_topic": result.get("sub_topic", "General Current Affairs"),
                        "syllabus_tag": result.get("syllabus_tag", ""),
                        "relevance_score": result.get("relevance_score", 5),
                        "key_bullets": result.get("key_bullets", []),
                        "quick_note": result.get("quick_note", ""),
                        "keywords": result.get("keywords", []),
                        "prelims_angle": result.get("prelims_angle", ""),
                        "mains_angle": result.get("mains_angle", ""),
                        "gemini_processed": True,
                        "gs_color": self.GS_COLORS.get(result.get("gs_paper", "General"), "#455a64")
                    }
                    enriched.append(enriched_art)
                    print(f"   ✓ [{enriched_art['gs_paper']}] {enriched_art['title'][:50]}... (Score: {enriched_art['relevance_score']})")

                # Rate limit courtesy
                time.sleep(1.5)

            except Exception as e:
                print(f"   ❌ Gemini batch failed: {e}. Using fallback for {len(batch)} articles.")
                fallback_results = self._fallback_classify(batch)
                enriched.extend(fallback_results)

        return enriched

    def _fallback_classify(self, articles: List[Dict]) -> List[Dict]:
        """Keyword-based fallback when Gemini is unavailable."""
        from ai_scraper import AIExamNewsScraper
        scraper = AIExamNewsScraper()
        results = []

        for art in articles:
            result = scraper._classify_article(art["title"], art["text"])
            if not result["is_exam_relevant"]:
                continue

            gs_paper = self._map_topic_to_gs(result["topic"])
            results.append({
                **art,
                "gs_paper": gs_paper,
                "sub_topic": result["topic"].replace("🏛️ ", "").replace("💰 ", "").replace("🌍 ", "").replace("🛡️ ", "").replace("🔬 ", "").replace("🌿 ", "").replace("👥 ", "").replace("📜 ", "").replace("⚖️ ", "").replace("🏗️ ", ""),
                "syllabus_tag": f"{gs_paper} - {result['topic']}",
                "relevance_score": result["score"],
                "key_bullets": [art["text"][:200] + "..."] if art["text"] else [],
                "quick_note": art["text"][:300] if art["text"] else "",
                "keywords": [],
                "prelims_angle": "",
                "mains_angle": "",
                "gemini_processed": False,
                "gs_color": self.GS_COLORS.get(gs_paper, "#455a64")
            })

        return results

    def _map_topic_to_gs(self, topic: str) -> str:
        """Map fallback topic to GS Paper."""
        topic_lower = topic.lower()
        if "polity" in topic_lower or "governance" in topic_lower:
            return "GS2"
        elif "economy" in topic_lower or "finance" in topic_lower:
            return "GS3"
        elif "international" in topic_lower:
            return "GS2"
        elif "defence" in topic_lower or "security" in topic_lower:
            return "GS3"
        elif "science" in topic_lower or "technology" in topic_lower:
            return "GS3"
        elif "environment" in topic_lower or "ecology" in topic_lower:
            return "GS3"
        elif "social" in topic_lower:
            return "GS1"
        elif "history" in topic_lower or "culture" in topic_lower:
            return "GS1"
        elif "law" in topic_lower or "judiciary" in topic_lower:
            return "GS2"
        elif "infrastructure" in topic_lower:
            return "GS3"
        return "General"
