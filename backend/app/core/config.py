from pydantic_settings import BaseSettings
from typing import List, Optional, Union
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "InsightFuse"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/insightfuse"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    
    # News Settings
    NEWS_SOURCES: Union[str, List[str]] = "techcrunch,ars-technica,the-verge,hacker-news"
    NEWS_LANGUAGES: Union[str, List[str]] = "en,ja,zh"
    NEWS_FETCH_LIMIT: int = 50
    
    @property
    def news_sources_list(self) -> List[str]:
        if isinstance(self.NEWS_SOURCES, str):
            return [s.strip() for s in self.NEWS_SOURCES.split(',')]
        return self.NEWS_SOURCES
    
    @property
    def news_languages_list(self) -> List[str]:
        if isinstance(self.NEWS_LANGUAGES, str):
            return [s.strip() for s in self.NEWS_LANGUAGES.split(',')]
        return self.NEWS_LANGUAGES
    
    # LLM Settings
    LLM_MODEL: str = "gpt-4-turbo-preview"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    
    # App Settings
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()