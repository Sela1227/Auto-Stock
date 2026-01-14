"""
FastAPI 主程式
股票技術分析系統 API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import logging
import os
from datetime import datetime

from app.config import settings
from app.database import init_db
from app.logging_config import setup_logging

# 初始化日誌系統（在其他 import 之前）
setup_logging(
    log_level="DEBUG" if settings.DEBUG else "INFO",
    log_to_file=True
)

# 確保所有 models 被載入，這樣 Base.metadata 才會包含所有表格
from app.models import (
    User, Watchlist, StockPrice, CryptoPrice, 
    MarketSentiment, Notification,
    UserIndicatorSettings, UserAlertSettings, UserIndicatorParams,
    IndexPrice, DividendHistory,
    Comparison,
    StockPriceCache,
    PortfolioTransaction, PortfolioHolding, ExchangeRate,
)
from app.models.user import LoginLog, TokenBlacklist, SystemConfig

from app.routers import (
    auth_router,
    stock_router,
    crypto_router,
    watchlist_router,
    settings_router,
    admin_router,
    compare_router,
    portfolio_router,
)
from app.routers.market import router as market_router
from app.routers.subscription import router as subscription_router  # 📡 訂閱精選

# 排程器
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# 建立排程器
scheduler = AsyncIOScheduler()


# ============================================================
# 🆕 交易時間判斷（優化版）
# ============================================================

def is_tw_market_hours() -> bool:
    """判斷是否在台股交易時間（週一到週五 09:00-13:30 台北時間）"""
    from datetime import timezone, timedelta
    tw_tz = timezone(timedelta(hours=8))
    now = datetime.now(tw_tz)
    
    # 週末不開盤
    if now.weekday() >= 5:
        return False
    
    # 09:00 - 13:30
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=13, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close


def is_us_market_hours() -> bool:
    """判斷是否在美股交易時間（週一到週五 21:30-05:00 台北時間）"""
    from datetime import timezone, timedelta
    tw_tz = timezone(timedelta(hours=8))
    now = datetime.now(tw_tz)
    
    # 週末不開盤（週六 05:00 後、週日全天）
    if now.weekday() == 6:  # 週日
        return False
    if now.weekday() == 5 and now.hour >= 5:  # 週六 05:00 後
        return False
    
    # 21:30 - 05:00 (跨日)
    hour = now.hour
    minute = now.minute
    
    if hour >= 21 and minute >= 30:
        return True
    if hour >= 22:
        return True
    if hour < 5:
        return True
    
    return False


def is_any_market_open() -> bool:
    """判斷是否有任何市場開盤"""
    return is_tw_market_hours() or is_us_market_hours()


# ============================================================
# 價格快取更新函數（優化版）
# ============================================================

def update_price_cache():
    """
    排程任務：更新價格快取
    🆕 優化：只在交易時間執行
    """
    # 檢查是否有市場開盤
    if not is_any_market_open():
        logger.debug("[排程] 非交易時間，跳過價格更新")
        return
    
    from app.database import SyncSessionLocal
    from app.services.price_cache_service import PriceCacheService

    logger.info("[排程] 開始更新價格快取...")
    db = SyncSessionLocal()
    try:
        service = PriceCacheService(db)
        result = service.update_all(force=False)
        logger.info(f"[排程] 價格快取更新完成: {result['total_updated']} 筆")
    except Exception as e:
        logger.error(f"[排程] 價格快取更新失敗: {e}")
    finally:
        db.close()


def update_price_cache_force():
    """強制更新所有價格（收盤後）"""
    from app.database import SyncSessionLocal
    from app.services.price_cache_service import PriceCacheService

    logger.info("[排程] 強制更新所有價格快取...")
    db = SyncSessionLocal()
    try:
        service = PriceCacheService(db)
        result = service.update_all(force=True)
        logger.info(f"[排程] 價格快取強制更新完成: {result['total_updated']} 筆")
    except Exception as e:
        logger.error(f"[排程] 價格快取強制更新失敗: {e}")
    finally:
        db.close()


# ============================================================
# 匯率更新函數
# ============================================================

def update_exchange_rate():
    """排程任務：更新 USD/TWD 匯率"""
    from app.database import SyncSessionLocal
    from app.services.exchange_rate_service import update_exchange_rate_sync

    logger.info("[排程] 開始更新匯率...")
    db = SyncSessionLocal()
    try:
        rate = update_exchange_rate_sync(db)
        logger.info(f"[排程] 匯率更新完成: USD/TWD = {rate:.4f}")
    except Exception as e:
        logger.error(f"[排程] 匯率更新失敗: {e}")
    finally:
        db.close()


# ============================================================
# 📡 訂閱源抓取函數
# ============================================================

def fetch_subscription_sources():
    """排程任務：抓取訂閱源更新"""
    from app.database import SyncSessionLocal
    from app.services.subscription_service import SubscriptionService

    logger.info("[排程] 開始抓取訂閱源...")
    db = SyncSessionLocal()
    try:
        service = SubscriptionService(db)
        result = service.fetch_all_sources(backfill=False)
        logger.info(f"[排程] 訂閱源抓取完成: {result}")
    except Exception as e:
        logger.error(f"[排程] 訂閱源抓取失敗: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # ★★★ 診斷資料庫連線 ★★★
    from app.database import database_url, is_postgres
    db_type = "PostgreSQL" if is_postgres(database_url) else "SQLite"
    logger.info(f"★★★ Database Type: {db_type} ★★★")
    if is_postgres(database_url):
        # 隱藏密碼
        safe_url = database_url.split("@")[-1] if "@" in database_url else database_url
        logger.info(f"★★★ Database Host: {safe_url} ★★★")
    else:
        logger.warning("⚠️ 使用 SQLite！資料會在重新部署後遺失！")
        logger.warning("⚠️ 請設定 DATABASE_URL 環境變數指向 PostgreSQL")

    await init_db()
    logger.info("Database initialized")

    # ============================================================
    # 🆕 優化後的排程設定
    # ============================================================

    # 價格快取：每 30 分鐘（原本 10 分鐘）
    # 內部會判斷交易時間，非交易時間自動跳過
    scheduler.add_job(
        update_price_cache,
        'interval',
        minutes=30,  # 🆕 從 10 分鐘改為 30 分鐘
        id='price_cache_update',
        name='價格快取更新(每30分鐘)',
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
    # 匯率排程（每天 2 次：09:00、17:00）
    # 🆕 從 3 次改為 2 次
    # ============================================================

    scheduler.add_job(
        update_exchange_rate,
        CronTrigger(hour=9, minute=0),
        id='exchange_rate_morning',
        name='匯率更新(早)',
    )

    scheduler.add_job(
        update_exchange_rate,
        CronTrigger(hour=17, minute=0),
        id='exchange_rate_evening',
        name='匯率更新(晚)',
    )

    # ============================================================
    # 📡 訂閱源排程
    # 🆕 從每小時改為每天 3 次（08:00、12:00、20:00）
    # ============================================================

    scheduler.add_job(
        fetch_subscription_sources,
        CronTrigger(hour=8, minute=0),
        id='subscription_fetch_morning',
        name='訂閱源抓取(早)',
    )

    scheduler.add_job(
        fetch_subscription_sources,
        CronTrigger(hour=12, minute=0),
        id='subscription_fetch_noon',
        name='訂閱源抓取(中)',
    )

    scheduler.add_job(
        fetch_subscription_sources,
        CronTrigger(hour=20, minute=0),
        id='subscription_fetch_evening',
        name='訂閱源抓取(晚)',
    )

    # 啟動排程器
    scheduler.start()
    logger.info("排程器已啟動（優化版：價格快取30分鐘 + 交易時間判斷）")

    # 🆕 啟動時只更新匯率，價格讓排程處理（減少啟動負擔）
    try:
        update_exchange_rate()
        # 只在交易時間才更新價格
        if is_any_market_open():
            update_price_cache()
    except Exception as e:
        logger.error(f"啟動時更新失敗: {e}")

    yield

    # 關閉時
    scheduler.shutdown()
    logger.info("Shutting down...")


# 建立 FastAPI 應用程式
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 📈 SELA 自動選股系統 API

多用戶股票與加密貨幣技術分析平台

### 功能特色

- **技術指標**: MA, RSI, MACD, KD, 布林通道, OBV
- **智能訊號**: 黃金交叉、死亡交叉、超買超賣、突破預警
- **綜合評分**: 多指標共振分析
- **市場情緒**: CNN Fear & Greed / Alternative.me
- **圖表生成**: 完整技術分析圖表
- **報酬率比較**: 多標的年化報酬率 (CAGR) 比較
- **個人投資記錄**: 交易紀錄、持股管理、損益追蹤
- **訂閱精選**: 自動追蹤投資專家精選股票 📡

### 認證方式

使用 LINE Login 登入，取得 JWT Token 後在 Header 帶入：
```
Authorization: Bearer {token}
```
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 正式環境應限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(auth_router)
app.include_router(stock_router)
app.include_router(crypto_router)
app.include_router(watchlist_router)
app.include_router(settings_router)
app.include_router(admin_router)
app.include_router(market_router)
app.include_router(compare_router)
app.include_router(portfolio_router)
app.include_router(subscription_router)  # 📡 訂閱精選

# 掛載靜態檔案
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path, html=True), name="static")


# 根路徑 - 重導向到登入頁
@app.get("/", tags=["系統"])
async def root():
    """重導向到首頁"""
    return RedirectResponse(url="/static/index.html")


# API 狀態
@app.get("/api", tags=["系統"])
async def api_root():
    """API 根路徑"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


# 健康檢查
@app.get("/health", tags=["系統"])
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


# 🆕 排程狀態 API
@app.get("/api/admin/scheduler-status", tags=["管理"])
async def scheduler_status():
    """查看排程器狀態"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs,
        "market_status": {
            "tw_open": is_tw_market_hours(),
            "us_open": is_us_market_hours(),
            "any_open": is_any_market_open(),
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
