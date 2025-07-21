from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.gmail_newsletter import GmailNewsletter, GmailFetchLog
from app.models.article import Article
from app.services.gmail_service import GmailService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gmail", tags=["Gmail"])


# Pydanticモデル
class GmailNewsletterCreate(BaseModel):
    name: str
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    subject_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    category: str = "newsletter"
    tags: Optional[List[str]] = None
    language: str = "en"
    enabled: bool = True
    fetch_interval_hours: int = 24
    max_emails_per_fetch: int = 10
    days_back: int = 7


class GmailNewsletterUpdate(BaseModel):
    name: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    subject_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    language: Optional[str] = None
    enabled: Optional[bool] = None
    fetch_interval_hours: Optional[int] = None
    max_emails_per_fetch: Optional[int] = None
    days_back: Optional[int] = None


class GmailNewsletterResponse(BaseModel):
    id: int
    name: str
    sender_email: Optional[str]
    sender_name: Optional[str]
    subject_keywords: Optional[List[str]]
    exclude_keywords: Optional[List[str]]
    category: str
    tags: Optional[List[str]]
    language: str
    enabled: bool
    fetch_interval_hours: int
    max_emails_per_fetch: int
    days_back: int
    last_fetched: Optional[datetime]
    total_emails_processed: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GmailFetchLogResponse(BaseModel):
    id: int
    newsletter_id: int
    fetch_time: datetime
    emails_found: int
    emails_processed: int
    articles_saved: int
    status: str
    error_message: Optional[str]
    query_used: Optional[str]
    processing_time_seconds: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/newsletters", response_model=List[GmailNewsletterResponse])
def get_gmail_newsletters(
    enabled_only: bool = True,
    db: Session = Depends(get_db)
):
    """Gmail ニュースレター設定一覧を取得"""
    query = db.query(GmailNewsletter)
    if enabled_only:
        query = query.filter(GmailNewsletter.enabled == True)
    
    newsletters = query.all()
    return newsletters


@router.get("/newsletters/{newsletter_id}", response_model=GmailNewsletterResponse)
def get_gmail_newsletter(
    newsletter_id: int,
    db: Session = Depends(get_db)
):
    """特定のGmail ニュースレター設定を取得"""
    newsletter = db.query(GmailNewsletter).filter(GmailNewsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter configuration not found")
    return newsletter


@router.post("/newsletters", response_model=GmailNewsletterResponse)
def create_gmail_newsletter(
    newsletter_data: GmailNewsletterCreate,
    db: Session = Depends(get_db)
):
    """新しいGmail ニュースレター設定を作成"""
    try:
        newsletter = GmailNewsletter(
            name=newsletter_data.name,
            sender_email=newsletter_data.sender_email,
            sender_name=newsletter_data.sender_name,
            subject_keywords=newsletter_data.subject_keywords,
            exclude_keywords=newsletter_data.exclude_keywords,
            category=newsletter_data.category,
            tags=newsletter_data.tags,
            language=newsletter_data.language,
            enabled=newsletter_data.enabled,
            fetch_interval_hours=newsletter_data.fetch_interval_hours,
            max_emails_per_fetch=newsletter_data.max_emails_per_fetch,
            days_back=newsletter_data.days_back
        )
        
        db.add(newsletter)
        db.commit()
        db.refresh(newsletter)
        
        logger.info(f"Created Gmail newsletter configuration: {newsletter.name}")
        return newsletter
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating Gmail newsletter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create newsletter configuration: {str(e)}")


@router.put("/newsletters/{newsletter_id}", response_model=GmailNewsletterResponse)
def update_gmail_newsletter(
    newsletter_id: int,
    newsletter_data: GmailNewsletterUpdate,
    db: Session = Depends(get_db)
):
    """Gmail ニュースレター設定を更新"""
    newsletter = db.query(GmailNewsletter).filter(GmailNewsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter configuration not found")
    
    try:
        # 更新されたフィールドのみ適用
        for field, value in newsletter_data.model_dump(exclude_unset=True).items():
            setattr(newsletter, field, value)
        
        db.commit()
        db.refresh(newsletter)
        
        logger.info(f"Updated Gmail newsletter configuration: {newsletter.name}")
        return newsletter
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating Gmail newsletter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update newsletter configuration: {str(e)}")


@router.delete("/newsletters/{newsletter_id}")
def delete_gmail_newsletter(
    newsletter_id: int,
    db: Session = Depends(get_db)
):
    """Gmail ニュースレター設定を削除"""
    newsletter = db.query(GmailNewsletter).filter(GmailNewsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter configuration not found")
    
    try:
        db.delete(newsletter)
        db.commit()
        
        logger.info(f"Deleted Gmail newsletter configuration: {newsletter.name}")
        return {"message": "Newsletter configuration deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting Gmail newsletter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete newsletter configuration: {str(e)}")


@router.post("/newsletters/{newsletter_id}/fetch")
def fetch_newsletter_emails(
    newsletter_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """特定のニュースレターのメールを取得"""
    newsletter = db.query(GmailNewsletter).filter(GmailNewsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter configuration not found")
    
    if not newsletter.enabled:
        raise HTTPException(status_code=400, detail="Newsletter is disabled")
    
    # バックグラウンドタスクでメール取得を実行
    background_tasks.add_task(
        fetch_emails_for_newsletter,
        newsletter_id=newsletter_id
    )
    
    return {"message": f"Started fetching emails for newsletter: {newsletter.name}"}


@router.post("/fetch-all")
def fetch_all_newsletter_emails(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """全ての有効なニュースレターのメールを取得"""
    newsletters = db.query(GmailNewsletter).filter(GmailNewsletter.enabled == True).all()
    
    if not newsletters:
        return {"message": "No enabled newsletters found"}
    
    # バックグラウンドタスクで実行
    for newsletter in newsletters:
        background_tasks.add_task(
            fetch_emails_for_newsletter,
            newsletter_id=newsletter.id
        )
    
    return {"message": f"Started fetching emails for {len(newsletters)} newsletters"}


@router.get("/newsletters/{newsletter_id}/logs", response_model=List[GmailFetchLogResponse])
def get_newsletter_fetch_logs(
    newsletter_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """特定のニュースレターの取得ログを取得"""
    newsletter = db.query(GmailNewsletter).filter(GmailNewsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter configuration not found")
    
    logs = (db.query(GmailFetchLog)
            .filter(GmailFetchLog.newsletter_id == newsletter_id)
            .order_by(GmailFetchLog.created_at.desc())
            .limit(limit)
            .all())
    
    return logs


@router.post("/test-connection")
def test_gmail_connection():
    """Gmail API接続をテスト"""
    try:
        gmail_service = GmailService()
        
        # 簡単なクエリでテスト
        emails = gmail_service.search_emails("in:inbox", max_results=1, days_back=1)
        
        return {
            "status": "success",
            "message": "Gmail API connection successful",
            "test_result": f"Found {len(emails)} recent emails"
        }
        
    except FileNotFoundError as e:
        return {
            "status": "error",
            "message": "Gmail API credentials not found",
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": "Gmail API connection failed",
            "error": str(e)
        }


def fetch_emails_for_newsletter(newsletter_id: int):
    """バックグラウンドタスク: 特定のニュースレターのメールを取得"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    start_time = datetime.now()
    
    try:
        newsletter = db.query(GmailNewsletter).filter(GmailNewsletter.id == newsletter_id).first()
        if not newsletter:
            logger.error(f"Newsletter {newsletter_id} not found")
            return
        
        logger.info(f"Starting email fetch for newsletter: {newsletter.name}")
        
        # Gmail サービスを初期化
        gmail_service = GmailService()
        
        # フィルター設定を構築
        filter_config = {
            'name': newsletter.name,
            'category': newsletter.category,
            'from': newsletter.sender_email,
            'subject_keywords': newsletter.subject_keywords or [],
            'exclude_keywords': newsletter.exclude_keywords or []
        }
        
        # メールを取得
        emails = gmail_service.get_newsletters_by_filters(
            [filter_config], 
            days_back=newsletter.days_back
        )
        
        # 取得したメールを記事として保存
        articles_saved = 0
        emails_processed = 0
        
        for email_data in emails[:newsletter.max_emails_per_fetch]:
            try:
                # メール内容を記事形式に変換
                article_data = gmail_service.extract_newsletter_content(email_data)
                if not article_data:
                    continue
                
                # 既存の記事をチェック（重複回避）
                existing_article = db.query(Article).filter(
                    Article.source_url == article_data['source_url']
                ).first()
                
                if existing_article:
                    logger.info(f"Article already exists: {article_data['title']}")
                    continue
                
                # 新しい記事として保存
                article = Article(
                    title=article_data['title'],
                    description=article_data['description'],
                    content=article_data['content'],
                    author=article_data['author'],
                    source=article_data['source'],
                    source_url=article_data['source_url'],
                    published_at=article_data['published_at'],
                    language=article_data['language'],
                    category=article_data['category'],
                    tags=article_data['tags']
                )
                
                db.add(article)
                articles_saved += 1
                
            except Exception as e:
                logger.error(f"Error processing email {email_data.get('id')}: {e}")
            
            emails_processed += 1
        
        # 統計情報を更新
        newsletter.last_fetched = datetime.now()
        newsletter.total_emails_processed += emails_processed
        
        # ログを記録
        processing_time = (datetime.now() - start_time).seconds
        
        fetch_log = GmailFetchLog(
            newsletter_id=newsletter_id,
            emails_found=len(emails),
            emails_processed=emails_processed,
            articles_saved=articles_saved,
            status="success",
            processing_time_seconds=processing_time,
            query_used=str(filter_config)
        )
        
        db.add(fetch_log)
        db.commit()
        
        logger.info(
            f"Completed email fetch for {newsletter.name}: "
            f"{emails_processed} processed, {articles_saved} saved"
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching emails for newsletter {newsletter_id}: {error_msg}")
        
        # エラーログを記録
        processing_time = (datetime.now() - start_time).seconds
        fetch_log = GmailFetchLog(
            newsletter_id=newsletter_id,
            emails_found=0,
            emails_processed=0,
            articles_saved=0,
            status="error",
            error_message=error_msg,
            processing_time_seconds=processing_time
        )
        
        db.add(fetch_log)
        db.commit()
        
    finally:
        db.close()