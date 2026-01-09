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
    Comparison,  # 🆕 新增：報酬率比較組合
)
from app.models.user import LoginLog, TokenBlacklist, SystemConfig

from app.routers import (
    auth_router,
    stock_router,
    crypto_router,
    watchlist_router,
    settings_router,
    admin_router,
    compare_router,  # 🆕 新增：報酬率比較
)
from app.routers.market import router as market_router

logger = logging.getLogger(__name__)


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
    
    yield
    
    # 關閉時
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
- **報酬率比較**: 多標的年化報酬率 (CAGR) 比較 🆕

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
app.include_router(compare_router)  # 🆕 新增：報酬率比較

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
