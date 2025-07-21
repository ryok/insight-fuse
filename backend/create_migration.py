"""
カスタムサイトテーブルのマイグレーションスクリプト
URLカラムのサイズを拡張
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_custom_sites_table():
    """custom_sitesテーブルのURLカラムを更新"""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # トランザクション開始
            trans = conn.begin()
            
            try:
                # まずテーブルが存在するか確認
                result = conn.execute(text("""
                    SELECT column_name, data_type, character_maximum_length 
                    FROM information_schema.columns 
                    WHERE table_name = 'custom_sites' AND column_name = 'url'
                """))
                
                row = result.fetchone()
                if row:
                    current_length = row[2]
                    logger.info(f"現在のURLカラムの長さ: {current_length}")
                    
                    if current_length < 1000:
                        # URLカラムのサイズを拡張
                        conn.execute(text("""
                            ALTER TABLE custom_sites 
                            ALTER COLUMN url TYPE VARCHAR(1000)
                        """))
                        logger.info("URLカラムを1000文字に拡張しました")
                    else:
                        logger.info("URLカラムは既に十分な長さです")
                else:
                    logger.error("custom_sitesテーブルまたはurlカラムが見つかりません")
                
                trans.commit()
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    update_custom_sites_table()