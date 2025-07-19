from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db import models
from app.schemas.summary import Summary, SummaryCreate
from app.services.llm_service import LLMService

router = APIRouter()


@router.get("/article/{article_id}", response_model=List[Summary])
def get_article_summaries(article_id: int, db: Session = Depends(get_db)):
    summaries = db.query(models.Summary).filter(models.Summary.article_id == article_id).all()
    return summaries


@router.get("/{summary_id}", response_model=Summary)
def get_summary(summary_id: int, db: Session = Depends(get_db)):
    summary = db.query(models.Summary).filter(models.Summary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary


@router.post("/article/{article_id}", response_model=Summary)
async def create_summary(
    article_id: int, 
    language: str,
    db: Session = Depends(get_db)
):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    existing_summary = db.query(models.Summary).filter(
        models.Summary.article_id == article_id,
        models.Summary.language == language
    ).first()
    
    if existing_summary:
        return existing_summary
    
    llm_service = LLMService()
    summary_data = await llm_service.generate_summary(article.content, language)
    
    db_summary = models.Summary(
        article_id=article_id,
        language=language,
        summary_text=summary_data["summary"],
        key_points=summary_data["key_points"],
        llm_model=summary_data["model"]
    )
    
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    
    return db_summary