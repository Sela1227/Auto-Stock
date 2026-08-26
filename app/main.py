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

from contextlib import contextmanager

@contextmanager
def sync_db_session():
    """同步 DB session context manager，自動關閉，統一取代各函數內的重複樣板"""
    from app.database import SyncSessionLocal
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


def update_exchange_rate():
    """更新匯率"""
    from app.services.exchange_rate_service import ExchangeRateService
    logger.info("⏰ [排程] 更新匯率...")
    try:
        with sync_db_session() as db:
            rate = ExchangeRateService(db).update_usd_twd_rate()
            if rate:
                logger.info(f"✅ 匯率更新成功: USD/TWD = {rate}")
            else:
                logger.warning("⚠️ 匯率更新失敗")
    except Exception as e:
        logger.error(f"❌ 匯率更新錯誤: {e}")


def update_market_sentiment():
    """更新市場情緒（存入 DB）"""
    from app.services.market_service import MarketService
    logger.info("⏰ [排程] 更新市場情緒...")
    try:
        with sync_db_session() as db:
            result = MarketService(db).update_today_sentiment()
            logger.info(f"✅ 情緒更新: stock={result.get('stock')}, crypto={result.get('crypto')}")
    except Exception as e:
        logger.error(f"❌ 情緒更新錯誤: {e}")


def update_indices():
    """更新四大指數"""
    from app.services.market_service import MarketService
    logger.info("⏰ [排程] 更新四大指數...")
    try:
        with sync_db_session() as db:
            result = MarketService(db).fetch_and_save_all_indices(period="5d")
            logger.info(f"✅ 指數更新完成: {result}")
    except Exception as e:
        logger.error(f"❌ 指數更新錯誤: {e}")


def update_all_stock_prices():
    """
    股價全量更新（追蹤清單所有標的）
    V1.14.0 起改為每日批次，不再依賴管理員登入觸發
    """
    from app.services.price_cache_service import PriceCacheService
    logger.info("⏰ [排程] 股價全量更新...")
    try:
        with sync_db_session() as db:
            result = PriceCacheService(db).update_all_prices(force=True)
            logger.info(f"✅ 股價更新完成: {result}")
    except Exception as e:
        logger.error(f"❌ 股價更新錯誤: {e}")


def daily_preload():
    """
    每日批次更新（週一~週六 06:00 台北時間）

    時間點選擇理由：
    - 美股 05:00（台北）收盤，06:00 抓到的是最新收盤價
    - 台股抓到的是前一交易日收盤價
    - 週六跑是為了補抓週五的美股收盤（週五 21:30 開盤，週六 05:00 收盤）

    更新項目：
    - 股價全量（追蹤清單所有標的）
    - 情緒指數
    - 四大指數
    - 匯率
    - 技術指標預計算
    """
    logger.info("⏰ [排程] === 每日批次更新開始（06:00）===")
    try:
        update_all_stock_prices()
        update_market_sentiment()
        update_indices()
        update_exchange_rate()
        precompute_indicators()
        logger.info("✅ [排程] === 每日批次更新完成 ===")
    except Exception as e:
        logger.error(f"❌ 每日批次更新錯誤: {e}")


def precompute_indicators():
    """V1.05 預計算追蹤清單股票的技術指標"""
    from app.services.analysis_cache_service import AnalysisCacheService
    logger.info("⏰ [排程] 預計算技術指標...")
    try:
        with sync_db_session() as db:
            result = AnalysisCacheService(db).precompute_indicators_for_watchlist()
            logger.info(f"✅ 指標預計算: 成功 {result['success']}, 失敗 {result['failed']}")
    except Exception as e:
        logger.error(f"❌ 指標預計算錯誤: {e}")


def clear_expired_caches():
    """V1.05 清除過期快取"""
    from app.services.analysis_cache_service import AnalysisCacheService
    logger.info("⏰ [排程] 清除過期快取...")
    try:
        with sync_db_session() as db:
            result = AnalysisCacheService(db).clear_expired_caches()
            logger.info(f"✅ 快取清除: {result}")
    except Exception as e:
        logger.error(f"❌ 快取清除錯誤: {e}")


def fetch_subscription_sources():
    """抓取訂閱源"""
    from app.services.subscription_service import SubscriptionService
    logger.info("⏰ [排程] 抓取訂閱源...")
    try:
        with sync_db_session() as db:
            result = SubscriptionService(db).fetch_all_sources()
            logger.info(f"✅ 訂閱源抓取完成: {result}")
    except Exception as e:
        logger.error(f"❌ 訂閱源抓取錯誤: {e}")


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
    # V1.14.0 極簡排程：每日單一批次
    # ============================================================
    # 設計理由：
    # - 本系統定位為「追蹤」而非「即時分析」，不需要盤中更新
    # - 06:00 台北時間 = 美股 05:00 收盤後，抓到的是最新收盤價
    # - mon-sat：週六補抓週五美股收盤（週五 21:30 開盤，週六 05:00 收盤）
    # - 需要即時資料時，管理後台有手動更新按鈕
    # ============================================================

    # 每日批次：美股收盤後（06:00 台北時間，週一~週六）
    scheduler.add_job(
        daily_preload,
        CronTrigger(day_of_week='mon-sat', hour=6, minute=0, timezone=TW_TZ),
        id='daily_preload',
        name='每日批次更新(06:00)',
    )

    # 每日清除過期快取（凌晨 3:00）
    scheduler.add_job(
        clear_expired_caches,
        CronTrigger(hour=3, minute=0, timezone=TW_TZ),
        id='clear_caches',
        name='清除過期快取',
    )

    # 註：以下排程於 V1.14.0 移除（改為手動觸發，降低 Railway 資源消耗）
    # - 訂閱源抓取（原 08:00 / 18:00）→ 管理後台手動按
    # - 情緒指數補充（原 09:00）→ 併入 06:00 批次
    # - 匯率補充（原 09:30）→ 併入 06:00 批次
    # - 每日預載（原 21:00）→ 移至 06:00

    # 啟動排程器
    scheduler.start()
    logger.info("✅ 排程器已啟動（V1.14.0：每日 06:00 單一批次 + 03:00 快取清除）")

    logger.info("🆕 啟動時不自動更新，完全依賴排程和用戶查詢")

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

# CORS 設定（production 限縮，development 全開）
_cors_origins = (
    [settings.LINE_LOGIN_CALLBACK_URL.rsplit("/", 2)[0]]  # 取 scheme+host
    if settings.APP_ENV == "production" and settings.LINE_LOGIN_CALLBACK_URL
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
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
            "V1.14.0: 排程簡化為每日 06:00 單一批次",
            "V1.12.3: 修復情緒指數顯示",
            "V1.12.2: JS 語法修復、資安強化",
            "V1.12.1: 修復啟動 crash",
        ]
    }
