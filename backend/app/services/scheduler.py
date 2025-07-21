import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import models
from app.services.custom_scraper import CustomScraper
from app.services.news_fetcher import NewsFetcher
import logging

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self.running = False
        self.db = SessionLocal()
    
    def start(self):
        """スケジューラーを開始"""
        self.running = True
        
        # 基本的なニュース取得（1時間ごと）
        schedule.every().hour.do(self._schedule_news_fetch)
        
        # カスタムサイト取得（30分ごとにチェック）
        schedule.every(30).minutes.do(self._schedule_custom_sites_fetch)
        
        # 古いデータのクリーンアップ（毎日午前2時）
        schedule.every().day.at("02:00").do(self._schedule_cleanup)
        
        logger.info("Task scheduler started")
        
        # スケジューラーのメインループ
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
    
    def stop(self):
        """スケジューラーを停止"""
        self.running = False
        self.db.close()
        logger.info("Task scheduler stopped")
    
    def _schedule_news_fetch(self):
        """通常のニュース取得をスケジュール"""
        try:
            asyncio.run(self._fetch_regular_news())
        except Exception as e:
            logger.error(f"Error in scheduled news fetch: {str(e)}")
    
    def _schedule_custom_sites_fetch(self):
        """カスタムサイト取得をスケジュール"""
        try:
            asyncio.run(self._fetch_custom_sites())
        except Exception as e:
            logger.error(f"Error in scheduled custom sites fetch: {str(e)}")
    
    def _schedule_cleanup(self):
        """データクリーンアップをスケジュール"""
        try:
            self._cleanup_old_data()
        except Exception as e:
            logger.error(f"Error in scheduled cleanup: {str(e)}")
    
    async def _fetch_regular_news(self):
        """通常のニュースソースから記事を取得"""
        logger.info("Starting scheduled news fetch")
        
        news_fetcher = NewsFetcher(self.db)
        await news_fetcher.fetch_all_sources()
        
        logger.info("Completed scheduled news fetch")
    
    async def _fetch_custom_sites(self):
        """カスタムサイトから記事を取得"""
        logger.info("Starting scheduled custom sites fetch")
        
        # 取得が必要なサイトを検索
        sites_to_fetch = self._get_sites_due_for_fetch()
        
        if not sites_to_fetch:
            logger.info("No custom sites due for fetching")
            return
        
        scraper = CustomScraper()
        
        try:
            for site in sites_to_fetch:
                await self._fetch_single_site(site, scraper)
        finally:
            await scraper.close()
        
        logger.info(f"Completed scheduled fetch for {len(sites_to_fetch)} custom sites")
    
    def _get_sites_due_for_fetch(self) -> List[models.CustomSite]:
        """取得が必要なカスタムサイトを返す"""
        current_time = datetime.utcnow()
        
        # 有効なサイトを取得
        sites = self.db.query(models.CustomSite).filter(
            models.CustomSite.enabled == True
        ).all()
        
        sites_due = []
        for site in sites:
            if site.last_fetched is None:
                # 一度も取得していない場合は取得対象
                sites_due.append(site)
            else:
                # 前回取得から指定時間が経過している場合
                time_since_last = current_time - site.last_fetched
                if time_since_last.total_seconds() >= site.fetch_interval_hours * 3600:
                    sites_due.append(site)
        
        return sites_due
    
    async def _fetch_single_site(self, site: models.CustomSite, scraper: CustomScraper):
        """単一のカスタムサイトを取得"""
        log = models.CustomSiteFetchLog(
            site_id=site.id,
            status="started"
        )
        
        try:
            logger.info(f"Fetching content from {site.name}")
            
            # サイト設定を辞書形式に変換
            site_config = {
                'name': site.name,
                'url': site.url,
                'type': site.site_type,
                'language': site.language,
                'category': site.category,
                'tags': site.tags or [],
                **(site.scraping_config or {})
            }
            
            # コンテンツを取得
            articles_data = await scraper.scrape_site(site_config)
            
            log.articles_found = len(articles_data)
            saved_count = 0
            
            # 記事を保存
            news_fetcher = NewsFetcher(self.db)
            for article_data in articles_data:
                try:
                    news_fetcher._save_article(article_data)
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"Error saving article from {site.name}: {str(e)}")
            
            log.articles_saved = saved_count
            log.status = "success"
            
            # サイトの最終取得時刻を更新
            site.last_fetched = datetime.utcnow()
            
            logger.info(f"Successfully fetched {saved_count}/{len(articles_data)} articles from {site.name}")
            
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            logger.error(f"Error fetching from {site.name}: {str(e)}")
        
        finally:
            self.db.add(log)
            self.db.commit()
    
    def _cleanup_old_data(self):
        """古いデータをクリーンアップ"""
        logger.info("Starting data cleanup")
        
        # 30日より古い記事を削除
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # 古い記事を削除
        old_articles = self.db.query(models.Article).filter(
            models.Article.created_at < cutoff_date
        ).count()
        
        if old_articles > 0:
            self.db.query(models.Article).filter(
                models.Article.created_at < cutoff_date
            ).delete()
            
            logger.info(f"Deleted {old_articles} old articles")
        
        # 古いフェッチログを削除（7日より古い）
        log_cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        old_logs = self.db.query(models.CustomSiteFetchLog).filter(
            models.CustomSiteFetchLog.fetch_time < log_cutoff_date
        ).count()
        
        if old_logs > 0:
            self.db.query(models.CustomSiteFetchLog).filter(
                models.CustomSiteFetchLog.fetch_time < log_cutoff_date
            ).delete()
            
            logger.info(f"Deleted {old_logs} old fetch logs")
        
        # 古いフェッチ履歴を削除
        old_history = self.db.query(models.FetchHistory).filter(
            models.FetchHistory.created_at < log_cutoff_date
        ).count()
        
        if old_history > 0:
            self.db.query(models.FetchHistory).filter(
                models.FetchHistory.created_at < log_cutoff_date
            ).delete()
            
            logger.info(f"Deleted {old_history} old fetch history records")
        
        self.db.commit()
        logger.info("Completed data cleanup")


# スケジューラーのインスタンス
scheduler = TaskScheduler()


def start_scheduler():
    """スケジューラーを開始する関数"""
    scheduler.start()


def stop_scheduler():
    """スケジューラーを停止する関数"""
    scheduler.stop()