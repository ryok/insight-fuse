from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FetchResponse(BaseModel):
    status: str
    message: str


class FetchStatus(BaseModel):
    last_fetch: Optional[datetime] = None
    total_articles: int = 0
    status: str = "never_run"