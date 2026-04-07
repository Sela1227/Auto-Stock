"""
FastAPI 主程式
股票技術分析系統 API

🚀 V1.02 極簡排程版 - 2026-04-07
- 移除所有自動更新排程
- 價格查詢改為純即時查（用戶查才查）
- 每天只預查一次（美股開盤前 21:00）
- 情緒指數每天 2 次
- 匯率每天 1 次
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import logging
import os
from datetime import datetime, timezone, timedelta

from app.config import settings
from app.database import init_db
from app.logging_config import setup_logging

# 初始化日誌系統（在其他 import 之前）
setup_logging(
    log_level="DEBUG" if settings.DEBUG else "INFO",
    log_to_file=True
)

# 確保所有 models 被載入
from app.models import (
    User, Watchlist, StockPrice, CryptoPrice, 
    MarketSentiment, Notification,
    UserIndicatorSettings, UserAlertSettings, UserIndicatorParams,
    IndexPrice, DividendHistory,
    Comparison,
    StockPriceCache,
    PortfolioTransaction, PortfolioHolding, ExchangeRate,
    UserTag, watchlist_tags,
    StockInfo,
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
from app.routers.subscription import router as subscription_router
from app.routers.tags import router as tags_router
from app.routers.stock_info import router as stock_info_router
from app.routers.broker import router as broker_router

# 排程器
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# 建立排程器
scheduler = AsyncIOScheduler()

# 台北時區
TW_TZ = timezone(timedelta(hours=8))


# ============================================================
# 排程任務函數
# ============================================================

def update_exchange_rate():
    """更新匯率"""
    from app.database import SyncSessionLocal
    from app.services.exchange_rate_service import ExchangeRateService
    
    logger.info("⏰ [排程] 更新匯率...")
    db = SyncSessionLocal()
    try:
        service = ExchangeRateService(db)
        rate = service.update_usd_twd_rate()
        if rate:
            logger.info(f"✅ 匯率更新成功: USD/TWD = {rate}")
        else:
            logger.warning("⚠️ 匯率更新失敗")
    except Exception as e:
        logger.error(f"❌ 匯率更新錯誤: {e}")
    finally:
        db.close()


def update_market_sentiment():
    """更新市場情緒（存入 DB）"""
    from app.database import SyncSessionLocal
    from app.services.market_service import MarketService
    
    logger.info("⏰ [排程] 更新市場情緒...")
    db = SyncSessionLocal()
    try:
        service = MarketService(db)
        result = service.update_today_sentiment()
        logger.info(f"✅ 情緒更新: stock={result.get('stock')}, crypto={result.get('crypto')}")
    except Exception as e:
        logger.error(f"❌ 情緒更新錯誤: {e}")
    finally:
        db.close()


def update_indices():
    """更新四大指數"""
    from app.database import SyncSessionLocal
    from app.services.market_service import MarketService
    
    logger.info("⏰ [排程] 更新四大指數...")
    db = SyncSessionLocal()
    try:
        service = MarketService(db)
        result = service.fetch_and_save_all_indices(period="5d")
        logger.info(f"✅ 指數更新完成: {result}")
    except Exception as e:
        logger.error(f"❌ 指數更新錯誤: {e}")
    finally:
        db.close()


def daily_preload():
    """
    每日預載（美股開盤前 21:00）
    - 更新情緒指數
    - 更新四大指數
    - 更新匯率
    - 🆕 V1.05 預計算追蹤清單技術指標
    """
    logger.info("⏰ [排程] === 每日預載開始 ===")
    
    try:
        update_market_sentiment()
        update_indices()
        update_exchange_rate()
        precompute_indicators()  # 🆕 V1.05
        logger.info("✅ [排程] === 每日預載完成 ===")
    except Exception as e:
        logger.error(f"❌ 每日預載錯誤: {e}")


def precompute_indicators():
    """🆕 V1.05 預計算追蹤清單股票的技術指標"""
    from app.database import SyncSessionLocal
    from app.services.analysis_cache_service import AnalysisCacheService
    
    logger.info("⏰ [排程] 預計算技術指標...")
    db = SyncSessionLocal()
    try:
        service = AnalysisCacheService(db)
        result = service.precompute_indicators_for_watchlist()
        logger.info(f"✅ 指標預計算: 成功 {result['success']}, 失敗 {result['failed']}")
    except Exception as e:
        logger.error(f"❌ 指標預計算錯誤: {e}")
    finally:
        db.close()


def clear_expired_caches():
    """🆕 V1.05 清除過期快取"""
    from app.database import SyncSessionLocal
    from app.services.analysis_cache_service import AnalysisCacheService
    
    logger.info("⏰ [排程] 清除過期快取...")
    db = SyncSessionLocal()
    try:
        service = AnalysisCacheService(db)
        result = service.clear_expired_caches()
        logger.info(f"✅ 快取清除: {result}")
    except Exception as e:
        logger.error(f"❌ 快取清除錯誤: {e}")
    finally:
        db.close()


def fetch_subscription_sources():
    """抓取訂閱源"""
    from app.database import SyncSessionLocal
    from app.services.subscription_service import SubscriptionService
    
    logger.info("⏰ [排程] 抓取訂閱源...")
    db = SyncSessionLocal()
    try:
        service = SubscriptionService(db)
        result = service.fetch_all_sources()
        logger.info(f"✅ 訂閱源抓取完成: {result}")
    except Exception as e:
        logger.error(f"❌ 訂閱源抓取錯誤: {e}")
    finally:
        db.close()


# ============================================================
# 應用程式生命週期
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # 診斷資料庫連線
    from app.database import database_url, is_postgres
    db_type = "PostgreSQL" if is_postgres(database_url) else "SQLite"
    logger.info(f"★★★ Database Type: {db_type} ★★★")
    if is_postgres(database_url):
        safe_url = database_url.split("@")[-1] if "@" in database_url else database_url
        logger.info(f"★★★ Database Host: {safe_url} ★★★")
    else:
        logger.warning("⚠️ 使用 SQLite！資料會在重新部署後遺失！")

    await init_db()
    logger.info("Database initialized")

    # ============================================================
    # 🆕 V1.02 極簡排程（大幅減少）
    # ============================================================

    # 每日預載：美股開盤前（21:00 台北時間）
    scheduler.add_job(
        daily_preload,
        CronTrigger(hour=21, minute=0, timezone=TW_TZ),
        id='daily_preload',
        name='每日預載(21:00)',
    )

    # 情緒指數：早上補充一次（09:00）
    scheduler.add_job(
        update_market_sentiment,
        CronTrigger(hour=9, minute=0, timezone=TW_TZ),
        id='sentiment_morning',
        name='情緒更新(早)',
    )

    # 匯率：補充一次（09:30）
    scheduler.add_job(
        update_exchange_rate,
        CronTrigger(hour=9, minute=30, timezone=TW_TZ),
        id='exchange_rate_morning',
        name='匯率更新(早)',
    )

    # 訂閱源：每天 2 次（08:00、18:00）
    scheduler.add_job(
        fetch_subscription_sources,
        CronTrigger(hour=8, minute=0, timezone=TW_TZ),
        id='subscription_morning',
        name='訂閱源(早)',
    )
    scheduler.add_job(
        fetch_subscription_sources,
        CronTrigger(hour=18, minute=0, timezone=TW_TZ),
        id='subscription_evening',
        name='訂閱源(晚)',
    )

    # 🆕 V1.05 每日清除過期快取（凌晨 3:00）
    scheduler.add_job(
        clear_expired_caches,
        CronTrigger(hour=3, minute=0, timezone=TW_TZ),
        id='clear_caches',
        name='清除過期快取',
    )

    # 啟動排程器
    scheduler.start()
    logger.info("✅ 排程器已啟動（V1.05：每日預載 + 指標預計算 + 快取清除）")

    # 🆕 啟動時不做任何自動更新，完全依賴排程和用戶查詢
    logger.info("🆕 V1.02: 啟動時不自動更新，節省資源")

    yield

    # 關閉時
    scheduler.shutdown()
    logger.info("Shutting down...")


# 建立 FastAPI 應用程式
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 📈 AutoStock 自動選股系統 API

多用戶股票與加密貨幣技術分析平台

### 🆕 V1.02 優化
- 極簡排程：每日預載 21:00（美股開盤前）
- 即時查詢：用戶查才查，不預先更新
- 內存快取：60 秒過期，避免重複查詢
""",
    lifespan=lifespan,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 靜態檔案
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# 註冊路由
app.include_router(auth_router)
app.include_router(stock_router)
app.include_router(crypto_router)
app.include_router(watchlist_router)
app.include_router(settings_router)
app.include_router(admin_router)
app.include_router(compare_router)
app.include_router(portfolio_router)
app.include_router(market_router)
app.include_router(subscription_router)
app.include_router(tags_router)
app.include_router(stock_info_router)
app.include_router(broker_router)


# ==================== 基本路由 ====================

@app.get("/")
async def root():
    """首頁重導向"""
    return RedirectResponse(url="/static/index.html")


@app.get("/health", tags=["系統"])
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "app": settings.APP_NAME,
    }


@app.get("/api/version", tags=["系統"])
async def get_version():
    """取得版本資訊"""
    return {
        "version": settings.APP_VERSION,
        "app": settings.APP_NAME,
        "features": [
            "V1.02: 極簡排程",
            "V1.01: 內存快取",
            "V1.0.0: 完整功能",
        ]
    }
