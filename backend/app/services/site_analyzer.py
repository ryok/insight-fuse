import httpx
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import re
import logging

try:
    from langdetect import detect, LangDetectException
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False

logger = logging.getLogger(__name__)


class SiteAnalyzer:
    """サイトのメタデータを自動的に分析・抽出するサービス"""
    
    def __init__(self):
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
    
    async def analyze_site(self, url: str) -> Dict[str, any]:
        """URLからサイト情報を自動的に抽出"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 基本情報の抽出
            site_info = {
                'name': self._extract_site_name(soup, url),
                'site_type': self._detect_site_type(url, soup),
                'language': self._detect_language(soup, response.text),
                'category': self._detect_category(soup, response.text),
                'tags': self._extract_tags(soup, response.text),
                'description': self._extract_description(soup)
            }
            
            # Mailchimpの場合の特別処理
            if 'campaign-archive.com' in url or 'list-manage.com' in url:
                site_info['site_type'] = 'newsletter'
                site_info['category'] = site_info['category'] or 'newsletter'
            
            return site_info
            
        except Exception as e:
            logger.error(f"Error analyzing site {url}: {str(e)}")
            return self._default_info(url)
    
    def _extract_site_name(self, soup: BeautifulSoup, url: str) -> str:
        """サイト名を抽出"""
        # 1. og:site_name
        og_site_name = soup.find('meta', property='og:site_name')
        if og_site_name and og_site_name.get('content'):
            return og_site_name['content'].strip()
        
        # 2. <title>タグ
        title = soup.find('title')
        if title and title.text:
            # " - " や " | " で分割して最後の部分を取得
            title_text = title.text.strip()
            for separator in [' - ', ' | ', ' – ', ' — ']:
                if separator in title_text:
                    parts = title_text.split(separator)
                    # 最後の部分がサイト名の可能性が高い
                    return parts[-1].strip()
            
            # 分割できない場合はタイトル全体（ただし長すぎる場合は省略）
            if len(title_text) <= 50:
                return title_text
        
        # 3. h1タグ
        h1 = soup.find('h1')
        if h1 and h1.text and len(h1.text.strip()) <= 50:
            return h1.text.strip()
        
        # 4. ドメイン名から推測
        domain = urlparse(url).netloc
        domain_parts = domain.split('.')
        if domain_parts:
            # サブドメインを除いた部分
            main_domain = domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]
            # キャメルケースやハイフンを処理
            name = re.sub(r'[-_]', ' ', main_domain)
            return name.title()
        
        return "Unknown Site"
    
    def _detect_site_type(self, url: str, soup: BeautifulSoup) -> str:
        """サイトタイプを検出"""
        url_lower = url.lower()
        
        # URLベースの判定
        if 'substack.com' in url_lower:
            return 'substack'
        elif any(x in url_lower for x in ['campaign-archive.com', 'list-manage.com', 'mailchi.mp']):
            return 'newsletter'
        elif 'medium.com' in url_lower or 'blog' in url_lower:
            return 'blog'
        
        # コンテンツベースの判定
        content = soup.get_text().lower()
        
        # ニュースレターの特徴
        newsletter_keywords = ['newsletter', 'subscribe', 'unsubscribe', 'email', 'weekly', 'monthly']
        if sum(1 for kw in newsletter_keywords if kw in content) >= 3:
            return 'newsletter'
        
        # ブログの特徴
        if soup.find('article') or soup.find(class_=re.compile(r'post|article|entry')):
            return 'blog'
        
        # RSSフィードの存在
        if soup.find('link', type='application/rss+xml'):
            return 'blog'
        
        return 'generic'
    
    def _detect_language(self, soup: BeautifulSoup, text: str) -> str:
        """言語を検出"""
        # 1. HTML lang属性
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            lang = html_tag['lang'][:2].lower()
            if lang in ['en', 'ja', 'zh']:
                return lang
        
        # 2. meta言語タグ
        meta_lang = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if meta_lang and meta_lang.get('content'):
            lang = meta_lang['content'][:2].lower()
            if lang in ['en', 'ja', 'zh']:
                return lang
        
        # 3. テキスト内容から検出
        if HAS_LANGDETECT:
            try:
                # タイトルと本文の最初の部分から検出
                sample_text = ''
                
                title = soup.find('title')
                if title and title.text:
                    sample_text += title.text + ' '
                
                # 本文の最初の段落
                for p in soup.find_all('p')[:5]:
                    if p.text:
                        sample_text += p.text + ' '
                
                if len(sample_text) > 50:
                    detected_lang = detect(sample_text)
                    
                    # 検出された言語をマッピング
                    lang_map = {
                        'en': 'en',
                        'ja': 'ja',
                        'zh-cn': 'zh',
                        'zh-tw': 'zh',
                        'ko': 'en',  # 韓国語はサポート外なので英語にフォールバック
                    }
                    
                    return lang_map.get(detected_lang, 'en')
                    
            except Exception:
                pass
        
        return 'en'  # デフォルト
    
    def _detect_category(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """カテゴリを検出"""
        content_lower = text.lower()
        
        # カテゴリキーワードマッピング
        category_keywords = {
            'ai': ['artificial intelligence', 'machine learning', 'deep learning', 'neural network', 
                   'ai', 'ml', 'chatgpt', 'gpt', 'llm', '人工知能', '機械学習', '深層学習'],
            'data-science': ['data science', 'kaggle', 'data analysis', 'statistics', 'analytics',
                            'データサイエンス', 'データ分析', '統計'],
            'technology': ['technology', 'tech', 'software', 'hardware', 'computer', 'programming',
                          'テクノロジー', '技術', 'ソフトウェア', 'プログラミング'],
            'startup': ['startup', 'entrepreneur', 'venture', 'funding', 'investment',
                       'スタートアップ', '起業', 'ベンチャー'],
            'business': ['business', 'management', 'marketing', 'finance', 'economy',
                        'ビジネス', '経営', 'マーケティング', '経済'],
            'science': ['science', 'research', 'study', 'discovery', 'experiment',
                       '科学', '研究', '実験', '発見'],
            'creative-ai': ['creative', 'art', 'design', 'music', 'generative',
                           'クリエイティブ', 'アート', 'デザイン', '音楽', '生成']
        }
        
        # 各カテゴリのスコアを計算
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                category_scores[category] = score
        
        # 最もスコアの高いカテゴリを返す
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        # メタタグからカテゴリを取得
        meta_category = soup.find('meta', attrs={'name': 'category'})
        if meta_category and meta_category.get('content'):
            return meta_category['content'].lower()
        
        return 'technology'  # デフォルト
    
    def _extract_tags(self, soup: BeautifulSoup, text: str) -> List[str]:
        """タグを抽出"""
        tags = set()
        
        # 1. メタキーワード
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = meta_keywords['content'].split(',')
            tags.update(kw.strip().lower() for kw in keywords[:10])
        
        # 2. article:tag
        for tag in soup.find_all('meta', property='article:tag'):
            if tag.get('content'):
                tags.add(tag['content'].strip().lower())
        
        # 3. カテゴリやサイトタイプから推測
        site_type = self._detect_site_type(soup.get_text(), soup)
        if site_type:
            tags.add(site_type)
        
        # 4. 頻出キーワードの抽出
        tech_keywords = [
            'ai', 'machine learning', 'deep learning', 'data science', 
            'programming', 'software', 'technology', 'startup', 'innovation',
            'api', 'cloud', 'security', 'blockchain', 'iot', 'robotics'
        ]
        
        content_lower = text.lower()
        for keyword in tech_keywords:
            if keyword in content_lower:
                tags.add(keyword.replace(' ', '-'))
        
        # 最大10個まで
        return list(tags)[:10]
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """説明文を抽出"""
        # 1. og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # 2. meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # 3. 最初の段落
        first_p = soup.find('p')
        if first_p and first_p.text:
            desc = first_p.text.strip()
            if len(desc) > 50 and len(desc) < 500:
                return desc
        
        return None
    
    def _default_info(self, url: str) -> Dict[str, any]:
        """デフォルトの情報を返す"""
        domain = urlparse(url).netloc
        name = domain.split('.')[0] if '.' in domain else domain
        
        return {
            'name': name.title(),
            'site_type': 'generic',
            'language': 'en',
            'category': 'technology',
            'tags': [],
            'description': None
        }
    
    async def close(self):
        """HTTPクライアントを閉じる"""
        await self.session.aclose()