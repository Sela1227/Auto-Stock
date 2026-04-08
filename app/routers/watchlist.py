"""
追蹤清單 API 路由

🚀 效能優化版 - 2026-01-17
- 非開盤時間直接使用快取（體感速度大幅提升）
- 回傳市場狀態，讓前端知道是否為開盤時間
- 批量載入標籤，消除 N+1 問題

🆕 目標價強化 - 2026-01-17
- 新增 target_direction 欄位（above/below）
- 支援「高於時提醒」和「低於時提醒」兩種模式
"""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
import logging
import json
import csv
import io
from datetime import datetime

from app.database import get_async_session
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
from app.models.watchlist import Watchlist
from app.models.price_cache import StockPriceCache
from app.models.watchlist_tag import UserTag, watchlist_tags  # ⭐ 新增

# 🔧 使用統一認證模組
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watchlist", tags=["追蹤清單"])


# Schemas
class TargetPriceUpdate(BaseModel):
    target_price: Optional[float] = None
    target_direction: Optional[str] = "above"  # 🆕 above=高於時提醒, below=低於時提醒


class WatchlistImportItem(BaseModel):
    symbol: str
    asset_type: Optional[str] = "stock"
    note: Optional[str] = None
    target_price: Optional[float] = None
    target_direction: Optional[str] = "above"  # 🆕


class WatchlistImportRequest(BaseModel):
    items: List[WatchlistImportItem]


# ============================================================
# 🆕 熱門追蹤統計 API
# ============================================================

@router.get("/popular", summary="熱門追蹤統計")
async def get_popular_watchlist(
    limit: int = 10,
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得最多人追蹤的股票排行
    
    - 不需要登入
    - 返回前 N 個最多人追蹤的標的
    - 包含追蹤人數統計
    """
    logger.info(f"API: 熱門追蹤統計 - limit={limit}")

    try:
        from sqlalchemy import func
        
        # 按 symbol 分組，計算追蹤人數
        stmt = (
            select(
                Watchlist.symbol,
                Watchlist.asset_type,
                func.count(Watchlist.user_id.distinct()).label('count')
            )
            .group_by(Watchlist.symbol, Watchlist.asset_type)
            .order_by(func.count(Watchlist.user_id.distinct()).desc())
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        popular = []
        for row in rows:
            popular.append({
                "symbol": row.symbol,
                "asset_type": row.asset_type or "stock",
                "count": row.count,
            })
        
        return {
            "success": True,
            "popular": popular,
            "total": len(popular),
        }

    except Exception as e:
        logger.error(f"取得熱門追蹤統計失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 匯出匯入 API
# ============================================================

@router.get("/export", summary="匯出追蹤清單")
async def export_watchlist(
    format: str = "json",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    匯出用戶的追蹤清單
    
    - format: json 或 csv
    - 包含 symbol, asset_type, note, target_price, target_direction
    """
    logger.info(f"API: 匯出追蹤清單 - user_id={user.id}, format={format}")

    try:
        # 取得用戶的追蹤清單
        stmt = (
            select(Watchlist)
            .where(Watchlist.user_id == user.id)
            .order_by(Watchlist.added_at.desc())
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        if not items:
            raise HTTPException(status_code=404, detail="追蹤清單為空")

        # 準備匯出資料
        export_data = []
        for item in items:
            export_data.append({
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "note": item.note or "",
                "target_price": float(item.target_price) if item.target_price else None,
                "target_direction": getattr(item, 'target_direction', 'above') or "above",  # 🆕
                "added_at": item.added_at.isoformat() if item.added_at else None,
            })

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format.lower() == "csv":
            # CSV 格式
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["symbol", "asset_type", "note", "target_price", "target_direction", "added_at"])  # 🆕
            writer.writeheader()
            writer.writerows(export_data)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=watchlist_{timestamp}.csv"
                }
            )
        else:
            # JSON 格式
            json_str = json.dumps({
                "export_time": datetime.now().isoformat(),
                "total": len(export_data),
                "items": export_data
            }, ensure_ascii=False, indent=2)
            
            return StreamingResponse(
                iter([json_str]),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=watchlist_{timestamp}.json"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"匯出追蹤清單失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", summary="匯入追蹤清單")
async def import_watchlist(
    data: WatchlistImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    匯入追蹤清單
    
    - 已存在的 symbol 會跳過
    - 返回成功/跳過/失敗的統計
    """
    logger.info(f"API: 匯入追蹤清單 - user_id={user.id}, items={len(data.items)}")

    try:
        # 取得現有追蹤清單
        stmt = select(Watchlist.symbol).where(Watchlist.user_id == user.id)
        result = await db.execute(stmt)
        existing_symbols = set(row[0] for row in result.all())

        added = []
        skipped = []
        errors = []

        for item in data.items:
            symbol = item.symbol.upper().strip()
            
            if not symbol:
                continue
                
            if symbol in existing_symbols:
                skipped.append(symbol)
                continue

            try:
                # 新增追蹤
                new_item = Watchlist(
                    user_id=user.id,
                    symbol=symbol,
                    asset_type=item.asset_type or "stock",
                    note=item.note,
                    target_price=item.target_price,
                )
                # 🆕 設定 target_direction（如果模型支援）
                if hasattr(new_item, 'target_direction'):
                    new_item.target_direction = item.target_direction or "above"
                db.add(new_item)
                added.append(symbol)
                existing_symbols.add(symbol)
            except Exception as e:
                errors.append({"symbol": symbol, "error": str(e)})

        await db.commit()

        return {
            "success": True,
            "message": f"匯入完成：新增 {len(added)} 筆，跳過 {len(skipped)} 筆",
            "data": {
                "added": added,
                "skipped": skipped,
                "errors": errors,
                "total_added": len(added),
                "total_skipped": len(skipped),
                "total_errors": len(errors),
            }
        }

    except Exception as e:
        logger.error(f"匯入追蹤清單失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================
# 🆕 基本資料 API（快速版，用於分階段載入）
# ============================================================

@router.get("/basic", summary="追蹤清單（基本資料，快速）")
async def get_watchlist_basic(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶追蹤清單基本資料（不含價格，毫秒級回應）
    
    🚀 效能優化：用於分階段載入的第一階段
    - 只查 watchlist 表和標籤
    - 不查 stock_price_cache
    - 價格欄位回傳 null，前端顯示「載入中」
    """
    logger.info(f"API: 追蹤清單(基本) - user_id={user.id}")

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
            }

        watchlist_ids = [item.id for item in watchlist_items]

        # 2. 批次取得所有標籤關聯
        tags_map = {}
        try:
            tags_stmt = (
                select(
                    watchlist_tags.c.watchlist_id,
                    UserTag
                )
                .join(UserTag, UserTag.id == watchlist_tags.c.tag_id)
                .where(watchlist_tags.c.watchlist_id.in_(watchlist_ids))
            )
            tags_result = await db.execute(tags_stmt)
            
            for row in tags_result:
                wl_id = row[0]
                tag = row[1]
                if wl_id not in tags_map:
                    tags_map[wl_id] = []
                tags_map[wl_id].append({
                    "id": tag.id,
                    "name": tag.name,
                    "color": tag.color,
                    "icon": tag.icon,
                })
        except Exception as e:
            logger.warning(f"載入標籤失敗: {e}")

        # 3. 組合資料（不含價格）
        data = []
        for item in watchlist_items:
            target_price = float(item.target_price) if item.target_price else None
            target_direction = getattr(item, 'target_direction', 'above') or 'above'

            data.append({
                "id": item.id,
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "note": item.note,
                "target_price": target_price,
                "target_direction": target_direction,
                "target_reached": False,  # 沒有價格無法判斷
                "added_at": item.added_at.isoformat() if item.added_at else None,
                # 價格欄位全部 null（前端會顯示「載入中」）
                "name": None,
                "price": None,
                "change": None,
                "change_pct": None,
                "ma20": None,
                "price_updated_at": None,
                # 標籤
                "tags": tags_map.get(item.id, []),
            })

        return {
            "success": True,
            "data": data,
            "total": len(data),
        }

    except Exception as e:
        logger.error(f"取得追蹤清單(基本)失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 價格快取 API（⭐ 優化版：包含標籤 + 市場狀態）
# ============================================================

@router.get("/with-prices", summary="追蹤清單（含即時價格）")
async def get_watchlist_with_prices(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶追蹤清單，包含即時價格（從快取讀取）
    
    🚀 效能優化版 2026-01-17：
    - 非開盤時間直接使用快取（毫秒級回應）
    - 回傳市場狀態，讓前端知道資料的時效性
    - 一次性載入所有標籤，消除 N+1 問題
    
    - 價格來自 stock_price_cache 表
    - 每 10 分鐘由排程更新
    - 回應時間：毫秒級
    - 包含目標價及是否達標
    - 包含該項目的所有標籤
    """
    logger.info(f"API: 追蹤清單(含價格) - user_id={user.id}")

    try:
        # 🆕 取得市場狀態
        from app.services.price_cache_service import get_market_status
        market_status = get_market_status()
        
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
                "market_status": market_status,  # 🆕
            }

        # 2. 取得所有 symbol 和 watchlist_id
        symbols = [item.symbol for item in watchlist_items]
        watchlist_ids = [item.id for item in watchlist_items]

        # 3. 從快取批次取得價格
        cache_stmt = select(StockPriceCache).where(
            StockPriceCache.symbol.in_(symbols)
        )
        cache_result = await db.execute(cache_stmt)
        cache_map = {c.symbol: c for c in cache_result.scalars().all()}

        # 4. ⭐ 批次取得所有標籤關聯（消除 N+1 問題）
        tags_map = {}
        try:
            tags_stmt = (
                select(
                    watchlist_tags.c.watchlist_id,
                    UserTag
                )
                .join(UserTag, UserTag.id == watchlist_tags.c.tag_id)
                .where(watchlist_tags.c.watchlist_id.in_(watchlist_ids))
            )
            tags_result = await db.execute(tags_stmt)
            
            # 建立 watchlist_id -> tags 的映射
            for row in tags_result:
                wl_id = row[0]
                tag = row[1]
                if wl_id not in tags_map:
                    tags_map[wl_id] = []
                tags_map[wl_id].append({
                    "id": tag.id,
                    "name": tag.name,
                    "color": tag.color,
                    "icon": tag.icon,
                })
        except Exception as e:
            logger.warning(f"載入標籤失敗（可能是新系統尚未建立標籤表）: {e}")
            # 標籤載入失敗不影響主要功能

        # 5. 組合資料
        data = []
        for item in watchlist_items:
            cache = cache_map.get(item.symbol)
            
            # MA20 值
            ma20_value = float(cache.ma20) if cache and cache.ma20 else None
            
            # 目標價判斷
            target_price = float(item.target_price) if item.target_price else None
            current_price = float(cache.price) if cache and cache.price else None
            target_reached = False
            
            # 🆕 取得 target_direction，預設為 above
            target_direction = getattr(item, 'target_direction', 'above') or 'above'
            
            if current_price and target_price:
                # 🆕 根據方向判斷是否達標
                if target_direction == 'below':
                    target_reached = current_price <= target_price
                else:
                    target_reached = current_price >= target_price

            data.append({
                "id": item.id,
                "symbol": item.symbol,
                "asset_type": item.asset_type,
                "note": item.note,
                "target_price": target_price,
                "target_direction": target_direction,  # 🆕
                "target_reached": target_reached,
                "added_at": item.added_at.isoformat() if item.added_at else None,
                # 價格資訊（從快取）
                "name": cache.name if cache else None,
                "price": current_price,
                "change": float(cache.change) if cache and cache.change else None,
                "change_pct": float(cache.change_pct) if cache and cache.change_pct else None,
                "ma20": ma20_value,
                "price_updated_at": cache.updated_at.isoformat() if cache and cache.updated_at else None,
                # ⭐ 標籤資訊（批量載入）
                "tags": tags_map.get(item.id, []),
            })

        return {
            "success": True,
            "data": data,
            "total": len(data),
            "market_status": market_status,  # 🆕 回傳市場狀態
        }

    except Exception as e:
        logger.error(f"取得追蹤清單(含價格)失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache-status", summary="快取狀態")
async def get_cache_status(
    db: AsyncSession = Depends(get_async_session),
):
    """查看價格快取狀態"""
    try:
        from app.services.price_cache_service import get_market_status

        stmt = select(StockPriceCache)
        result = await db.execute(stmt)
        all_cache = list(result.scalars().all())

        if not all_cache:
            return {
                "success": True,
                "total_cached": 0,
                "message": "快取為空，請等待排程更新",
                "market_status": get_market_status(),
            }

        updates = [c.updated_at for c in all_cache if c.updated_at]
        tw_stocks = [c for c in all_cache if c.symbol.endswith(('.TW', '.TWO'))]
        us_stocks = [c for c in all_cache if c.asset_type == 'stock' and not c.symbol.endswith(('.TW', '.TWO'))]
        crypto = [c for c in all_cache if c.asset_type == 'crypto']

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


# ============================================================
# 目標價 API
# ============================================================

@router.put("/{item_id}/target-price", summary="設定目標價")
async def set_target_price(
    item_id: int,
    data: TargetPriceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    設定追蹤標的的目標價格
    
    - 設定後，當現價達到目標價會變色提醒
    - target_direction: "above" (高於時提醒) 或 "below" (低於時提醒)
    - 傳入 null 可清除目標價
    """
    logger.info(f"API: 設定目標價 - user_id={user.id}, item_id={item_id}, target={data.target_price}, direction={data.target_direction}")

    try:
        # 查詢該追蹤項目
        stmt = select(Watchlist).where(
            Watchlist.id == item_id,
            Watchlist.user_id == user.id
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            raise HTTPException(status_code=404, detail="找不到該追蹤項目")

        # 更新目標價
        item.target_price = data.target_price
        # 🆕 更新方向（如果模型支援）
        if hasattr(item, 'target_direction'):
            item.target_direction = data.target_direction or "above"
        await db.commit()

        return {
            "success": True,
            "message": "目標價已更新" if data.target_price else "目標價已清除",
            "data": {
                "id": item.id,
                "symbol": item.symbol,
                "target_price": float(item.target_price) if item.target_price else None,
                "target_direction": getattr(item, 'target_direction', 'above') or "above",  # 🆕
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"設定目標價失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 原有的端點
# ============================================================

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
                "target_price": float(item.target_price) if item.target_price else None,
                "target_direction": getattr(item, 'target_direction', 'above') or "above",  # 🆕
                "added_at": item.added_at.isoformat() if item.added_at else None,
            }
            for item in items
        ],
        "total": len(items),
    }
