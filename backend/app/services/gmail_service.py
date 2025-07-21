import os
import base64
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from email.mime.text import MIMEText
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)

# Gmail API のスコープ
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailService:
    """Gmail APIを使用してメールレターを取得するサービス"""
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Gmail APIの認証を行う"""
        creds = None
        
        # token.jsonが存在する場合、既存の認証情報を読み込む
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # 認証情報がないか、期限切れの場合は再認証
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Credentials file not found: {self.credentials_file}")
                    raise FileNotFoundError(f"Please place your Google API credentials in {self.credentials_file}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 認証情報を保存
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail API authentication successful")
    
    def search_emails(
        self, 
        query: str, 
        max_results: int = 50, 
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        指定したクエリでメールを検索
        
        Args:
            query: Gmail検索クエリ（例: 'from:newsletter@example.com', 'subject:weekly'）
            max_results: 取得する最大件数
            days_back: 何日前まで遡るか
        
        Returns:
            メール情報のリスト
        """
        try:
            if not self.service:
                self._authenticate()
            
            # 日付フィルターを追加
            date_filter = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            full_query = f"{query} after:{date_filter}"
            
            # メールを検索
            results = self.service.users().messages().list(
                userId='me', 
                q=full_query, 
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info(f"No messages found for query: {full_query}")
                return []
            
            email_data = []
            for message in messages:
                email_info = self._get_email_details(message['id'])
                if email_info:
                    email_data.append(email_info)
            
            logger.info(f"Retrieved {len(email_data)} emails for query: {query}")
            return email_data
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []
    
    def _get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """指定されたメッセージIDのメール詳細を取得"""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            
            # ヘッダー情報を取得
            subject = self._get_header_value(headers, 'Subject')
            sender = self._get_header_value(headers, 'From')
            date_str = self._get_header_value(headers, 'Date')
            
            # メール本文を取得
            content = self._extract_email_content(message['payload'])
            
            # テキスト版とHTML版を分離
            text_content = content.get('text', '')
            html_content = content.get('html', '')
            
            # HTMLからプレーンテキストを抽出
            if html_content and not text_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                text_content = soup.get_text(separator=' ', strip=True)
            
            # 日付をパース
            published_at = self._parse_email_date(date_str)
            
            return {
                'id': message_id,
                'subject': subject or 'No Subject',
                'sender': sender or 'Unknown Sender',
                'published_at': published_at,
                'text_content': text_content,
                'html_content': html_content,
                'raw_headers': headers,
            }
            
        except HttpError as error:
            logger.error(f"Error getting email details for {message_id}: {error}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting email details for {message_id}: {e}")
            return None
    
    def _get_header_value(self, headers: List[Dict], name: str) -> Optional[str]:
        """ヘッダーから指定された名前の値を取得"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return None
    
    def _extract_email_content(self, payload: Dict) -> Dict[str, str]:
        """メールのペイロードからコンテンツを抽出"""
        content = {'text': '', 'html': ''}
        
        def extract_part(part):
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    content['text'] = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            elif mime_type == 'text/html':
                data = part['body'].get('data', '')
                if data:
                    content['html'] = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            
            # 複数パートの場合は再帰的に処理
            if 'parts' in part:
                for sub_part in part['parts']:
                    extract_part(sub_part)
        
        extract_part(payload)
        return content
    
    def _parse_email_date(self, date_str: Optional[str]) -> datetime:
        """メールの日付文字列をdatetimeオブジェクトに変換"""
        if not date_str:
            return datetime.now()
        
        try:
            # RFC 2822形式の日付をパース
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return datetime.now()
    
    def get_newsletters_by_filters(
        self, 
        filters: List[Dict[str, Any]], 
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        複数のフィルターでニュースレターを取得
        
        Args:
            filters: フィルター設定のリスト
                [
                    {
                        'name': 'AI Weekly',
                        'from': 'newsletter@aiweekly.com',
                        'subject_keywords': ['AI', 'machine learning'],
                        'exclude_keywords': ['unsubscribe', 'spam']
                    }
                ]
            days_back: 何日前まで遡るか
        
        Returns:
            取得したニュースレターのリスト
        """
        all_newsletters = []
        
        for filter_config in filters:
            try:
                # クエリを構築
                query_parts = []
                
                if filter_config.get('from'):
                    query_parts.append(f"from:{filter_config['from']}")
                
                if filter_config.get('subject_keywords'):
                    for keyword in filter_config['subject_keywords']:
                        query_parts.append(f"subject:{keyword}")
                
                # 除外キーワード
                if filter_config.get('exclude_keywords'):
                    for keyword in filter_config['exclude_keywords']:
                        query_parts.append(f"-{keyword}")
                
                query = ' '.join(query_parts)
                
                if not query:
                    logger.warning(f"No valid query for filter: {filter_config}")
                    continue
                
                # メールを検索
                emails = self.search_emails(query, max_results=20, days_back=days_back)
                
                # フィルター名を追加
                for email in emails:
                    email['filter_name'] = filter_config.get('name', 'Unknown')
                    email['newsletter_category'] = filter_config.get('category', 'general')
                
                all_newsletters.extend(emails)
                
                logger.info(f"Found {len(emails)} emails for filter '{filter_config.get('name')}'")
                
            except Exception as e:
                logger.error(f"Error processing filter {filter_config}: {e}")
                continue
        
        # 重複を除去（メールIDベース）
        seen_ids = set()
        unique_newsletters = []
        for newsletter in all_newsletters:
            if newsletter['id'] not in seen_ids:
                unique_newsletters.append(newsletter)
                seen_ids.add(newsletter['id'])
        
        logger.info(f"Retrieved {len(unique_newsletters)} unique newsletters")
        return unique_newsletters
    
    def extract_newsletter_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ニュースレターからコンテンツを抽出し、記事形式に変換
        
        Args:
            email_data: Gmail APIから取得したメールデータ
        
        Returns:
            記事形式のデータ
        """
        try:
            # HTMLコンテンツを優先、なければテキストコンテンツを使用
            content = email_data.get('html_content') or email_data.get('text_content', '')
            
            if not content:
                logger.warning(f"No content found in email {email_data['id']}")
                return None
            
            # HTMLの場合、BeautifulSoupでパース
            if email_data.get('html_content'):
                soup = BeautifulSoup(content, 'html.parser')
                
                # 不要な要素を削除
                for tag in soup(['script', 'style', 'meta', 'link']):
                    tag.decompose()
                
                # テキストコンテンツを抽出
                text_content = soup.get_text(separator='\n', strip=True)
                
                # HTMLコンテンツはクリーニング
                clean_html = str(soup)
            else:
                text_content = content
                clean_html = None
            
            # 送信者情報をパース
            sender_name, sender_email = self._parse_sender(email_data.get('sender', ''))
            
            # カテゴリを推定
            category = self._detect_newsletter_category(
                email_data.get('subject', ''), 
                text_content
            )
            
            # 記事データを構築
            article_data = {
                'title': email_data.get('subject', 'No Subject'),
                'content': text_content[:5000],  # 最初の5000文字
                'html_content': clean_html,
                'description': text_content[:500] + '...' if len(text_content) > 500 else text_content,
                'author': sender_name,
                'source': email_data.get('filter_name', sender_name),
                'source_url': f"gmail://message/{email_data['id']}",
                'published_at': email_data.get('published_at', datetime.now()),
                'language': self._detect_language(text_content),
                'category': category,
                'tags': self._extract_tags(email_data.get('subject', ''), text_content),
                'newsletter_data': {
                    'gmail_id': email_data['id'],
                    'sender_email': sender_email,
                    'filter_name': email_data.get('filter_name'),
                    'newsletter_category': email_data.get('newsletter_category', 'general')
                }
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error extracting newsletter content: {e}")
            return None
    
    def _parse_sender(self, sender_str: str) -> tuple[str, str]:
        """送信者文字列から名前とメールアドレスを分離"""
        if not sender_str:
            return 'Unknown', 'unknown@unknown.com'
        
        # "Name <email@example.com>" 形式
        match = re.match(r'^(.+?)\s*<(.+?)>$', sender_str)
        if match:
            name = match.group(1).strip(' "')
            email = match.group(2).strip()
            return name, email
        
        # メールアドレスのみの場合
        if '@' in sender_str:
            return sender_str.split('@')[0], sender_str
        
        return sender_str, 'unknown@unknown.com'
    
    def _detect_newsletter_category(self, subject: str, content: str) -> str:
        """件名とコンテンツからカテゴリを推定"""
        text = (subject + ' ' + content).lower()
        
        categories = {
            'ai': ['artificial intelligence', 'machine learning', 'deep learning', 'ai', 'ml', 'gpt', 'llm'],
            'tech': ['technology', 'startup', 'programming', 'software', 'developer'],
            'data': ['data science', 'analytics', 'big data', 'kaggle'],
            'business': ['business', 'finance', 'market', 'economy', 'investment'],
            'science': ['science', 'research', 'study', 'discovery'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'newsletter'
    
    def _detect_language(self, text: str) -> str:
        """テキストの言語を検出"""
        try:
            from langdetect import detect
            lang = detect(text[:1000])  # 最初の1000文字で判定
            if lang in ['ja', 'en', 'zh']:
                return lang
        except:
            pass
        
        # 日本語の文字が含まれているかチェック
        if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF' for char in text):
            return 'ja'
        
        return 'en'
    
    def _extract_tags(self, subject: str, content: str) -> List[str]:
        """件名とコンテンツからタグを抽出"""
        text = (subject + ' ' + content).lower()
        tags = set()
        
        # 技術関連キーワード
        tech_keywords = [
            'ai', 'machine learning', 'deep learning', 'data science',
            'programming', 'software', 'startup', 'innovation',
            'blockchain', 'cloud', 'security', 'api'
        ]
        
        for keyword in tech_keywords:
            if keyword in text:
                tags.add(keyword.replace(' ', '-'))
        
        # メール固有のタグ
        tags.add('newsletter')
        tags.add('email')
        
        return list(tags)[:10]  # 最大10個