from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class GmailNewsletter(Base):
    """Gmail ニュースレター設定"""
    __tablename__ = "gmail_newsletters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="ニュースレター名")
    
    # フィルタリング設定
    sender_email = Column(String(500), nullable=True, comment="送信者メールアドレス")
    sender_name = Column(String(200), nullable=True, comment="送信者名")
    subject_keywords = Column(JSON, nullable=True, comment="件名キーワード (JSON配列)")
    exclude_keywords = Column(JSON, nullable=True, comment="除外キーワード (JSON配列)")
    
    # カテゴリ・タグ設定
    category = Column(String(100), default="newsletter", comment="カテゴリ")
    tags = Column(JSON, nullable=True, comment="タグ (JSON配列)")
    language = Column(String(10), default="en", comment="言語 (en, ja, zh)")
    
    # 取得設定
    enabled = Column(Boolean, default=True, comment="有効/無効")
    fetch_interval_hours = Column(Integer, default=24, comment="取得間隔（時間）")
    max_emails_per_fetch = Column(Integer, default=10, comment="1回の取得で処理する最大メール数")
    days_back = Column(Integer, default=7, comment="何日前まで遡るか")
    
    # 統計情報
    last_fetched = Column(DateTime, nullable=True, comment="最終取得日時")
    total_emails_processed = Column(Integer, default=0, comment="処理済みメール総数")
    
    # メタデータ
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class GmailFetchLog(Base):
    """Gmail取得ログ"""
    __tablename__ = "gmail_fetch_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    newsletter_id = Column(Integer, nullable=False, comment="ニュースレター設定ID")
    
    # 取得結果
    fetch_time = Column(DateTime, server_default=func.now(), comment="取得日時")
    emails_found = Column(Integer, default=0, comment="見つかったメール数")
    emails_processed = Column(Integer, default=0, comment="処理済みメール数")
    articles_saved = Column(Integer, default=0, comment="保存された記事数")
    
    # ステータス
    status = Column(String(50), default="success", comment="ステータス (success, error, partial)")
    error_message = Column(Text, nullable=True, comment="エラーメッセージ")
    
    # 処理詳細
    query_used = Column(String(1000), nullable=True, comment="使用したGmailクエリ")
    processing_time_seconds = Column(Integer, nullable=True, comment="処理時間（秒）")
    
    created_at = Column(DateTime, server_default=func.now())