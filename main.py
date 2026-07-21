#!/usr/bin/env python3
"""
Competitive Exam Daily News Digest
Scrapes The Hindu, Indian Express, and Marathi papers
Filters by exam-relevant topics, generates clean PDF, sends to Telegram.
"""

import os
import sys
import argparse
import asyncio
import re
from datetime import datetime
from collections import defaultdict

# Ensure NLTK data
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

from ai_scraper import AIExamNewsScraper
from pdf_generator import ExamPDFGenerator
from telegram_sender import TelegramSender
from config import PDF_OUTPUT_PATH, PDF_TITLE


def main():
    parser = argparse.ArgumentParser(description='Competitive Exam News Digest')
    parser.add_argument('--pdf-only', action='store_true', help='Only generate PDF')
    parser.add_argument('--send-only', action='store_true', help='Only send existing PDF')
    parser.add_argument('--output', type=str, default=PDF_OUTPUT_PATH)
    args = parser.parse_args()

    print("=" * 65)
    print("   📰 COMPETITIVE EXAM DAILY NEWS DIGEST")
    print("   UPSC | MPSC | SSC | Banking | RBI | NDA")
    print("=" * 65)

    if args.send_only:
        if not os.path.exists(args.output):
            print(f"❌ PDF not found: {args.output}")
            sys.exit(1)
        sender = TelegramSender()
        sender.send_pdf_sync(args.output)
        return

    # Scrape
    print("\n🔍 Scraping & filtering exam-relevant articles...")
    scraper = ExamNewsScraper()
    categorized_articles = scraper.scrape_all()

    total = sum(len(v) for v in categorized_articles.values())
    if total == 0:
        print("❌ No relevant articles found.")
        sys.exit(1)

    print(f"\n📊 Summary:")
    for topic, arts in sorted(categorized_articles.items()):
        print(f"   • {topic}: {len(arts)} articles")
    print(f"   Total: {total} articles")

    # Generate PDF
    print(f"\n📝 Generating clean PDF...")
    pdf_gen = ExamPDFGenerator(output_path=args.output)
    pdf_path = pdf_gen.generate(categorized_articles, title=PDF_TITLE)

    # Send to Telegram
    if not args.pdf_only:
        print("\n📤 Sending to Telegram...")
        sender = TelegramSender()
        success = sender.send_pdf_sync(pdf_path)
        if not success:
            print(f"\n⚠️  PDF saved: {os.path.abspath(pdf_path)}")
    else:
        print(f"\n📄 PDF saved: {os.path.abspath(pdf_path)}")

    print("\n" + "=" * 65)
    print("   ✅ Done!")
    print("=" * 65)


if __name__ == "__main__":
    main()
