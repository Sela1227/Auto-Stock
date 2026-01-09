"""
============================================================
將以下程式碼加到 main.py
============================================================
"""

# ============================================================
# 1. 在檔案頂部加入 import
# ============================================================

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# ============================================================
# 2. 在 app = FastAPI(...) 之後加入
# ============================================================

# 建立排程器
scheduler = AsyncIOScheduler()


def update_price_cache():
    """排程任務：更新價格快取"""
    from app.database import SyncSessionLocal
    from app.services.price_cache_service import PriceCacheService
    
    db = SyncSessionLocal()
    try:
        service = PriceCacheService(db)
        result = service.update_all(force=False)
        print(f"[排程] 價格快取更新: {result['total_updated']} 筆")
    except Exception as e:
        print(f"[排程] 價格快取更新失敗: {e}")
    finally:
        db.close()


def update_price_cache_force():
    """強制更新所有價格（啟動時 / 收盤後）"""
    from app.database import SyncSessionLocal
    from app.services.price_cache_service import PriceCacheService
    
    db = SyncSessionLocal()
    try:
        service = PriceCacheService(db)
        result = service.update_all(force=True)
        print(f"[排程] 價格快取強制更新: {result['total_updated']} 筆")
    except Exception as e:
        print(f"[排程] 價格快取強制更新失敗: {e}")
    finally:
        db.close()


# 每 10 分鐘執行（自動判斷開盤時間）
scheduler.add_job(
    update_price_cache,
    'interval',
    minutes=10,
    id='price_cache_update',
    name='價格快取更新',
)

# 台股收盤後（週一到週五 13:35）
scheduler.add_job(
    update_price_cache_force,
    CronTrigger(day_of_week='mon-fri', hour=13, minute=35),
    id='tw_close_update',
    name='台股收盤更新',
)

# 美股收盤後（週二到週六 05:05）
scheduler.add_job(
    update_price_cache_force,
    CronTrigger(day_of_week='tue-sat', hour=5, minute=5),
    id='us_close_update',
    name='美股收盤更新',
)


# ============================================================
# 3. 修改 startup 事件
# ============================================================

@app.on_event("startup")
async def startup_event():
    # ... 你現有的 startup 程式碼 ...
    
    # 加入以下兩行
    scheduler.start()
    update_price_cache_force()  # 啟動時更新一次


@app.on_event("shutdown")
async def shutdown_event():
    # ... 你現有的 shutdown 程式碼 ...
    
    # 加入以下一行
    scheduler.shutdown()


# ============================================================
# 4. 確認有安裝 APScheduler
# ============================================================
# pip install apscheduler
# 或在 requirements.txt 加入: apscheduler>=3.10.0
