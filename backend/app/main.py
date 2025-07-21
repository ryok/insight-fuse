from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading
from app.core.config import settings
from app.api.v1.router import api_router
from app.db.database import engine
from app.db import models
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリケーション起動時
    models.Base.metadata.create_all(bind=engine)
    
    # カスタムサイトテーブルのURLカラムを更新（必要な場合）
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # PostgreSQLの場合
            try:
                conn.execute(text("""
                    ALTER TABLE custom_sites 
                    ALTER COLUMN url TYPE VARCHAR(1000)
                """))
                conn.commit()
                print("Updated custom_sites.url column to VARCHAR(1000)")
            except Exception as e:
                # 既に更新済みまたはエラーの場合は無視
                print(f"Column update skipped or failed: {str(e)}")
    except Exception as e:
        print(f"Database migration check failed: {str(e)}")
    
    # バックグラウンドでスケジューラーを開始
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    yield
    
    # アプリケーション終了時
    stop_scheduler()


app = FastAPI(
    title="InsightFuse API",
    description="AI-powered news aggregation and analysis platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to InsightFuse API", "version": "1.0.0"}