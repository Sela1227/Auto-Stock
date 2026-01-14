"""
訂閱精選排程任務
每小時抓取一次 RSS
"""
import logging
from datetime import datetime

from app.database import SessionLocal
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


def scheduled_fetch_subscriptions():
    """
    排程任務：抓取所有訂閱源
    每小時執行一次
    """
    logger.info("=" * 40)
    logger.info(f"開始排程抓取訂閱源 - {datetime.now()}")
    logger.info("=" * 40)
    
    try:
        db = SessionLocal()
        service = SubscriptionService(db)
        
        # 抓取所有訂閱源（非回溯模式，只抓新的）
        result = service.fetch_all_sources(backfill=False)
        
        logger.info(f"抓取完成: 新增 {result['total_new']}, 更新 {result['total_updated']}")
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"排程抓取失敗: {e}", exc_info=True)
        return None


def init_and_backfill():
    """
    初始化並回溯抓取
    首次部署時執行
    """
    logger.info("=" * 40)
    logger.info("初始化訂閱源並回溯抓取")
    logger.info("=" * 40)
    
    try:
        db = SessionLocal()
        service = SubscriptionService(db)
        
        # 初始化預設訂閱源
        service.init_default_sources()
        
        # 回溯抓取 30 天
        result = service.fetch_all_sources(backfill=True)
        
        logger.info(f"回溯完成: 新增 {result['total_new']}, 更新 {result['total_updated']}")
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"初始化失敗: {e}", exc_info=True)
        return None
