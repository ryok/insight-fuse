from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.database import get_db
from app.db import models
from app.schemas.article import Article, ArticleCreate, ArticleUpdate

router = APIRouter()


@router.get("/", response_model=List[Article])
def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    language: Optional[str] = None,
    source: Optional[str] = None,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    query = db.query(models.Article)
    
    if language:
        query = query.filter(models.Article.language == language)
    if source:
        query = query.filter(models.Article.source == source)
    
    since_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(models.Article.published_at >= since_date)
    
    articles = query.order_by(models.Article.published_at.desc()).offset(skip).limit(limit).all()
    return articles


@router.get("/{article_id}", response_model=Article)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/", response_model=Article)
def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    db_article = models.Article(**article.dict())
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


@router.put("/{article_id}", response_model=Article)
def update_article(article_id: int, article: ArticleUpdate, db: Session = Depends(get_db)):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    for key, value in article.dict(exclude_unset=True).items():
        setattr(db_article, key, value)
    
    db.commit()
    db.refresh(db_article)
    return db_article


@router.delete("/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    db_article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    db.delete(db_article)
    db.commit()
    return {"message": "Article deleted successfully"}