"""
訂閱精選 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.database import get_db, get_async_session
from app.services.subscription_service import SubscriptionService
from app.models.subscription import SubscriptionSource, AutoPick
from app.models.price_cache import StockPriceCache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscription", tags=["訂閱精選"])


# ============================================================
# 認證（複用 watchlist 的認證邏輯）
# ============================================================

async def get_current_user(request: Request, db: AsyncSession = Depends(get_async_session)):
    """從 watchlist.py 複用的認證"""
    from app.services.auth_service import AuthService
    from app.models.user import User
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供認證 Token")
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="無效的 Token")
    
    return user


# ============================================================
# 訂閱源
# ============================================================

@router.get("/sources", summary="取得所有訂閱源")
def get_sources(db: Session = Depends(get_db)):
    """取得所有可訂閱的來源"""
    service = SubscriptionService(db)
    sources = service.get_all_sources(enabled_only=True)
    
    return {
        "success": True,
        "data": [s.to_dict() for s in sources],
    }


@router.get("/sources/{slug}", summary="取得單一訂閱源")
def get_source(slug: str, db: Session = Depends(get_db)):
    """取得單一訂閱源詳情"""
    service = SubscriptionService(db)
    source = service.get_source_by_slug(slug)
    
    if not source:
        raise HTTPException(status_code=404, detail="找不到訂閱源")
    
    return {
        "success": True,
        "data": source.to_dict(),
    }


# ============================================================
# 用戶訂閱
# ============================================================

@router.get("/my", summary="我的訂閱")
async def get_my_subscriptions(
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取得用戶訂閱的來源"""
    service = SubscriptionService(db)
    sources = service.get_user_subscriptions(user.id)
    
    return {
        "success": True,
        "data": [s.to_dict() for s in sources],
    }


@router.post("/subscribe/{source_id}", summary="訂閱來源")
async def subscribe_source(
    source_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """訂閱指定來源"""
    service = SubscriptionService(db)
    
    # 檢查來源是否存在
    source = db.query(SubscriptionSource).filter(
        SubscriptionSource.id == source_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="找不到訂閱源")
    
    result = service.subscribe(user.id, source_id)
    
    if not result:
        return {
            "success": True,
            "message": "已經訂閱過了",
        }
    
    return {
        "success": True,
        "message": f"成功訂閱 {source.name}",
    }


@router.delete("/unsubscribe/{source_id}", summary="取消訂閱")
async def unsubscribe_source(
    source_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取消訂閱指定來源"""
    service = SubscriptionService(db)
    result = service.unsubscribe(user.id, source_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="未訂閱此來源")
    
    return {
        "success": True,
        "message": "已取消訂閱",
    }


# ============================================================
# 精選列表
# ============================================================

@router.get("/picks", summary="我的訂閱精選")
async def get_my_picks(
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    取得用戶訂閱的所有精選
    包含價格資訊（從快取）
    """
    service = SubscriptionService(db)
    picks = service.get_user_picks(user.id)
    
    if not picks:
        return {
            "success": True,
            "data": [],
            "message": "尚未訂閱任何來源，或目前沒有精選",
        }
    
    # 取得價格快取
    symbols = [p["symbol"] for p in picks]
    cache_map = {}
    
    if symbols:
        caches = db.query(StockPriceCache).filter(
            StockPriceCache.symbol.in_(symbols)
        ).all()
        cache_map = {c.symbol: c for c in caches}
    
    # 組合價格
    for pick in picks:
        cache = cache_map.get(pick["symbol"])
        pick["price"] = float(cache.price) if cache and cache.price else None
        pick["change_pct"] = float(cache.change_pct) if cache and cache.change_pct else None
        pick["price_updated_at"] = cache.updated_at.isoformat() if cache and cache.updated_at else None
    
    return {
        "success": True,
        "data": picks,
        "total": len(picks),
    }


@router.get("/picks/{source_slug}", summary="特定來源的精選")
def get_source_picks(
    source_slug: str,
    db: Session = Depends(get_db),
):
    """取得特定來源的所有精選（公開）"""
    service = SubscriptionService(db)
    source = service.get_source_by_slug(source_slug)
    
    if not source:
        raise HTTPException(status_code=404, detail="找不到訂閱源")
    
    picks = service.get_active_picks(source_id=source.id)
    
    # 取得價格
    symbols = [p.symbol for p in picks]
    cache_map = {}
    if symbols:
        caches = db.query(StockPriceCache).filter(
            StockPriceCache.symbol.in_(symbols)
        ).all()
        cache_map = {c.symbol: c for c in caches}
    
    results = []
    for pick in picks:
        pick_dict = pick.to_dict()
        cache = cache_map.get(pick.symbol)
        pick_dict["price"] = float(cache.price) if cache and cache.price else None
        pick_dict["change_pct"] = float(cache.change_pct) if cache and cache.change_pct else None
        results.append(pick_dict)
    
    return {
        "success": True,
        "source": source.to_dict(),
        "data": results,
        "total": len(results),
    }


# ============================================================
# 管理 API（管理員用）
# ============================================================

@router.post("/admin/fetch", summary="手動抓取")
def admin_fetch(
    backfill: bool = False,
    db: Session = Depends(get_db),
):
    """
    手動觸發抓取
    - backfill=True: 回溯 30 天
    - backfill=False: 只抓新的
    """
    service = SubscriptionService(db)
    result = service.fetch_all_sources(backfill=backfill)
    
    return {
        "success": True,
        "message": "抓取完成",
        "data": result,
    }


@router.post("/admin/init", summary="初始化訂閱源")
def admin_init(db: Session = Depends(get_db)):
    """初始化預設訂閱源"""
    service = SubscriptionService(db)
    service.init_default_sources()
    
    return {
        "success": True,
        "message": "初始化完成",
    }
