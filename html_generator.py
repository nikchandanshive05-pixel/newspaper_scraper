"""
Beautiful, self-contained HTML notes generator for UPSC revision.
Print-ready, mobile-friendly, and Telegram-shareable.
"""

import os
import re
from datetime import datetime
from typing import Dict, List
from html import escape


class HTMLNotesGenerator:
    """
    Generates professional HTML revision notes with GS Paper color coding.
    """

    GS_COLORS = {
        "GS1": "#c62828",
        "GS2": "#1565c0",
        "GS3": "#2e7d32",
        "GS4": "#6a1b9a",
        "Essay": "#e65100",
        "General": "#455a64",
        "Skip": "#757575"
    }

    def __init__(self, output_path: str = "daily_exam_notes.html"):
        self.output_path = output_path

    def _escape(self, text: str) -> str:
        if not text:
            return ""
        return escape(str(text))

    def _truncate_url(self, url: str, max_len: int = 80) -> str:
        if len(url) <= max_len:
            return url
        return url[:max_len-3] + "..."

    def _render_bullets(self, bullets: List[str]) -> str:
        if not bullets:
            return '<p class="no-bullets">No key points extracted.</p>'
        items = "".join(f'<li>{self._escape(b)}</li>' for b in bullets if b)
        return f'<ul class="key-bullets">{items}</ul>'

    def _render_keywords(self, keywords: List[str]) -> str:
        if not keywords:
            return ""
        tags = "".join(f'<span class="keyword-tag">{self._escape(k)}</span>' for k in keywords[:12] if k)
        return f'<div class="keywords">{tags}</div>'

    def generate(self, categorized_articles: Dict[str, List[dict]],
                 title: str = "UPSC Daily Exam Notes") -> str:
        """
        Generate a complete, self-contained HTML file.
        """
        total_articles = sum(len(v) for v in categorized_articles.values())
        today = datetime.now().strftime("%A, %B %d, %Y")

        # Build topic sections
        topic_sections = []
        toc_items = []
        topic_index = 0

        # Collect all prelims and mains angles for summary sections
        all_prelims = []
        all_mains = []

        for topic_key in sorted(categorized_articles.keys()):
            articles = categorized_articles[topic_key]
            if not articles:
                continue

            topic_index += 1
            gs_paper = articles[0].get("gs_paper", "General")
            color = self.GS_COLORS.get(gs_paper, "#455a64")

            toc_items.append(
                f'<a href="#topic-{topic_index}" class="toc-item" style="border-left-color: {color}">'
                f'<span class="toc-gs" style="background: {color}">{gs_paper}</span>'
                f'<span class="toc-name">{self._escape(topic_key)}</span>'
                f'<span class="toc-count">{len(articles)}</span></a>'
            )

            article_cards = []
            for i, art in enumerate(articles, 1):
                # Collect exam angles
                if art.get("prelims_angle"):
                    all_prelims.append({
                        "angle": art["prelims_angle"],
                        "topic": topic_key,
                        "title": art.get("title", "")
                    })
                if art.get("mains_angle"):
                    all_mains.append({
                        "angle": art["mains_angle"],
                        "topic": topic_key,
                        "title": art.get("title", "")
                    })

                art_color = art.get("gs_color", color)
                bullets = self._render_bullets(art.get("key_bullets", []))
                keywords = self._render_keywords(art.get("keywords", []))
                quick_note = art.get("quick_note", "")
                prelims = art.get("prelims_angle", "")
                mains = art.get("mains_angle", "")
                syllabus = art.get("syllabus_tag", "")
                score = art.get("relevance_score", 5)
                gemini_badge = "🤖 AI" if art.get("gemini_processed") else "🔑 Keyword"

                card_html = f'''
                <div class="article-card" style="border-left-color: {art_color}">
                    <div class="card-header">
                        <div class="card-badges">
                            <span class="gs-badge" style="background: {art_color}">{gs_paper}</span>
                            <span class="score-badge">⭐ {score}/10</span>
                            <span class="ai-badge">{gemini_badge}</span>
                        </div>
                        <div class="article-number">#{i}</div>
                    </div>
                    
                    <h3 class="article-title">{self._escape(art.get("title", "Untitled"))}</h3>
                    
                    {f'<div class="syllabus-tag">📋 {self._escape(syllabus)}</div>' if syllabus else ''}
                    
                    <div class="quick-note">
                        <div class="section-label">📝 Quick Revision Note</div>
                        <p>{self._escape(quick_note) if quick_note else "No summary available."}</p>
                    </div>
                    
                    <div class="key-points">
                        <div class="section-label">🔑 Key Points</div>
                        {bullets}
                    </div>
                    
                    {keywords}
                    
                    <div class="exam-angles">
                        {f'<div class="prelims-box"><div class="angle-label">🎯 Prelims Angle</div><p>{self._escape(prelims)}</p></div>' if prelims else ''}
                        {f'<div class="mains-box"><div class="angle-label">✍️ Mains Angle</div><p>{self._escape(mains)}</p></div>' if mains else ''}
                    </div>
                    
                    <div class="card-footer">
                        <span class="source">📰 {self._escape(art.get("source", ""))}</span>
                        <span class="date">📅 {self._escape(art.get("publish_date", "Today"))}</span>
                        <a href="{art.get("url", "#")}" class="source-link" target="_blank">🔗 {self._truncate_url(art.get("url", ""))}</a>
                    </div>
                </div>
                '''

                article_cards.append(card_html)

            section_html = f'''
            <section class="topic-section" id="topic-{topic_index}">
                <div class="topic-header" style="background: {color};">
                    <span class="topic-icon">{'🏛️' if gs_paper == 'GS2' else '💰' if gs_paper == 'GS3' else '🌍' if 'International' in topic_key else '🛡️' if 'Defence' in topic_key else '🔬' if 'Science' in topic_key else '🌿' if 'Environment' in topic_key else '👥' if 'Social' in topic_key else '📜' if 'History' in topic_key else '⚖️' if 'Law' in topic_key else '🏗️' if 'Infrastructure' in topic_key else '📰'}</span>
                    <h2>{self._escape(topic_key)}</h2>
                    <span class="topic-count">{len(articles)} articles</span>
                </div>
                <div class="articles-container">
                    {''.join(article_cards)}
                </div>
            </section>
            '''
            topic_sections.append(section_html)

        # Prelims Quick Facts section
        prelims_html = ""
        if all_prelims:
            prelims_items = "".join(
                f'<div class="fact-item"><span class="fact-topic">{self._escape(p["topic"].split("—")[-1].strip()[:30])}</span>'
                f'<p>{self._escape(p["angle"])}</p></div>'
                for p in all_prelims[:30]
            )
            prelims_html = f'''
            <section class="summary-section" id="prelims-facts">
                <h2>🎯 Prelims Quick Facts</h2>
                <div class="facts-grid">
                    {prelims_items}
                </div>
            </section>
            '''

        # Mains Questions section
        mains_html = ""
        if all_mains:
            mains_items = "".join(
                f'<div class="question-item"><span class="q-topic">{self._escape(m["topic"].split("—")[-1].strip()[:30])}</span>'
                f'<p>{self._escape(m["angle"])}</p></div>'
                for m in all_mains[:25]
            )
            mains_html = f'''
            <section class="summary-section" id="mains-questions">
                <h2>✍️ Mains Question Bank</h2>
                <div class="questions-list">
                    {mains_items}
                </div>
            </section>
            '''

        # Build full HTML
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape(title)} — {today}</title>
    <style>
        /* ─── RESET & BASE ───────────────────────────────────── */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #f0f2f5;
            color: #1a1a2e;
            line-height: 1.6;
            padding: 0;
        }}

        /* ─── COVER PAGE ─────────────────────────────────────── */
        .cover {{
            background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
            color: white;
            padding: 50px 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .cover::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 600px;
            height: 600px;
            background: rgba(255,255,255,0.03);
            border-radius: 50%;
        }}
        .cover h1 {{
            font-size: 2.4rem;
            font-weight: 800;
            margin-bottom: 10px;
            letter-spacing: -0.5px;
        }}
        .cover .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            margin-bottom: 20px;
        }}
        .cover .meta {{
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-top: 25px;
            font-size: 0.95rem;
        }}
        .cover .meta span {{
            background: rgba(255,255,255,0.15);
            padding: 8px 18px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }}

        /* ─── TABLE OF CONTENTS ─────────────────────────────── */
        .toc-section {{
            background: white;
            margin: 30px auto;
            max-width: 900px;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }}
        .toc-section h2 {{
            color: #1a237e;
            font-size: 1.4rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #1a237e;
        }}
        .toc-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 12px;
        }}
        .toc-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            background: #f8f9fa;
            border-radius: 10px;
            text-decoration: none;
            color: inherit;
            border-left: 4px solid;
            transition: all 0.2s;
        }}
        .toc-item:hover {{
            background: #e8eaf6;
            transform: translateX(4px);
        }}
        .toc-gs {{
            color: white;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            min-width: 36px;
            text-align: center;
        }}
        .toc-name {{
            flex: 1;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        .toc-count {{
            background: #1a237e;
            color: white;
            font-size: 0.75rem;
            padding: 2px 10px;
            border-radius: 12px;
        }}

        /* ─── TOPIC SECTIONS ───────────────────────────────── */
        .topic-section {{
            max-width: 900px;
            margin: 30px auto;
        }}
        .topic-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px 24px;
            color: white;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .topic-header h2 {{
            font-size: 1.3rem;
            font-weight: 700;
            flex: 1;
        }}
        .topic-icon {{ font-size: 1.5rem; }}
        .topic-count {{
            background: rgba(255,255,255,0.2);
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
        }}

        /* ─── ARTICLE CARDS ──────────────────────────────────── */
        .articles-container {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .article-card {{
            background: white;
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-left: 5px solid;
            transition: box-shadow 0.2s;
        }}
        .article-card:hover {{
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .card-badges {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .gs-badge {{
            color: white;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 6px;
        }}
        .score-badge {{
            background: #fff3e0;
            color: #e65100;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
        }}
        .ai-badge {{
            background: #e8f5e9;
            color: #2e7d32;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
        }}
        .article-number {{
            font-size: 1.5rem;
            font-weight: 800;
            color: #e0e0e0;
        }}
        .article-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: #1a237e;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        .syllabus-tag {{
            background: #e8eaf6;
            color: #1a237e;
            font-size: 0.8rem;
            padding: 6px 14px;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 14px;
            font-weight: 600;
        }}

        /* ─── CONTENT SECTIONS ───────────────────────────────── */
        .section-label {{
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #666;
            margin-bottom: 8px;
        }}
        .quick-note {{
            background: #fff8e1;
            border-left: 3px solid #ffc107;
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 16px;
        }}
        .quick-note p {{
            font-size: 0.95rem;
            color: #5d4037;
            line-height: 1.6;
        }}
        .key-points {{
            margin-bottom: 16px;
        }}
        .key-bullets {{
            list-style: none;
            padding: 0;
        }}
        .key-bullets li {{
            padding: 8px 0 8px 28px;
            position: relative;
            border-bottom: 1px solid #f0f0f0;
            font-size: 0.92rem;
            line-height: 1.5;
        }}
        .key-bullets li:last-child {{ border-bottom: none; }}
        .key-bullets li::before {{
            content: '▸';
            position: absolute;
            left: 0;
            color: #1a237e;
            font-weight: bold;
            font-size: 1.1rem;
        }}
        .no-bullets {{
            color: #999;
            font-style: italic;
            padding: 10px;
        }}

        /* ─── KEYWORDS ───────────────────────────────────────── */
        .keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 16px;
        }}
        .keyword-tag {{
            background: #e3f2fd;
            color: #1565c0;
            font-size: 0.78rem;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
        }}

        /* ─── EXAM ANGLES ────────────────────────────────────── */
        .exam-angles {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
            margin-bottom: 16px;
        }}
        @media (min-width: 600px) {{
            .exam-angles {{ grid-template-columns: 1fr 1fr; }}
        }}
        .prelims-box {{
            background: #e8f5e9;
            border-left: 3px solid #4caf50;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
        }}
        .mains-box {{
            background: #fce4ec;
            border-left: 3px solid #e91e63;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
        }}
        .angle-label {{
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 6px;
        }}
        .prelims-box .angle-label {{ color: #2e7d32; }}
        .mains-box .angle-label {{ color: #c62828; }}
        .exam-angles p {{
            font-size: 0.9rem;
            color: #444;
            line-height: 1.5;
        }}

        /* ─── CARD FOOTER ────────────────────────────────────── */
        .card-footer {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
            padding-top: 14px;
            border-top: 1px solid #eee;
            font-size: 0.82rem;
            color: #666;
        }}
        .source-link {{
            color: #1565c0;
            text-decoration: none;
            font-weight: 600;
            word-break: break-all;
        }}
        .source-link:hover {{ text-decoration: underline; }}

        /* ─── SUMMARY SECTIONS ───────────────────────────────── */
        .summary-section {{
            max-width: 900px;
            margin: 30px auto;
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }}
        .summary-section h2 {{
            color: #1a237e;
            font-size: 1.3rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #1a237e;
        }}
        .facts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 14px;
        }}
        .fact-item, .question-item {{
            background: #f8f9fa;
            padding: 14px 18px;
            border-radius: 10px;
            border-left: 3px solid #4caf50;
        }}
        .question-item {{ border-left-color: #e91e63; }}
        .fact-topic, .q-topic {{
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 6px;
            display: block;
        }}
        .fact-item p, .question-item p {{
            font-size: 0.9rem;
            color: #333;
            line-height: 1.5;
        }}

        /* ─── FOOTER ─────────────────────────────────────────── */
        .page-footer {{
            text-align: center;
            padding: 30px;
            color: #888;
            font-size: 0.85rem;
            max-width: 900px;
            margin: 0 auto;
        }}

        /* ─── PRINT STYLES ───────────────────────────────────── */
        @media print {{
            body {{ background: white; }}
            .cover {{ padding: 30px; }}
            .article-card {{
                box-shadow: none;
                border: 1px solid #ddd;
                page-break-inside: avoid;
            }}
            .topic-section {{ page-break-before: always; }}
            .topic-section:first-child {{ page-break-before: auto; }}
            .toc-item {{ text-decoration: none; color: inherit; }}
            a {{ text-decoration: none; color: #333; }}
            .source-link {{ color: #333; }}
        }}

        /* ─── MOBILE ─────────────────────────────────────────── */
        @media (max-width: 600px) {{
            .cover h1 {{ font-size: 1.6rem; }}
            .cover .meta {{ gap: 10px; }}
            .toc-grid {{ grid-template-columns: 1fr; }}
            .article-card {{ padding: 16px; }}
            .exam-angles {{ grid-template-columns: 1fr; }}
            .card-footer {{ flex-direction: column; align-items: flex-start; }}
        }}
    </style>
</head>
<body>

    <!-- COVER -->
    <div class="cover">
        <h1>{self._escape(title)}</h1>
        <div class="subtitle">UPSC CSE · MPSC · State PCS · SSC · Banking</div>
        <div class="meta">
            <span>📅 {today}</span>
            <span>📊 {total_articles} Articles</span>
            <span>🤖 Gemini 1.5 Pro</span>
            <span>📑 {len(categorized_articles)} Topics</span>
        </div>
    </div>

    <!-- TABLE OF CONTENTS -->
    <div class="toc-section">
        <h2>📑 Topics Covered</h2>
        <div class="toc-grid">
            {''.join(toc_items)}
        </div>
    </div>

    <!-- PRELIMS QUICK FACTS -->
    {prelims_html}

    <!-- MAINS QUESTIONS -->
    {mains_html}

    <!-- ARTICLES BY TOPIC -->
    {''.join(topic_sections)}

    <!-- FOOTER -->
    <div class="page-footer">
        <p>Generated on {today} · Gemini 1.5 Pro + AI Scraper · For Educational Use Only</p>
        <p>Sources: The Hindu, Indian Express, GKToday, Lokmat, Loksatta, eSakal</p>
    </div>

</body>
</html>'''

        # Write file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✅ HTML Notes generated: {os.path.abspath(self.output_path)}")
        print(f"   📊 {total_articles} articles across {len(categorized_articles)} topics")
        return self.output_path
