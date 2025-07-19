from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.news_fetcher import NewsFetcher
from app.schemas.fetch import FetchResponse, FetchStatus

router = APIRouter()


@router.post("/news", response_model=FetchResponse)
async def fetch_news(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    news_fetcher = NewsFetcher(db)
    
    background_tasks.add_task(news_fetcher.fetch_all_sources)
    
    return FetchResponse(
        status="started",
        message="News fetching started in background"
    )


@router.get("/status", response_model=FetchStatus)
def get_fetch_status(db: Session = Depends(get_db)):
    from sqlalchemy import func
    from app.db import models
    
    latest_fetch = db.query(models.FetchHistory).order_by(
        models.FetchHistory.fetch_time.desc()
    ).first()
    
    total_articles = db.query(func.count(models.Article.id)).scalar()
    
    return FetchStatus(
        last_fetch=latest_fetch.fetch_time if latest_fetch else None,
        total_articles=total_articles,
        status=latest_fetch.status if latest_fetch else "never_run"
    )