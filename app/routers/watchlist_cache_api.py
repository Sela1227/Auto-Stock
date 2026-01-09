"""
追蹤清單 API - 含價格快取版本

============================================================
注意：這個檔案是範例程式碼
請將下方的端點整合到你現有的 app/routers/watchlist.py
============================================================

新增端點：
- GET /api/watchlist/with-prices  從快取取得追蹤清單（含即時價格）
- POST /api/watchlist/refresh-cache  手動觸發快取更新
- GET /api/watchlist/cache-status  查看快取狀態
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Dict, Any
import logging

# ============================================================
# 以下 import 需要根據你的專案結構調整
# ============================================================
from app.database import get_async_session, get_db
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.price_cache import StockPriceCache  # 新增的 model
from app.services.price_cache_service import PriceCacheService  # 新增的 service

logger = logging.getLogger(__name__)


# ============================================================
# 整合到現有的 watchlist.py
# 
# 1. 加入上方的 import
# 2. 複製下方三個端點到 watchlist.py
# 3. 將 get_current_user 替換成你現有的驗證函數
# ============================================================


# ---------- 端點 1: 追蹤清單（含價格） ----------

"""
@router.get("/with-prices", summary="追蹤清單（含即時價格）")
async def get_watchlist_with_prices(
    user: User = Depends(get_current_user),  # 用你現有的驗證函數
    db: AsyncSession = Depends(get_async_session),
):
    '''
    取得用戶追蹤清單，包含即時價格（從快取讀取）
    
    - 價格來自 stock_price_cache 表
    - 每 10 分鐘由排程更新
    - 回應時間：毫秒級
    '''
    logger.info(f"API: 追蹤清單(含價格) - user_id={user.id}")
    
    try:
        # 1. 取得用戶的追蹤清單
        stmt = (
            select(Watchlist)
            .where(Watchlist.user_id == user.id)
            .order_by(Watchlist.added_at.desc())
        )
        result = await db.execute(stmt)
        watchlist_items = list(result.scalars().all())
        
        if not watchlist_items:
            return {
                "success": True,
                "data": [],
                "total": 0,
                "cache_info": None,
            }
        
        # 2. 取得所有 symbol
        symbols = [item.symbol for item in watchlist_items]
        
        # 3. 從快取批次取得價格
        cache_stmt = select(StockPriceCache).where(
            StockPriceCache.symbol.in_(symbols)
        )
        cache_result = await db.execute(cache_stmt)
        cached_prices = {r.symbol: r for r in cache_result.scalars().all()}
        
        # 4. 組合資料
        data = []
        oldest_update = None
        
        for item in watchlist_items:
            cache = cached_prices.get(item.symbol)
            
            item_data = {
                "id": item.id,
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "note": item.note,
                "added_at": item.added_at.isoformat() if item.added_at else None,
                # 價格資訊（從快取）
                "name": cache.name if cache else None,
                "price": float(cache.price) if cache and cache.price else None,
                "change": float(cache.change) if cache and cache.change else None,
                "change_pct": float(cache.change_pct) if cache and cache.change_pct else None,
                "volume": cache.volume if cache else None,
                "price_updated_at": cache.updated_at.isoformat() if cache and cache.updated_at else None,
            }
            data.append(item_data)
            
            # 記錄最舊的更新時間
            if cache and cache.updated_at:
                if oldest_update is None or cache.updated_at < oldest_update:
                    oldest_update = cache.updated_at
        
        return {
            "success": True,
            "data": data,
            "total": len(data),
            "cache_info": {
                "oldest_update": oldest_update.isoformat() if oldest_update else None,
                "symbols_with_price": len(cached_prices),
                "symbols_without_price": len(symbols) - len(cached_prices),
            },
        }
        
    except Exception as e:
        logger.error(f"取得追蹤清單(含價格)失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
"""


# ---------- 端點 2: 手動更新快取 ----------

"""
@router.post("/refresh-cache", summary="手動更新價格快取")
async def refresh_price_cache(
    user: User = Depends(get_current_user),  # 用你現有的驗證函數
    db: Session = Depends(get_db),  # 使用同步 session
):
    '''
    手動觸發價格快取更新
    
    注意：這會對 Yahoo Finance 發送請求，請勿頻繁呼叫
    '''
    # 可選：加上管理員權限檢查
    # if not user.is_admin:
    #     raise HTTPException(status_code=403, detail="需要管理員權限")
    
    logger.info(f"手動更新價格快取 - by user_id={user.id}")
    
    try:
        service = PriceCacheService(db)
        result = service.update_all_tracked_prices(force=True)
        
        return {
            "success": True,
            "message": f"已更新 {result['total_updated']} 筆價格",
            "detail": result,
        }
        
    except Exception as e:
        logger.error(f"手動更新價格快取失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
"""


# ---------- 端點 3: 快取狀態（公開） ----------

"""
@router.get("/cache-status", summary="快取狀態")
async def get_cache_status(
    db: AsyncSession = Depends(get_async_session),
):
    '''
    查看價格快取狀態（公開 API，用於監控）
    '''
    from app.services.price_cache_service import get_market_status
    
    try:
        stmt = select(StockPriceCache)
        result = await db.execute(stmt)
        all_cache = list(result.scalars().all())
        
        if not all_cache:
            return {
                "success": True,
                "total_cached": 0,
                "market_status": get_market_status(),
            }
        
        tw_stocks = [c for c in all_cache if c.symbol.endswith(('.TW', '.TWO'))]
        us_stocks = [c for c in all_cache if c.asset_type == 'stock' and not c.symbol.endswith(('.TW', '.TWO'))]
        crypto = [c for c in all_cache if c.asset_type == "crypto"]
        
        updates = [c.updated_at for c in all_cache if c.updated_at]
        
        return {
            "success": True,
            "total_cached": len(all_cache),
            "tw_stocks": len(tw_stocks),
            "us_stocks": len(us_stocks),
            "crypto": len(crypto),
            "oldest_update": min(updates).isoformat() if updates else None,
            "newest_update": max(updates).isoformat() if updates else None,
            "market_status": get_market_status(),
        }
        
    except Exception as e:
        logger.error(f"查詢快取狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
"""

