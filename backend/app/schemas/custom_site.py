from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class CustomSiteBase(BaseModel):
    name: str
    url: str
    site_type: str  # substack, newsletter, blog, generic
    language: Optional[str] = 'en'
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    enabled: Optional[bool] = True
    scraping_config: Optional[Dict[str, Any]] = {}
    fetch_interval_hours: Optional[int] = 24


class CustomSiteCreate(CustomSiteBase):
    pass


class CustomSiteUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    site_type: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    enabled: Optional[bool] = None
    scraping_config: Optional[Dict[str, Any]] = None
    fetch_interval_hours: Optional[int] = None


class CustomSite(CustomSiteBase):
    id: int
    last_fetched: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomSiteFetchLogBase(BaseModel):
    articles_found: int = 0
    articles_saved: int = 0
    status: str
    error_message: Optional[str] = None


class CustomSiteFetchLogCreate(CustomSiteFetchLogBase):
    site_id: int


class CustomSiteFetchLog(CustomSiteFetchLogBase):
    id: int
    site_id: int
    fetch_time: datetime

    class Config:
        from_attributes = True