from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SummaryBase(BaseModel):
    language: str
    summary_text: str
    key_points: Optional[List[str]] = []
    llm_model: Optional[str] = None


class SummaryCreate(SummaryBase):
    article_id: int


class Summary(SummaryBase):
    id: int
    article_id: int
    created_at: datetime

    class Config:
        from_attributes = True