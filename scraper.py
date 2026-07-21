"""
Scraping module using newspaper3k and BeautifulSoup as fallback.
"""

import newspaper
from newspaper import Article, Config
import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict
from config import NEWSPAPER_CONFIG, MAX_ARTICLES_PER_SOURCE


class NewspaperScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.0'
        ]
        
    def _get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def scrape_with_newspaper3k(self, source_name: str, url: str, 
                                 max_articles: int = 5, 
                                 language: str = "en") -> List[Dict]:
        """
        Scrape articles using newspaper3k library.
        """
        articles_data = []
        
        try:
            # Configure newspaper3k
            config = Config()
            config.browser_user_agent = random.choice(self.user_agents)
            config.request_timeout = 30
            
            # Build the paper
            paper = newspaper.build(url, config=config, memoize_articles=False)
            
            print(f"[{source_name}] Found {len(paper.articles)} articles")
            
            # Get top articles
            target_articles = paper.articles[:max_articles]
            
            for article in target_articles:
                try:
                    article.download()
                    article.parse()
                    
                    # Skip if no content
                    if not article.text or len(article.text) < 100:
                        continue
                    
                    articles_data.append({
                        "title": article.title or "Untitled",
                        "text": article.text,
                        "url": article.url,
                        "source": source_name,
                        "publish_date": str(article.publish_date) if article.publish_date else "Unknown",
                        "authors": ", ".join(article.authors) if article.authors else "Unknown"
                    })
                    
                    print(f"  ✓ Scraped: {article.title[:60]}...")
                    time.sleep(random.uniform(1, 2))  # Be polite
                    
                except Exception as e:
                    print(f"  ✗ Error scraping article: {e}")
                    continue
                    
        except Exception as e:
            print(f"[{source_name}] Error building paper: {e}")
            
        return articles_data

    def scrape_with_beautifulsoup(self, source_name: str, url: str) -> List[Dict]:
        """
        Fallback scraping using BeautifulSoup for sites that don't work well with newspaper3k.
        """
        articles_data = []
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find article links (common patterns)
            article_links = []
            
            # Try different selectors for article links
            selectors = [
                'a[href*="/article/"]', 'a[href*="/news/"]',
                'a[href*="/story/"]', 'h2 a', 'h3 a',
                '.article-title a', '.story-title a',
                '[class*="headline"] a', '[class*="title"] a'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if href and href.startswith('http'):
                        article_links.append((link.get_text(strip=True), href))
            
            # Remove duplicates
            seen = set()
            unique_links = []
            for title, href in article_links:
                if href not in seen and title and len(title) > 10:
                    seen.add(href)
                    unique_links.append((title, href))
            
            print(f"[{source_name}] Found {len(unique_links)} article links via BS4")
            
            # Scrape top articles
            for title, article_url in unique_links[:MAX_ARTICLES_PER_SOURCE]:
                try:
                    resp = requests.get(article_url, headers=self._get_headers(), timeout=30)
                    article_soup = BeautifulSoup(resp.content, 'lxml')
                    
                    # Extract text from common content containers
                    text = ""
                    for tag in ['article', 'div[class*="content"]', 'div[class*="article"]', 
                                '.story-content', '#article-content', 'main']:
                        content = article_soup.select_one(tag)
                        if content:
                            paragraphs = content.find_all('p')
                            text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                            if len(text) > 200:
                                break
                    
                    if text and len(text) > 100:
                        articles_data.append({
                            "title": title,
                            "text": text,
                            "url": article_url,
                            "source": source_name,
                            "publish_date": "Unknown",
                            "authors": "Unknown"
                        })
                        print(f"  ✓ Scraped: {title[:60]}...")
                        
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    continue
                    
        except Exception as e:
            print(f"[{source_name}] BS4 scraping failed: {e}")
            
        return articles_data

    def scrape_all(self) -> Dict[str, List[Dict]]:
        """
        Scrape all configured newspapers.
        """
        all_articles = {}
        
        for source_name, config in NEWSPAPER_CONFIG.items():
            print(f"\n{'='*50}")
            print(f"Scraping: {source_name}")
            print(f"{'='*50}")
            
            # Try newspaper3k first
            articles = self.scrape_with_newspaper3k(
                source_name,
                config["url"],
                config.get("max_articles", MAX_ARTICLES_PER_SOURCE),
                config.get("language", "en")
            )
            
            # Fallback to BeautifulSoup if no articles found
            if not articles:
                print(f"[{source_name}] Falling back to BeautifulSoup...")
                articles = self.scrape_with_beautifulsoup(source_name, config["url"])
            
            all_articles[source_name] = articles
            print(f"[{source_name}] Total articles scraped: {len(articles)}")
            
        return all_articles
      
