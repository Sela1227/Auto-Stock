"""
追蹤清單 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.database import get_async_session
from app.services.auth_service import AuthService
from app.services.watchlist_service import WatchlistService
from app.schemas.schemas import (
    WatchlistAdd,
    WatchlistUpdate,
    WatchlistItem,
    WatchlistResponse,
    WatchlistListResponse,
    WatchlistOverviewResponse,
    ResponseBase,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watchlist", tags=["追蹤清單"])


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """依賴注入：取得當前用戶"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Watchlist API: 未提供認證 Token")
        raise HTTPException(
            status_code=401,
            detail="未提供認證 Token"
        )
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        logger.warning("Watchlist API: Token 驗證失敗")
        raise HTTPException(
            status_code=401,
            detail="無效的 Token"
        )
    
    logger.debug(f"Watchlist API: 驗證成功 user_id={user.id}, line_id={user.line_user_id}")
    return user


@router.get("", summary="取得追蹤清單", response_model=WatchlistListResponse)
async def get_watchlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶的追蹤清單
    """
    logger.info(f"API: 取得追蹤清單 - user_id={user.id}, line_id={user.line_user_id}")
    
    service = WatchlistService(db)
    items = await service.get_watchlist(user.id)
    
    return WatchlistListResponse(
        success=True,
        data=[WatchlistItem.model_validate(item) for item in items],
        total=len(items),
    )


@router.post("", summary="新增追蹤", response_model=WatchlistResponse)
async def add_to_watchlist(
    data: WatchlistAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    新增標的到追蹤清單
    
    - **symbol**: 股票代號 (如 AAPL) 或加密貨幣 (如 BTC)
    - **note**: 自訂備註（選填）
    """
    logger.info(f"API: 新增追蹤 - user_id={user.id}, line_id={user.line_user_id}, symbol={data.symbol}")
    
    service = WatchlistService(db)
    result = await service.add_to_watchlist(
        user_id=user.id,
        symbol=data.symbol,
        note=data.note,
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )
    
    return WatchlistResponse(
        success=True,
        message=result["message"],
        data=WatchlistItem.model_validate(result["watchlist"]),
    )


@router.delete("/{symbol}", summary="移除追蹤", response_model=ResponseBase)
async def remove_from_watchlist(
    symbol: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    從追蹤清單移除標的
    """
    logger.info(f"API: 移除追蹤 - user_id={user.id}, line_id={user.line_user_id}, symbol={symbol}")
    
    service = WatchlistService(db)
    result = await service.remove_from_watchlist(
        user_id=user.id,
        symbol=symbol,
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )
    
    return ResponseBase(
        success=True,
        message=result["message"],
    )


@router.put("/{symbol}", summary="更新備註", response_model=ResponseBase)
async def update_watchlist_note(
    symbol: str,
    data: WatchlistUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    更新追蹤標的的備註
    """
    logger.info(f"API: 更新備註 - user_id={user.id}, symbol={symbol}")
    
    service = WatchlistService(db)
    result = await service.update_note(
        user_id=user.id,
        symbol=symbol,
        note=data.note,
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )
    
    return ResponseBase(
        success=True,
        message=result["message"],
    )


@router.get("/overview", summary="追蹤清單總覽")
async def get_watchlist_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得追蹤清單總覽
    
    包含所有追蹤標的的基本資訊
    """
    logger.info(f"API: 追蹤清單總覽 - user_id={user.id}, line_id={user.line_user_id}")
    
    service = WatchlistService(db)
    items = await service.get_watchlist(user.id)
    
    return {
        "success": True,
        "data": [
            {
                "id": item.id,
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "note": item.note,
                "added_at": item.added_at.isoformat() if item.added_at else None,
            }
            for item in items
        ],
        "total": len(items),
    }
