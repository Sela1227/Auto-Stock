"""
價格快取排程任務

排程邏輯：
1. 每 10 分鐘執行 run_update()
   - 自動判斷哪些市場開盤
   - 只更新開盤中的市場
   
2. 收盤後各執行一次（確保有最終收盤價）
   - 台股：13:35
   - 美股：05:05
"""
import logging
from datetime import datetime
from typing import Dict, Any

from app.database import SyncSessionLocal
from app.services.price_cache_service import PriceCacheService, get_market_status

logger = logging.getLogger(__name__)


class PriceCacheScheduler:
    """價格快取排程器"""
    
    def __init__(self):
        self.last_run: datetime = None
        self.last_result: Dict[str, Any] = {}
    
    def run_update(self) -> Dict[str, Any]:
        """
        執行價格快取更新（每 10 分鐘）
        
        自動判斷：
        - 台股開盤 (09:00-13:30) → 更新台股
        - 美股開盤 (21:30-05:00) → 更新美股
        - 加密貨幣 → 24 小時更新
        """
        market_status = get_market_status()
        
        # 如果所有股市都收盤，只更新加密貨幣
        if not market_status["tw_open"] and not market_status["us_open"]:
            logger.info("台股美股皆收盤，只更新加密貨幣")
        
        return self._do_update(force=False)
    
    def run_force_update(self) -> Dict[str, Any]:
        """
        強制更新所有市場（用於收盤後或手動觸發）
        """
        logger.info("強制更新所有市場")
        return self._do_update(force=True)
    
    def run_tw_close_update(self) -> Dict[str, Any]:
        """
        台股收盤後更新（13:35 執行）
        確保有最終收盤價
        """
        logger.info("台股收盤，執行最終更新")
        
        db = SyncSessionLocal()
        try:
            service = PriceCacheService(db)
            tracked = service.get_all_tracked_symbols()
            
            if tracked["tw_stocks"]:
                result = service.batch_update_stock_prices(tracked["tw_stocks"])
                logger.info(f"台股收盤更新完成: {result['updated']} 支")
                return result
            return {"updated": 0, "message": "無台股追蹤"}
            
        except Exception as e:
            logger.error(f"台股收盤更新失敗: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def run_us_close_update(self) -> Dict[str, Any]:
        """
        美股收盤後更新（05:05 執行）
        確保有最終收盤價
        """
        logger.info("美股收盤，執行最終更新")
        
        db = SyncSessionLocal()
        try:
            service = PriceCacheService(db)
            tracked = service.get_all_tracked_symbols()
            
            if tracked["us_stocks"]:
                result = service.batch_update_stock_prices(tracked["us_stocks"])
                logger.info(f"美股收盤更新完成: {result['updated']} 支")
                return result
            return {"updated": 0, "message": "無美股追蹤"}
            
        except Exception as e:
            logger.error(f"美股收盤更新失敗: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def _do_update(self, force: bool = False) -> Dict[str, Any]:
        """執行更新"""
        logger.info("=" * 50)
        logger.info(f"排程: 開始更新價格快取 (force={force})")
        logger.info(f"時間: {datetime.now()}")
        logger.info("=" * 50)
        
        db = SyncSessionLocal()
        
        try:
            service = PriceCacheService(db)
            result = service.update_all_tracked_prices(force=force)
            
            self.last_run = datetime.now()
            self.last_result = result
            
            logger.info(f"排程: 價格快取更新完成, 共 {result['total_updated']} 筆")
            
            return result
            
        except Exception as e:
            logger.error(f"排程: 價格快取更新失敗: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        finally:
            db.close()
    
    def get_status(self) -> Dict[str, Any]:
        """取得排程狀態"""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_result": self.last_result,
            "market_status": get_market_status(),
        }


# 全域實例
price_cache_scheduler = PriceCacheScheduler()


# ============================================================
# APScheduler 設定範例（加到 main.py）
# ============================================================

"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.tasks.price_cache_task import price_cache_scheduler

scheduler = AsyncIOScheduler()

# 1. 每 10 分鐘執行（自動判斷開盤時間）
scheduler.add_job(
    price_cache_scheduler.run_update,
    'interval',
    minutes=10,
    id='price_cache_interval',
    name='價格快取更新(每10分鐘)',
)

# 2. 台股收盤後執行一次（週一到週五 13:35）
scheduler.add_job(
    price_cache_scheduler.run_tw_close_update,
    CronTrigger(day_of_week='mon-fri', hour=13, minute=35),
    id='price_cache_tw_close',
    name='台股收盤更新',
)

# 3. 美股收盤後執行一次（週二到週六 05:05，對應美股週一到週五）
scheduler.add_job(
    price_cache_scheduler.run_us_close_update,
    CronTrigger(day_of_week='tue-sat', hour=5, minute=5),
    id='price_cache_us_close',
    name='美股收盤更新',
)

# 啟動排程
@app.on_event("startup")
async def startup_event():
    scheduler.start()
    # 啟動時執行一次（強制更新所有）
    price_cache_scheduler.run_force_update()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
"""
