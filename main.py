#!/usr/bin/env python3
"""
Competitive Exam Daily Notes — AI-Powered
"""

import os
import sys
import argparse
from datetime import datetime

import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

from ai_scraper import AIExamNewsScraper
from html_generator import HTMLNotesGenerator
from telegram_sender import TelegramSender
from config import HTML_OUTPUT_PATH, NOTES_TITLE


def main():
    parser = argparse.ArgumentParser(description='AI-Powered Exam Daily Notes')
    parser.add_argument('--html-only', action='store_true', help='Only generate HTML')
    parser.add_argument('--send-only', action='store_true', help='Only send existing HTML')
    parser.add_argument('--output', type=str, default=HTML_OUTPUT_PATH)
    parser.add_argument('--title', type=str, default=NOTES_TITLE)
    args = parser.parse_args()

    print("=" * 65)
    print("   📰 AI-POWERED EXAM DAILY NOTES")
    print("   Gemini 1.5 Pro · Structured Notes · HTML Output")
    print("=" * 65)

    if args.send_only:
        if not os.path.exists(args.output):
            print(f"❌ HTML not found: {args.output}")
            sys.exit(1)
        sender = TelegramSender()
        sender.send_file_sync(args.output, filename=args.output.split('/')[-1])
        return

    # Scrape + AI Analysis
    print("\n🔍 Scraping & analyzing...")
    scraper = AIExamNewsScraper()
    categorized = scraper.scrape_all()

    total = sum(len(v) for v in categorized.values())
    if total == 0:
        print("❌ No relevant articles found.")
        sys.exit(1)

    gemini_count = sum(1 for arts in categorized.values() for a in arts if a.get("gemini_processed"))

    print(f"\n📊 Summary:")
    for topic, arts in sorted(categorized.items()):
        g = sum(1 for a in arts if a.get("gemini_processed"))
        print(f"   • {topic}: {len(arts)} articles ({g} AI)")
    print(f"   Total: {total} | AI-analyzed: {gemini_count}")

    # Generate HTML
    print(f"\n📝 Generating HTML notes...")
    html_gen = HTMLNotesGenerator(output_path=args.output)
    html_path = html_gen.generate(categorized, title=args.title)

    # Telegram
    if not args.html_only:
        print("\n📤 Sending to Telegram...")
        sender = TelegramSender()

        gs_counts = {}
        for arts in categorized.values():
            gs = arts[0].get("gs_paper", "General") if arts else "General"
            gs_counts[gs] = gs_counts.get(gs, 0) + len(arts)

        stats = " | ".join([f"{gs}: {cnt}" for gs, cnt in sorted(gs_counts.items())])
        caption = (
            f"📰 <b>{args.title}</b>\n"
            f"📅 {datetime.now().strftime('%B %d, %Y')}\n"
            f"📊 {total} articles | 🤖 {gemini_count} AI-analyzed\n"
            f"🗂️ {stats}\n\n"
            f"<i>Open in browser for best reading experience</i>"
        )
        sender.send_file_sync(html_path, caption=caption, filename=html_path.split('/')[-1])

    print("\n" + "=" * 65)
    print("   ✅ Done!")
    print("=" * 65)


if __name__ == "__main__":
    main()
