"""
åƒ¹æ ¼å¿«å–æŽ’ç¨‹ä»»å‹™

æŽ’ç¨‹é‚è¼¯ï¼š
1. æ¯ 10 åˆ†é˜åŸ·è¡Œ run_update()
   - è‡ªå‹•åˆ¤æ–·å“ªäº›å¸‚å ´é–‹ç›¤
   - åªæ›´æ–°é–‹ç›¤ä¸­çš„å¸‚å ´
   
2. æ”¶ç›¤å¾Œå„åŸ·è¡Œä¸€æ¬¡ï¼ˆç¢ºä¿æœ‰æœ€çµ‚æ”¶ç›¤åƒ¹ï¼‰
   - å°è‚¡ï¼š13:35
   - ç¾Žè‚¡ï¼š05:05
"""
import logging
from datetime import datetime
from typing import Dict, Any

from app.database import SyncSessionLocal
from app.services.price_cache_service import PriceCacheService, get_market_status

logger = logging.getLogger(__name__)


class PriceCacheScheduler:
    """åƒ¹æ ¼å¿«å–æŽ’ç¨‹å™¨"""
    
    def __init__(self):
        self.last_run: datetime = None
        self.last_result: Dict[str, Any] = {}
    
    def run_update(self) -> Dict[str, Any]:
        """
        åŸ·è¡Œåƒ¹æ ¼å¿«å–æ›´æ–°ï¼ˆæ¯ 10 åˆ†é˜ï¼‰
        
        è‡ªå‹•åˆ¤æ–·ï¼š
        - å°è‚¡é–‹ç›¤ (09:00-13:30) â†’ æ›´æ–°å°è‚¡
        - ç¾Žè‚¡é–‹ç›¤ (21:30-05:00) â†’ æ›´æ–°ç¾Žè‚¡
        - åŠ å¯†è²¨å¹£ â†’ 24 å°æ™‚æ›´æ–°
        """
        market_status = get_market_status()
        
        # å¦‚æžœæ‰€æœ‰è‚¡å¸‚éƒ½æ”¶ç›¤ï¼Œåªæ›´æ–°åŠ å¯†è²¨å¹£
        if not market_status["tw_open"] and not market_status["us_open"]:
            logger.info("å°è‚¡ç¾Žè‚¡çš†æ”¶ç›¤ï¼Œåªæ›´æ–°åŠ å¯†è²¨å¹£")
        
        return self._do_update(force=False)
    
    def run_force_update(self) -> Dict[str, Any]:
        """
        å¼·åˆ¶æ›´æ–°æ‰€æœ‰å¸‚å ´ï¼ˆç”¨æ–¼æ”¶ç›¤å¾Œæˆ–æ‰‹å‹•è§¸ç™¼ï¼‰
        """
        logger.info("å¼·åˆ¶æ›´æ–°æ‰€æœ‰å¸‚å ´")
        return self._do_update(force=True)
    
    def run_tw_close_update(self) -> Dict[str, Any]:
        """
        å°è‚¡æ”¶ç›¤å¾Œæ›´æ–°ï¼ˆ13:35 åŸ·è¡Œï¼‰
        ç¢ºä¿æœ‰æœ€çµ‚æ”¶ç›¤åƒ¹
        """
        logger.info("å°è‚¡æ”¶ç›¤ï¼ŒåŸ·è¡Œæœ€çµ‚æ›´æ–°")
        
        db = SyncSessionLocal()
        try:
            service = PriceCacheService(db)
            tracked = service.get_all_tracked_symbols()
            
            if tracked["tw_stocks"]:
                result = service.batch_update_stock_prices(tracked["tw_stocks"])
                logger.info(f"å°è‚¡æ”¶ç›¤æ›´æ–°å®Œæˆ: {result['updated']} æ”¯")
                return result
            return {"updated": 0, "message": "ç„¡å°è‚¡è¿½è¹¤"}
            
        except Exception as e:
            logger.error(f"å°è‚¡æ”¶ç›¤æ›´æ–°å¤±æ•—: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def run_us_close_update(self) -> Dict[str, Any]:
        """
        ç¾Žè‚¡æ”¶ç›¤å¾Œæ›´æ–°ï¼ˆ05:05 åŸ·è¡Œï¼‰
        ç¢ºä¿æœ‰æœ€çµ‚æ”¶ç›¤åƒ¹
        """
        logger.info("ç¾Žè‚¡æ”¶ç›¤ï¼ŒåŸ·è¡Œæœ€çµ‚æ›´æ–°")
        
        db = SyncSessionLocal()
        try:
            service = PriceCacheService(db)
            tracked = service.get_all_tracked_symbols()
            
            if tracked["us_stocks"]:
                result = service.batch_update_stock_prices(tracked["us_stocks"])
                logger.info(f"ç¾Žè‚¡æ”¶ç›¤æ›´æ–°å®Œæˆ: {result['updated']} æ”¯")
                return result
            return {"updated": 0, "message": "ç„¡ç¾Žè‚¡è¿½è¹¤"}
            
        except Exception as e:
            logger.error(f"ç¾Žè‚¡æ”¶ç›¤æ›´æ–°å¤±æ•—: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def _do_update(self, force: bool = False) -> Dict[str, Any]:
        """åŸ·è¡Œæ›´æ–°"""
        logger.info("=" * 50)
        logger.info(f"æŽ’ç¨‹: é–‹å§‹æ›´æ–°åƒ¹æ ¼å¿«å– (force={force})")
        logger.info(f"æ™‚é–“: {datetime.now()}")
        logger.info("=" * 50)
        
        db = SyncSessionLocal()
        
        try:
            service = PriceCacheService(db)
            result = service.update_all_tracked_prices(force=force)
            
            self.last_run = datetime.now()
            self.last_result = result
            
            logger.info(f"æŽ’ç¨‹: åƒ¹æ ¼å¿«å–æ›´æ–°å®Œæˆ, å…± {result['total_updated']} ç­†")
            
            return result
            
        except Exception as e:
            logger.error(f"æŽ’ç¨‹: åƒ¹æ ¼å¿«å–æ›´æ–°å¤±æ•—: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            db.close()
    
    def get_status(self) -> Dict[str, Any]:
        """å–å¾—æŽ’ç¨‹ç‹€æ…‹"""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_result": self.last_result,
            "market_status": get_market_status(),
        }


# å…¨åŸŸå¯¦ä¾‹
price_cache_scheduler = PriceCacheScheduler()


# ============================================================
# APScheduler è¨­å®šç¯„ä¾‹ï¼ˆåŠ åˆ° main.pyï¼‰
# ============================================================

"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.tasks.price_cache_task import price_cache_scheduler

scheduler = AsyncIOScheduler()

# 1. æ¯ 10 åˆ†é˜åŸ·è¡Œï¼ˆè‡ªå‹•åˆ¤æ–·é–‹ç›¤æ™‚é–“ï¼‰
scheduler.add_job(
    price_cache_scheduler.run_update,
    'interval',
    minutes=10,
    id='price_cache_interval',
    name='åƒ¹æ ¼å¿«å–æ›´æ–°(æ¯10åˆ†é˜)',
)

# 2. å°è‚¡æ”¶ç›¤å¾ŒåŸ·è¡Œä¸€æ¬¡ï¼ˆé€±ä¸€åˆ°é€±äº” 13:35ï¼‰
scheduler.add_job(
    price_cache_scheduler.run_tw_close_update,
    CronTrigger(day_of_week='mon-fri', hour=13, minute=35),
    id='price_cache_tw_close',
    name='å°è‚¡æ”¶ç›¤æ›´æ–°',
)

# 3. ç¾Žè‚¡æ”¶ç›¤å¾ŒåŸ·è¡Œä¸€æ¬¡ï¼ˆé€±äºŒåˆ°é€±å…­ 05:05ï¼Œå°æ‡‰ç¾Žè‚¡é€±ä¸€åˆ°é€±äº”ï¼‰
scheduler.add_job(
    price_cache_scheduler.run_us_close_update,
    CronTrigger(day_of_week='tue-sat', hour=5, minute=5),
    id='price_cache_us_close',
    name='ç¾Žè‚¡æ”¶ç›¤æ›´æ–°',
)

# å•Ÿå‹•æŽ’ç¨‹
@app.on_event("startup")
async def startup_event():
    scheduler.start()
    # å•Ÿå‹•æ™‚åŸ·è¡Œä¸€æ¬¡ï¼ˆå¼·åˆ¶æ›´æ–°æ‰€æœ‰ï¼‰
    price_cache_scheduler.run_force_update()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
"""