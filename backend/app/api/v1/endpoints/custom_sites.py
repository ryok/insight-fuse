from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.db.database import get_db
from app.db import models
from app.schemas.custom_site import CustomSite, CustomSiteCreate, CustomSiteUpdate, CustomSiteFetchLog
from app.services.custom_scraper import CustomScraper
from app.services.news_fetcher import NewsFetcher
from app.services.site_analyzer import SiteAnalyzer
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[CustomSite])
def get_custom_sites(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(models.CustomSite)
    
    if enabled_only:
        query = query.filter(models.CustomSite.enabled == True)
    
    sites = query.offset(skip).limit(limit).all()
    return sites


@router.get("/{site_id}", response_model=CustomSite)
def get_custom_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(models.CustomSite).filter(models.CustomSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Custom site not found")
    return site


@router.post("/", response_model=CustomSite)
def create_custom_site(site: CustomSiteCreate, db: Session = Depends(get_db)):
    try:
        # URL長のチェック
        if len(site.url) > 1000:
            raise HTTPException(
                status_code=400, 
                detail=f"URLが長すぎます（最大1000文字）。現在: {len(site.url)}文字"
            )
        
        # 既存のURLチェック
        existing = db.query(models.CustomSite).filter(
            models.CustomSite.url == site.url
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"このURLは既に登録されています: {existing.name}"
            )
        
        # サイトデータの準備
        site_data = site.dict()
        logger.info(f"Creating custom site with data: {site_data}")
        
        db_site = models.CustomSite(**site_data)
        db.add(db_site)
        db.commit()
        db.refresh(db_site)
        logger.info(f"Successfully created custom site: {db_site.id}")
        return db_site
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating custom site: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Site data: {site_data}")
        
        # より詳細なエラーメッセージ
        error_detail = str(e)
        if "value too long" in error_detail.lower() or "varchar" in error_detail.lower():
            error_detail = f"URLが長すぎる可能性があります。データベースのカラムサイズを確認してください: {error_detail}"
        
        raise HTTPException(
            status_code=500,
            detail=f"サイトの作成中にエラーが発生しました: {error_detail}"
        )


@router.put("/{site_id}", response_model=CustomSite)
def update_custom_site(
    site_id: int,
    site: CustomSiteUpdate,
    db: Session = Depends(get_db)
):
    db_site = db.query(models.CustomSite).filter(models.CustomSite.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Custom site not found")
    
    for key, value in site.dict(exclude_unset=True).items():
        setattr(db_site, key, value)
    
    db.commit()
    db.refresh(db_site)
    return db_site


@router.delete("/{site_id}")
def delete_custom_site(site_id: int, db: Session = Depends(get_db)):
    db_site = db.query(models.CustomSite).filter(models.CustomSite.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Custom site not found")
    
    db.delete(db_site)
    db.commit()
    return {"message": "Custom site deleted successfully"}


@router.post("/{site_id}/fetch")
async def fetch_custom_site(
    site_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    site = db.query(models.CustomSite).filter(models.CustomSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Custom site not found")
    
    background_tasks.add_task(fetch_site_content, site_id, db)
    
    return {"message": f"Fetching started for {site.name}"}


@router.post("/fetch-all")
async def fetch_all_custom_sites(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    background_tasks.add_task(fetch_all_sites_content, db)
    return {"message": "Fetching started for all enabled custom sites"}


@router.get("/{site_id}/logs", response_model=List[CustomSiteFetchLog])
def get_site_fetch_logs(
    site_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    logs = db.query(models.CustomSiteFetchLog).filter(
        models.CustomSiteFetchLog.site_id == site_id
    ).order_by(
        models.CustomSiteFetchLog.fetch_time.desc()
    ).offset(skip).limit(limit).all()
    
    return logs


async def fetch_site_content(site_id: int, db: Session):
    """単一サイトのコンテンツを取得"""
    site = db.query(models.CustomSite).filter(models.CustomSite.id == site_id).first()
    if not site:
        return
    
    scraper = CustomScraper()
    log = models.CustomSiteFetchLog(site_id=site_id, status="started")
    
    try:
        # サイト設定を辞書形式に変換
        site_config = {
            'name': site.name,
            'url': site.url,
            'type': site.site_type,
            'language': site.language,
            'category': site.category,
            'tags': site.tags or [],
            **(site.scraping_config or {})
        }
        
        # コンテンツを取得
        articles_data = await scraper.scrape_site(site_config)
        
        log.articles_found = len(articles_data)
        saved_count = 0
        
        # 記事を保存
        news_fetcher = NewsFetcher(db)
        for article_data in articles_data:
            try:
                news_fetcher._save_article(article_data)
                saved_count += 1
            except Exception as e:
                print(f"Error saving article: {str(e)}")
        
        log.articles_saved = saved_count
        log.status = "success"
        
        # サイトの最終取得時刻を更新
        site.last_fetched = datetime.utcnow()
        
    except Exception as e:
        log.status = "failed"
        log.error_message = str(e)
    
    finally:
        db.add(log)
        db.commit()
        await scraper.close()


async def fetch_all_sites_content(db: Session):
    """全ての有効なカスタムサイトのコンテンツを取得"""
    sites = db.query(models.CustomSite).filter(models.CustomSite.enabled == True).all()
    
    for site in sites:
        # 取得間隔をチェック
        if site.last_fetched:
            time_since_last = datetime.utcnow() - site.last_fetched
            if time_since_last.total_seconds() < site.fetch_interval_hours * 3600:
                continue  # まだ取得間隔に達していない
        
        await fetch_site_content(site.id, db)


# 事前定義サイトを追加するヘルパー関数
@router.post("/init-default-sites")
def initialize_default_sites(db: Session = Depends(get_db)):
    """デフォルトのカスタムサイトを初期化"""
    default_sites = [
        {
            "name": "Weekly Kaggle News",
            "url": "https://weeklykagglenews.substack.com/",
            "site_type": "substack",
            "language": "en",
            "category": "data-science",
            "tags": ["kaggle", "machine-learning", "competitions"],
            "fetch_interval_hours": 168  # 週1回
        },
        {
            "name": "The Batch (DeepLearning.AI)",
            "url": "https://www.deeplearning.ai/the-batch/",
            "site_type": "newsletter",
            "language": "en", 
            "category": "ai",
            "tags": ["deep-learning", "ai", "newsletter"],
            "fetch_interval_hours": 24
        },
        {
            "name": "TLDR Newsletter",
            "url": "https://tldr.tech/",
            "site_type": "newsletter",
            "language": "en",
            "category": "technology",
            "tags": ["tech", "startup", "newsletter"],
            "fetch_interval_hours": 24
        },
        {
            "name": "Qosmo Insights",
            "url": "https://qosmo.jp/",
            "site_type": "blog",
            "language": "ja",
            "category": "creative-ai",
            "tags": ["creative", "ai", "art"],
            "fetch_interval_hours": 24
        }
    ]
    
    created_sites = []
    for site_data in default_sites:
        # 既存サイトをチェック
        existing = db.query(models.CustomSite).filter(
            models.CustomSite.url == site_data["url"]
        ).first()
        
        if not existing:
            db_site = models.CustomSite(**site_data)
            db.add(db_site)
            created_sites.append(site_data["name"])
    
    db.commit()
    
    return {
        "message": f"Initialized {len(created_sites)} default sites",
        "sites": created_sites
    }


@router.post("/analyze-url")
async def analyze_site_url(url_data: dict, db: Session = Depends(get_db)):
    """URLを分析してサイト情報を自動取得"""
    url = url_data.get('url')
    if not url:
        raise HTTPException(status_code=400, detail="URLが必要です")
    
    try:
        analyzer = SiteAnalyzer()
        site_info = await analyzer.analyze_site(url)
        await analyzer.close()
        
        return {
            "success": True,
            "data": site_info
        }
        
    except Exception as e:
        logger.error(f"Error analyzing URL {url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"URLの分析中にエラーが発生しました: {str(e)}"
        )