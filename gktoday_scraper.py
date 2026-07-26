"""
Dedicated GKToday scraper — newspaper3k doesn't handle GKToday's structure well.
"""

import requests
import time
import random
import re
from datetime import datetime
from typing import List, Dict
from bs4 import BeautifulSoup


class GKTodayScraper:
    """
    Custom scraper for GKToday current affairs articles.
    """

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _clean_text(self, text: str) -> str:
        """Remove social media junk and ads."""
        if not text:
            return ""

        junk_patterns = [
            r"Share this:.*?(?=\n|$)",
            r"Click to share on.*?(?=\n|$)",
            r"Categories:.*?(?=\n|$)",
            r"Tags:.*?(?=\n|$)",
            r"Posted by.*?(?=\n|$)",
            r"Follow us on.*?(?=\n|$)",
            r"Subscribe to.*?(?=\n|$)",
            r"Advertisement\s+",
            r"Also Read:.*?(?=\n|$)",
            r"^Related Posts.*",
            r"^You Might Also Like.*",
        ]

        for pattern in junk_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

        text = re.sub(r"\n\s*\n+", "\n\n", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        return text.strip()

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publish date from GKToday article."""
        # Try multiple selectors
        selectors = [
            'time.entry-date',
            '.published',
            '.post-date',
            'span.date',
            '.entry-meta time'
        ]

        for sel in selectors:
            elem = soup.select_one(sel)
            if elem:
                date_text = elem.get_text(strip=True)
                # Try to parse
                try:
                    # Common formats: "January 15, 2024" or "2024-01-15"
                    for fmt in ["%B %d, %Y", "%Y-%m-%d", "%d %B %Y"]:
                        try:
                            dt = datetime.strptime(date_text, fmt)
                            return dt.strftime("%Y-%m-%d")
                        except:
                            continue
                except:
                    pass
                return date_text

        return datetime.now().strftime("%Y-%m-%d")

    def scrape(self, max_articles: int = 15) -> List[Dict]:
        """
        Scrape GKToday current affairs articles.
        """
        articles = []
        base_url = "https://www.gktoday.in/current-affairs/"

        try:
            print(f"[GKToday] Fetching article list...")
            resp = self.session.get(base_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')

            # Find article links — GKToday uses .post-title or h2 > a
            article_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/current-affairs/' in href and href != base_url:
                    # Ensure full URL
                    if href.startswith('/'):
                        href = f"https://www.gktoday.in{href}"
                    elif not href.startswith('http'):
                        href = f"https://www.gktoday.in/{href}"
                    article_links.append(href)

            # Deduplicate and limit
            article_links = list(dict.fromkeys(article_links))[:max_articles * 2]

            print(f"[GKToday] Found {len(article_links)} article links")

            for url in article_links[:max_articles]:
                try:
                    time.sleep(random.uniform(0.5, 1.0))
                    art_resp = self.session.get(url, timeout=30)
                    art_resp.raise_for_status()
                    art_soup = BeautifulSoup(art_resp.text, 'lxml')

                    # Extract title
                    title_elem = art_soup.find('h1') or art_soup.select_one('.entry-title') or art_soup.select_one('h2')
                    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

                    # Skip non-article pages
                    if any(x in title.lower() for x in ["archive", "category", "tag", "page not found"]):
                        continue

                    # Extract content
                    content_elem = (
                        art_soup.select_one('.entry-content') or
                        art_soup.select_one('.post-content') or
                        art_soup.select_one('article') or
                        art_soup.select_one('.content-area')
                    )

                    if not content_elem:
                        continue

                    # Remove script, style, nav, footer
                    for tag in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                        tag.decompose()

                    text = content_elem.get_text(separator='\n', strip=True)
                    text = self._clean_text(text)

                    if len(text) < 300:
                        continue

                    date = self._extract_date(art_soup)

                    articles.append({
                        "title": title,
                        "text": text,
                        "url": url,
                        "source": "GKToday",
                        "publish_date": date,
                        "authors": "GKToday Editorial",
                        "language": "en"
                    })
                    print(f"  ✓ {title[:55]}...")

                except Exception as e:
                    print(f"  ✗ Failed: {url[:60]}... ({e})")
                    continue

        except Exception as e:
            print(f"[GKToday] Error: {e}")

        print(f"[GKToday] Kept {len(articles)} articles")
        return articles
