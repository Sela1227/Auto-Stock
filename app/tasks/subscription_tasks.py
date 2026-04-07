"""
è¨‚é–±ç²¾é¸æŽ’ç¨‹ä»»å‹™
æ¯å°æ™‚æŠ“å–ä¸€æ¬¡ RSS
"""
import logging
from datetime import datetime

from app.database import SessionLocal
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


def scheduled_fetch_subscriptions():
    """
    æŽ’ç¨‹ä»»å‹™ï¼šæŠ“å–æ‰€æœ‰è¨‚é–±æº
    æ¯å°æ™‚åŸ·è¡Œä¸€æ¬¡
    """
    logger.info("=" * 40)
    logger.info(f"é–‹å§‹æŽ’ç¨‹æŠ“å–è¨‚é–±æº - {datetime.now()}")
    logger.info("=" * 40)
    
    try:
        db = SessionLocal()
        service = SubscriptionService(db)
        
        # æŠ“å–æ‰€æœ‰è¨‚é–±æºï¼ˆéžå›žæº¯æ¨¡å¼ï¼ŒåªæŠ“æ–°çš„ï¼‰
        result = service.fetch_all_sources(backfill=False)
        
        logger.info(f"æŠ“å–å®Œæˆ: æ–°å¢ž {result['total_new']}, æ›´æ–° {result['total_updated']}")
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"æŽ’ç¨‹æŠ“å–å¤±æ•—: {e}", exc_info=True)
        return None


def init_and_backfill():
    """
    åˆå§‹åŒ–ä¸¦å›žæº¯æŠ“å–
    é¦–æ¬¡éƒ¨ç½²æ™‚åŸ·è¡Œ
    """
    logger.info("=" * 40)
    logger.info("åˆå§‹åŒ–è¨‚é–±æºä¸¦å›žæº¯æŠ“å–")
    logger.info("=" * 40)
    
    try:
        db = SessionLocal()
        service = SubscriptionService(db)
        
        # åˆå§‹åŒ–é è¨­è¨‚é–±æº
        service.init_default_sources()
        
        # å›žæº¯æŠ“å– 30 å¤©
        result = service.fetch_all_sources(backfill=True)
        
        logger.info(f"å›žæº¯å®Œæˆ: æ–°å¢ž {result['total_new']}, æ›´æ–° {result['total_updated']}")
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"åˆå§‹åŒ–å¤±æ•—: {e}", exc_info=True)
        return None