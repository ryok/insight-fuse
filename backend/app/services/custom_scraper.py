import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
import re
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class CustomScraper:
    def __init__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
    
    async def scrape_site(self, site_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """指定されたサイト設定に基づいてコンテンツを取得"""
        try:
            site_type = site_config.get('type', 'generic')
            url = site_config['url']
            
            # Mailchimp Campaign Archiveの検出
            if 'campaign-archive.com' in url or 'list-manage.com' in url:
                return await self._scrape_mailchimp_archive(url, site_config)
            elif site_type == 'substack':
                return await self._scrape_substack(url, site_config)
            elif site_type == 'newsletter':
                return await self._scrape_newsletter(url, site_config)
            elif site_type == 'blog':
                return await self._scrape_blog(url, site_config)
            else:
                return await self._scrape_generic(url, site_config)
                
        except Exception as e:
            logger.error(f"Error scraping {site_config.get('name', 'unknown')}: {str(e)}")
            return []
    
    async def _scrape_mailchimp_archive(self, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mailchimp Campaign Archiveから記事を取得"""
        articles = []
        
        try:
            # URLからパラメータを抽出
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            
            # Campaign ArchiveのRSSフィードURLを構築
            if 'u' in params and 'id' in params:
                user_id = params['u'][0]
                list_id = params['id'][0]
                rss_url = f"https://us20.campaign-archive.com/feed?u={user_id}&id={list_id}"
                
                # RSSフィードから記事を取得
                response = await self.session.get(rss_url)
                response.raise_for_status()
                
                # フィードパーサーを使ってRSSを解析
                import feedparser
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries[:10]:  # 最新10記事
                    try:
                        article_data = {
                            'source': config.get('name', feed.feed.get('title', 'Mailchimp Newsletter')),
                            'source_url': entry.get('link', ''),
                            'title': entry.get('title', ''),
                            'description': entry.get('summary', '')[:500],
                            'content': entry.get('summary', ''),
                            'published_at': self._parse_date(entry.get('published', '')),
                            'language': config.get('language', 'en'),
                            'category': config.get('category', 'newsletter'),
                            'tags': config.get('tags', [])
                        }
                        
                        # 個別記事の内容を取得
                        if entry.get('link'):
                            full_content = await self._fetch_mailchimp_article_content(entry['link'])
                            if full_content:
                                article_data['content'] = full_content
                                article_data['description'] = full_content[:500] + '...' if len(full_content) > 500 else full_content
                        
                        articles.append(article_data)
                        
                    except Exception as e:
                        logger.warning(f"Error processing RSS entry: {str(e)}")
                        continue
                
            else:
                # 通常のアーカイブページから記事リンクを取得
                response = await self.session.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Mailchimpのアーカイブページから記事リンクを探す
                campaign_links = soup.find_all('a', href=re.compile(r'/?u=.*&id=.*'))
                
                for link in campaign_links[:10]:  # 最新10記事
                    article_url = urljoin(url, link.get('href'))
                    article_data = await self._scrape_mailchimp_article(article_url, config)
                    if article_data:
                        articles.append(article_data)
                        
        except Exception as e:
            logger.error(f"Error scraping Mailchimp archive {url}: {str(e)}")
        
        return articles
    
    async def _fetch_mailchimp_article_content(self, url: str) -> Optional[str]:
        """Mailchimp記事の本文を取得"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Mailchimp記事のコンテンツセレクター
            content_selectors = [
                '#templateBody',
                '.mcnTextContent',
                '.bodyContent',
                '#bodyTable',
                'td.mcnTextContent',
                '[role="article"]'
            ]
            
            content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # スタイルとスクリプトを除去
                    for elem in content_elem(['style', 'script']):
                        elem.decompose()
                    content = content_elem.get_text(strip=True)
                    if content:
                        break
            
            return content if content else None
            
        except Exception as e:
            logger.error(f"Error fetching Mailchimp article content: {str(e)}")
            return None
    
    async def _scrape_mailchimp_article(self, url: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """個別のMailchimp記事を取得"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # タイトル取得
            title_elem = soup.find('title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # コンテンツ取得
            content = await self._fetch_mailchimp_article_content(url) or ''
            
            # 公開日取得（メタタグから）
            date_elem = soup.find('meta', attrs={'property': 'article:published_time'})
            published_at = self._parse_date(date_elem.get('content') if date_elem else None)
            
            return {
                'source': config.get('name', 'Mailchimp Newsletter'),
                'source_url': url,
                'title': title,
                'description': content[:500] + '...' if len(content) > 500 else content,
                'content': content,
                'published_at': published_at,
                'language': config.get('language', 'en'),
                'category': config.get('category', 'newsletter'),
                'tags': config.get('tags', [])
            }
            
        except Exception as e:
            logger.error(f"Error scraping Mailchimp article {url}: {str(e)}")
            return None
    
    async def _scrape_substack(self, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Substackサイトの記事を取得"""
        articles = []
        
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Substackの記事リンクを取得
            article_links = soup.find_all('a', href=re.compile(r'/p/'))
            
            for link in article_links[:5]:  # 最新5記事
                article_url = urljoin(url, link.get('href'))
                article_data = await self._scrape_substack_article(article_url, config)
                if article_data:
                    articles.append(article_data)
                    
        except Exception as e:
            logger.error(f"Error scraping Substack {url}: {str(e)}")
        
        return articles
    
    async def _scrape_substack_article(self, url: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """個別のSubstack記事を取得"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # タイトル取得
            title_elem = soup.find('h1', class_='post-title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # 内容取得
            content_elem = soup.find('div', class_='available-content') or soup.find('div', class_='body')
            content = content_elem.get_text(strip=True) if content_elem else ''
            
            # 公開日取得
            date_elem = soup.find('time') or soup.find('span', class_='pencraft')
            published_at = self._parse_date(date_elem.get('datetime') if date_elem else None)
            
            # 説明文取得
            description_elem = soup.find('meta', attrs={'name': 'description'})
            description = description_elem.get('content', '') if description_elem else content[:300]
            
            return {
                'source': config.get('name', 'Substack'),
                'source_url': url,
                'title': title,
                'description': description,
                'content': content,
                'published_at': published_at,
                'language': config.get('language', 'en'),
                'category': config.get('category', 'newsletter'),
                'tags': config.get('tags', [])
            }
            
        except Exception as e:
            logger.error(f"Error scraping Substack article {url}: {str(e)}")
            return None
    
    async def _scrape_newsletter(self, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ニュースレター形式のサイトを取得"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # タイトル取得
            title_elem = soup.find('title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else 'Newsletter'
            
            # メインコンテンツ取得
            content_selectors = [
                'main', 
                '.email-content', 
                '.newsletter-content',
                '[role="main"]',
                'article',
                '.content'
            ]
            
            content = ''
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
            
            if not content:
                # フォールバック: bodyから不要な要素を除外
                for elem in soup(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                content = soup.get_text(strip=True)
            
            # 公開日取得の試行
            published_at = self._extract_date_from_content(soup) or datetime.utcnow()
            
            return [{
                'source': config.get('name', 'Newsletter'),
                'source_url': url,
                'title': title,
                'description': content[:300] + '...' if len(content) > 300 else content,
                'content': content,
                'published_at': published_at,
                'language': config.get('language', 'en'),
                'category': config.get('category', 'newsletter'),
                'tags': config.get('tags', [])
            }]
            
        except Exception as e:
            logger.error(f"Error scraping newsletter {url}: {str(e)}")
            return []
    
    async def _scrape_blog(self, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ブログサイトの記事一覧を取得"""
        articles = []
        
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ブログ記事のリンクを探す
            article_selectors = [
                'article a', 
                '.post a', 
                '.entry a',
                'h2 a',
                'h3 a'
            ]
            
            article_links = []
            for selector in article_selectors:
                links = soup.select(selector)
                if links:
                    article_links = links[:5]  # 最新5記事
                    break
            
            for link in article_links:
                article_url = urljoin(url, link.get('href'))
                article_data = await self._scrape_blog_article(article_url, config)
                if article_data:
                    articles.append(article_data)
                    
        except Exception as e:
            logger.error(f"Error scraping blog {url}: {str(e)}")
        
        return articles
    
    async def _scrape_blog_article(self, url: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """個別のブログ記事を取得"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # タイトル取得
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # 記事内容取得
            content_selectors = ['article', '.post-content', '.entry-content', '.content', 'main']
            content = ''
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
            
            # 公開日取得
            published_at = self._extract_date_from_content(soup) or datetime.utcnow()
            
            return {
                'source': config.get('name', 'Blog'),
                'source_url': url,
                'title': title,
                'description': content[:300] + '...' if len(content) > 300 else content,
                'content': content,
                'published_at': published_at,
                'language': config.get('language', 'en'),
                'category': config.get('category', 'blog'),
                'tags': config.get('tags', [])
            }
            
        except Exception as e:
            logger.error(f"Error scraping blog article {url}: {str(e)}")
            return None
    
    async def _scrape_generic(self, url: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """汎用的なWebページを取得"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 不要な要素を除去
            for elem in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                elem.decompose()
            
            # タイトル取得
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else 'Web Content'
            
            # メインコンテンツ取得
            main_elem = soup.find('main') or soup.find('article') or soup.find('body')
            content = main_elem.get_text(strip=True) if main_elem else ''
            
            return [{
                'source': config.get('name', 'Web'),
                'source_url': url,
                'title': title,
                'description': content[:300] + '...' if len(content) > 300 else content,
                'content': content,
                'published_at': datetime.utcnow(),
                'language': config.get('language', 'en'),
                'category': config.get('category', 'web'),
                'tags': config.get('tags', [])
            }]
            
        except Exception as e:
            logger.error(f"Error scraping generic site {url}: {str(e)}")
            return []
    
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """日付文字列をパース"""
        if not date_str:
            return datetime.utcnow()
        
        try:
            # ISO形式の場合
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # RSSの日付形式
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            return datetime.utcnow()
    
    def _extract_date_from_content(self, soup: BeautifulSoup) -> Optional[datetime]:
        """コンテンツから日付を抽出"""
        date_selectors = [
            'time[datetime]',
            '.published-date',
            '.post-date',
            '.date',
            'meta[property="article:published_time"]'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                date_str = elem.get('datetime') or elem.get('content') or elem.get_text()
                if date_str:
                    return self._parse_date(date_str)
        
        return None
    
    async def close(self):
        """HTTPクライアントを閉じる"""
        await self.session.aclose()