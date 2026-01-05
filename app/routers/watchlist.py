"""
追蹤清單 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

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

router = APIRouter(prefix="/api/watchlist", tags=["追蹤清單"])


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """依賴注入：取得當前用戶"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="未提供認證 Token"
        )
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="無效的 Token"
        )
    
    return user


@router.get("", summary="取得追蹤清單", response_model=WatchlistListResponse)
async def get_watchlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶的追蹤清單
    """
    service = WatchlistService(db)
    items = service.get_watchlist(user.id)
    
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
    service = WatchlistService(db)
    result = service.add_to_watchlist(
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
    service = WatchlistService(db)
    result = service.remove_from_watchlist(
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
    service = WatchlistService(db)
    result = service.update_note(
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


@router.get("/overview", summary="追蹤清單總覽", response_model=WatchlistOverviewResponse)
async def get_watchlist_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得追蹤清單總覽
    
    包含所有追蹤標的的即時價格、技術指標和市場情緒
    """
    service = WatchlistService(db)
    overview = service.get_watchlist_overview(user.id)
    
    return WatchlistOverviewResponse(
        success=True,
        stocks=overview["stocks"],
        crypto=overview["crypto"],
        sentiment=overview.get("sentiment"),
        total_count=overview["total_count"],
    )
