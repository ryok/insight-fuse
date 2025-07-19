from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.schemas.analysis import Analysis, AnalysisCreate
from app.services.llm_service import LLMService

router = APIRouter()


@router.get("/article/{article_id}", response_model=Analysis)
def get_article_analysis(article_id: int, db: Session = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(models.Analysis.article_id == article_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.post("/article/{article_id}", response_model=Analysis)
async def create_analysis(article_id: int, db: Session = Depends(get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    existing_analysis = db.query(models.Analysis).filter(
        models.Analysis.article_id == article_id
    ).first()
    
    if existing_analysis:
        return existing_analysis
    
    llm_service = LLMService()
    analysis_data = await llm_service.generate_analysis(article.content, article.title)
    
    db_analysis = models.Analysis(
        article_id=article_id,
        vocabulary_analysis=analysis_data["vocabulary"],
        context_explanation=analysis_data["context"],
        impact_analysis=analysis_data["impact"],
        blog_titles=analysis_data["blog_titles"],
        llm_model=analysis_data["model"]
    )
    
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    
    return db_analysis