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
    PortfolioTransaction, PortfolioHolding, ExchangeRate,  # 🆕 個人投資記錄
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
    portfolio_router,  # 🆕 個人投資記錄
)
from app.routers.market import router as market_router

# 排程器
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# 建立排程器
scheduler = AsyncIOScheduler()


# ============================================================
# 價格快取更新函數
# ============================================================

def update_price_cache():
    """排程任務：更新價格快取（每 10 分鐘）"""
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
    """強制更新所有價格（啟動時 / 收盤後）"""
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
# 🆕 匯率更新函數
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
    # 價格快取排程
    # ============================================================
    
    # 每 10 分鐘執行（自動判斷開盤時間）
    scheduler.add_job(
        update_price_cache,
        'interval',
        minutes=10,
        id='price_cache_update',
        name='價格快取更新(每10分鐘)',
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
    # 🆕 匯率排程（每天 3 次：09:00、12:00、17:00）
    # ============================================================
    
    scheduler.add_job(
        update_exchange_rate,
        CronTrigger(hour=9, minute=0),
        id='exchange_rate_morning',
        name='匯率更新(早)',
    )
    
    scheduler.add_job(
        update_exchange_rate,
        CronTrigger(hour=12, minute=0),
        id='exchange_rate_noon',
        name='匯率更新(中)',
    )
    
    scheduler.add_job(
        update_exchange_rate,
        CronTrigger(hour=17, minute=0),
        id='exchange_rate_evening',
        name='匯率更新(晚)',
    )
    
    # 啟動排程器
    scheduler.start()
    logger.info("排程器已啟動（價格快取 + 匯率）")
    
    # 啟動時執行一次
    try:
        update_price_cache_force()
        update_exchange_rate()
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
- **個人投資記錄**: 交易紀錄、持股管理、損益追蹤 🆕

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
app.include_router(portfolio_router)  # 🆕 個人投資記錄

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
