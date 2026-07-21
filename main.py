#!/usr/bin/env python3
"""
Newspaper Scraper Bot - Main Entry Point

Scrapes Indian newspapers, combines into PDF, and sends to Telegram.
"""

import os
import sys
import argparse
from datetime import datetime

# Ensure NLTK data is available
try:
    import nltk
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK punkt data...")
    nltk.download('punkt', quiet=True)

from scraper import NewspaperScraper
from pdf_generator import PDFGenerator
from telegram_sender import TelegramSender
from config import PDF_OUTPUT_PATH, PDF_TITLE


def main():
    parser = argparse.ArgumentParser(description='Newspaper Scraper Bot')
    parser.add_argument('--pdf-only', action='store_true', 
                        help='Only generate PDF, do not send to Telegram')
    parser.add_argument('--send-only', action='store_true',
                        help='Only send existing PDF to Telegram')
    parser.add_argument('--output', type=str, default=PDF_OUTPUT_PATH,
                        help='Output PDF path')
    args = parser.parse_args()
    
    print("=" * 60)
    print("   📰 INDIAN NEWSPAPER SCRAPER BOT")
    print("=" * 60)
    
    # ─── Send Only Mode ─────────────────────────────────────────────
    if args.send_only:
        if not os.path.exists(args.output):
            print(f"❌ PDF not found: {args.output}")
            sys.exit(1)
        
        print("\n📤 Sending existing PDF to Telegram...")
        sender = TelegramSender()
        sender.send_pdf_sync(args.output)
        return
    
    # ─── Scrape Articles ────────────────────────────────────────────
    print("\n🔍 Starting scraping process...")
    scraper = NewspaperScraper()
    articles = scraper.scrape_all()
    
    total_articles = sum(len(v) for v in articles.values())
    if total_articles == 0:
        print("\n❌ No articles scraped. Check your internet connection and URLs.")
        sys.exit(1)
    
    print(f"\n📊 Scraping Summary:")
    for source, arts in articles.items():
        print(f"   • {source}: {len(arts)} articles")
    print(f"   Total: {total_articles} articles")
    
    # ─── Generate PDF ───────────────────────────────────────────────
    print(f"\n📝 Generating PDF...")
    pdf_gen = PDFGenerator(output_path=args.output)
    pdf_path = pdf_gen.generate(articles, title=PDF_TITLE)
    
    # ─── Send to Telegram ───────────────────────────────────────────
    if not args.pdf_only:
        print("\n📤 Sending PDF to Telegram...")
        sender = TelegramSender()
        success = sender.send_pdf_sync(pdf_path)
        
        if not success:
            print("\n⚠️  PDF saved locally but failed to send to Telegram.")
            print(f"   File location: {os.path.abspath(pdf_path)}")
    else:
        print(f"\n📄 PDF saved to: {os.path.abspath(pdf_path)}")
    
    print("\n" + "=" * 60)
    print("   ✅ Process Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
  
