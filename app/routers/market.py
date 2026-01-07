"""
市場資料 API 路由
三大指數、市場情緒、排程任務
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.database import get_db, get_async_session
from app.services.market_service import MarketService
from app.services.auth_service import AuthService
from app.tasks.scheduler import scheduler_service
from app.models.index_price import INDEX_SYMBOLS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["market"])


# ==================== 認證依賴 ====================

async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """取得當前用戶（選擇性，未登入返回 None）"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    return user


async def get_current_admin(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """取得當前管理員（必須是管理員）"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供認證 Token")
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="無效的 Token")
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理員權限")
    
    return user


# ==================== 三大指數 ====================

@router.get("/indices")
async def get_indices(
    db: Session = Depends(get_db),
):
    """
    取得三大指數最新資料
    
    Returns:
        - S&P 500 (^GSPC)
        - 道瓊工業 (^DJI)
        - 納斯達克 (^IXIC)
    """
    try:
        market_service = MarketService(db)
        indices = market_service.get_latest_indices()
        
        return {
            "success": True,
            "data": {
                "indices": indices,
                "symbols": INDEX_SYMBOLS,
            }
        }
    except Exception as e:
        logger.error(f"取得指數失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices/{symbol}/history")
async def get_index_history(
    symbol: str,
    days: int = Query(default=365, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    """
    取得指數歷史資料
    
    Args:
        symbol: 指數代號 (^GSPC, ^DJI, ^IXIC)
        days: 天數 (預設 365，最多 3650)
    """
    # 驗證 symbol
    if symbol not in INDEX_SYMBOLS:
        raise HTTPException(
            status_code=400,
            detail=f"無效的指數代號，可用: {list(INDEX_SYMBOLS.keys())}"
        )
    
    try:
        market_service = MarketService(db)
        history = market_service.get_index_history(symbol, days)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "name": INDEX_SYMBOLS[symbol]["name"],
                "name_zh": INDEX_SYMBOLS[symbol]["name_zh"],
                "days": days,
                "count": len(history),
                "history": history,
            }
        }
    except Exception as e:
        logger.error(f"取得指數歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 市場情緒 ====================

@router.get("/sentiment")
async def get_sentiment(
    db: Session = Depends(get_db),
):
    """
    取得市場情緒（美股 + 幣圈）
    """
    try:
        market_service = MarketService(db)
        sentiment = market_service.get_latest_sentiment()
        
        return {
            "success": True,
            "data": sentiment,
        }
    except Exception as e:
        logger.error(f"取得情緒失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/{market}/history")
async def get_sentiment_history(
    market: str,
    days: int = Query(default=365, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    取得情緒歷史資料
    
    Args:
        market: 市場類型 (stock, crypto)
        days: 天數 (預設 365，最多 365)
    """
    if market not in ["stock", "crypto"]:
        raise HTTPException(
            status_code=400,
            detail="無效的市場類型，可用: stock, crypto"
        )
    
    try:
        market_service = MarketService(db)
        history = market_service.get_sentiment_history(market, days)
        
        return {
            "success": True,
            "data": {
                "market": market,
                "days": days,
                "count": len(history),
                "history": history,
            }
        }
    except Exception as e:
        logger.error(f"取得情緒歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 管理員功能：排程任務 ====================

@router.post("/admin/update")
async def trigger_daily_update(
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    [管理員] 手動觸發每日更新
    """
    try:
        result = scheduler_service.run_daily_update()
        
        return {
            "success": result.get("success", False),
            "data": result,
        }
    except Exception as e:
        logger.error(f"執行更新失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/initialize")
async def initialize_historical_data(
    years: int = Query(default=10, ge=1, le=10),
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    [管理員] 初始化歷史資料
    
    首次部署時執行，抓取：
    - 三大指數 N 年歷史
    - 幣圈情緒 365 天歷史
    """
    try:
        result = scheduler_service.initialize_historical_data(years=years)
        
        return {
            "success": result.get("success", False),
            "data": result,
        }
    except Exception as e:
        logger.error(f"初始化失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/update-indices")
async def update_indices(
    period: str = Query(default="5d", pattern="^(5d|1mo|3mo|1y|5y|10y)$"),
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    [管理員] 更新三大指數資料
    """
    try:
        market_service = MarketService(db)
        result = market_service.fetch_and_save_all_indices(period=period)
        
        return {
            "success": True,
            "data": {
                "period": period,
                "indices": result,
            }
        }
    except Exception as e:
        logger.error(f"更新指數失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/update-sentiment")
async def update_sentiment(
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    [管理員] 更新今日市場情緒
    """
    try:
        market_service = MarketService(db)
        result = market_service.update_today_sentiment()
        
        return {
            "success": True,
            "data": result,
        }
    except Exception as e:
        logger.error(f"更新情緒失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/init-crypto-sentiment")
async def init_crypto_sentiment(
    days: int = Query(default=365, ge=1, le=365),
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    [管理員] 初始化幣圈情緒歷史
    """
    try:
        market_service = MarketService(db)
        count = market_service.fetch_and_save_crypto_history(days=days)
        
        return {
            "success": True,
            "data": {
                "days_requested": days,
                "records_added": count,
            }
        }
    except Exception as e:
        logger.error(f"初始化幣圈情緒失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/scheduler-status")
async def get_scheduler_status(
    current_user = Depends(get_current_admin),
):
    """
    [管理員] 取得排程狀態
    """
    return {
        "success": True,
        "data": scheduler_service.get_status(),
    }
