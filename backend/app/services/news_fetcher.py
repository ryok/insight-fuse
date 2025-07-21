import httpx
import feedparser
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.db import models
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class NewsFetcher:
    def __init__(self, db: Session):
        self.db = db
        self.news_api_key = settings.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2"
        
    async def fetch_all_sources(self):
        fetch_history = models.FetchHistory(
            source="all",
            status="started",
            article_count=0
        )
        self.db.add(fetch_history)
        self.db.commit()
        
        total_articles = 0
        errors = []
        
        try:
            if self.news_api_key:
                articles = await self.fetch_from_newsapi()
                total_articles += len(articles)
            
            rss_articles = await self.fetch_from_rss_feeds()
            total_articles += len(rss_articles)
            
            fetch_history.status = "success"
            fetch_history.article_count = total_articles
            
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            fetch_history.status = "failed"
            fetch_history.error_message = str(e)
            errors.append(str(e))
        
        self.db.commit()
        
    async def fetch_from_newsapi(self) -> List[Dict]:
        articles = []
        
        async with httpx.AsyncClient() as client:
            for source in settings.news_sources_list:
                try:
                    response = await client.get(
                        f"{self.base_url}/everything",
                        params={
                            "sources": source,
                            "apiKey": self.news_api_key,
                            "pageSize": settings.NEWS_FETCH_LIMIT,
                            "sortBy": "publishedAt"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        for article_data in data.get("articles", []):
                            article = self._process_newsapi_article(article_data, source)
                            if article:
                                self._save_article(article)
                                articles.append(article)
                    else:
                        logger.error(f"Error fetching from {source}: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Error fetching from {source}: {str(e)}")
        
        return articles
    
    async def fetch_from_rss_feeds(self) -> List[Dict]:
        articles = []
        
        rss_feeds = {
            "techcrunch": "https://techcrunch.com/feed/",
            "ars-technica": "https://feeds.arstechnica.com/arstechnica/index",
            "the-verge": "https://www.theverge.com/rss/index.xml",
            "hacker-news": "https://news.ycombinator.com/rss"
        }
        
        async with httpx.AsyncClient() as client:
            for source, feed_url in rss_feeds.items():
                try:
                    response = await client.get(feed_url)
                    if response.status_code == 200:
                        feed = feedparser.parse(response.text)
                        
                        for entry in feed.entries[:settings.NEWS_FETCH_LIMIT]:
                            article = self._process_rss_entry(entry, source)
                            if article:
                                self._save_article(article)
                                articles.append(article)
                                
                except Exception as e:
                    logger.error(f"Error fetching RSS from {source}: {str(e)}")
        
        return articles
    
    def _process_newsapi_article(self, data: Dict, source: str) -> Optional[Dict]:
        try:
            return {
                "source": source,
                "source_url": data.get("url", ""),
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "content": data.get("content", ""),
                "author": data.get("author", ""),
                "published_at": datetime.fromisoformat(
                    data.get("publishedAt", "").replace("Z", "+00:00")
                ),
                "language": "en",
                "category": "technology",
                "image_url": data.get("urlToImage", "")
            }
        except Exception as e:
            logger.error(f"Error processing article: {str(e)}")
            return None
    
    def _process_rss_entry(self, entry: Dict, source: str) -> Optional[Dict]:
        try:
            published_at = None
            if hasattr(entry, "published_parsed"):
                published_at = datetime.fromtimestamp(
                    entry.published_parsed.tm_year
                )
            
            return {
                "source": source,
                "source_url": entry.get("link", ""),
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "content": entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "",
                "author": entry.get("author", ""),
                "published_at": published_at,
                "language": "en",
                "category": "technology"
            }
        except Exception as e:
            logger.error(f"Error processing RSS entry: {str(e)}")
            return None
    
    def _save_article(self, article_data: Dict):
        existing = self.db.query(models.Article).filter(
            models.Article.source_url == article_data["source_url"]
        ).first()
        
        if not existing:
            article = models.Article(**article_data)
            self.db.add(article)
            self.db.commit()