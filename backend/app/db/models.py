from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False)
    source_url = Column(String(500), nullable=False, unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content = Column(Text)
    author = Column(String(200))
    published_at = Column(DateTime)
    language = Column(String(10))
    category = Column(String(50))
    tags = Column(JSON)
    image_url = Column(String(500))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    summaries = relationship("Summary", back_populates="article")
    analyses = relationship("Analysis", back_populates="article")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    language = Column(String(10), nullable=False)
    summary_text = Column(Text, nullable=False)
    key_points = Column(JSON)
    llm_model = Column(String(50))
    
    created_at = Column(DateTime, server_default=func.now())
    
    article = relationship("Article", back_populates="summaries")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    
    vocabulary_analysis = Column(JSON)  # TOEIC 800+ level words with explanations
    context_explanation = Column(Text)  # Background and context
    impact_analysis = Column(Text)  # Future impact analysis (500 chars)
    blog_titles = Column(JSON)  # Suggested blog/SNS titles
    llm_model = Column(String(50))
    
    created_at = Column(DateTime, server_default=func.now())
    
    article = relationship("Article", back_populates="analyses")


class FetchHistory(Base):
    __tablename__ = "fetch_history"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100))
    fetch_time = Column(DateTime, server_default=func.now())
    article_count = Column(Integer, default=0)
    status = Column(String(20))  # success, failed, partial
    error_message = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())