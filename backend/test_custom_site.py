#!/usr/bin/env python3
"""
カスタムサイト作成のテストスクリプト
エラーの詳細を確認するために使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine
from app.db import models
from sqlalchemy import inspect

def test_db_schema():
    """データベーススキーマを確認"""
    print("=== データベーススキーマの確認 ===")
    
    inspector = inspect(engine)
    
    # custom_sitesテーブルの確認
    if 'custom_sites' in inspector.get_table_names():
        columns = inspector.get_columns('custom_sites')
        for column in columns:
            if column['name'] == 'url':
                print(f"URLカラム: タイプ={column['type']}, nullable={column['nullable']}")
                if hasattr(column['type'], 'length'):
                    print(f"URLカラムの長さ: {column['type'].length}")
    else:
        print("custom_sitesテーブルが存在しません")
        
def test_create_site():
    """サイト作成のテスト"""
    print("\n=== サイト作成テスト ===")
    
    db = SessionLocal()
    
    test_url = "https://us20.campaign-archive.com/home/?u=49bcfb001a9bac61c07e60864&id=a136f2fa8e"
    print(f"URL長: {len(test_url)} 文字")
    
    try:
        # 既存のレコードを確認
        existing = db.query(models.CustomSite).filter(
            models.CustomSite.url == test_url
        ).first()
        
        if existing:
            print(f"このURLは既に登録されています: {existing.name}")
            return
            
        # 新規作成
        site = models.CustomSite(
            name="Qosmo Insights Test",
            url=test_url,
            site_type="newsletter",
            language="ja",
            category="creative-ai",
            tags=["creative", "ai", "art"],
            enabled=True,
            fetch_interval_hours=24
        )
        
        db.add(site)
        db.commit()
        db.refresh(site)
        
        print(f"サイトが正常に作成されました: ID={site.id}")
        
    except Exception as e:
        print(f"エラーが発生しました: {type(e).__name__}")
        print(f"エラーメッセージ: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_db_schema()
    test_create_site()