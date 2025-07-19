from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class AnalysisBase(BaseModel):
    vocabulary_analysis: Optional[Dict[str, str]] = {}
    context_explanation: Optional[str] = None
    impact_analysis: Optional[str] = None
    blog_titles: Optional[List[str]] = []
    llm_model: Optional[str] = None


class AnalysisCreate(AnalysisBase):
    article_id: int


class Analysis(AnalysisBase):
    id: int
    article_id: int
    created_at: datetime

    class Config:
        from_attributes = True