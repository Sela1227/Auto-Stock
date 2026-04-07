"""
è‚¡ç¥¨è³‡è¨Š API è·¯ç”±
==================
stock_info ç¨®å­è¡¨æŸ¥è©¢èˆ‡ç®¡ç†

P1 åŠŸèƒ½
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

from app.database import get_db, get_async_session
from app.models.stock_info import StockInfo, DEFAULT_STOCK_INFO
from app.dependencies import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stock-info", tags=["è‚¡ç¥¨è³‡è¨Š"])


# ============================================================
# Schemas
# ============================================================

class StockInfoCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    name: Optional[str] = Field(None, max_length=100)
    name_zh: Optional[str] = Field(None, max_length=100)
    market: str = Field(default="us", pattern="^(us|tw|crypto)$")
    exchange: Optional[str] = Field(None, max_length=20)
    sector: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=50)
    is_popular: bool = False


class StockInfoUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    name_zh: Optional[str] = Field(None, max_length=100)
    market: Optional[str] = Field(None, pattern="^(us|tw|crypto)$")
    exchange: Optional[str] = Field(None, max_length=20)
    sector: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=50)
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None


# ============================================================
# å…¬é–‹ API
# ============================================================

@router.get("/search", summary="æœå°‹è‚¡ç¥¨")
async def search_stocks(
    q: str = Query(..., min_length=1, description="æœå°‹é—œéµå­—"),
    market: Optional[str] = Query(None, pattern="^(us|tw|crypto)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
):
    """
    æœå°‹è‚¡ç¥¨è³‡è¨Š
    - æ”¯æ´ä»£è™Ÿã€åç¨±ã€ä¸­æ–‡åç¨±æ¨¡ç³Šæœå°‹
    - å¯ç¯©é¸å¸‚å ´
    """
    q_upper = q.upper()
    q_like = f"%{q}%"
    
    stmt = select(StockInfo).where(
        StockInfo.is_active == True,
        or_(
            StockInfo.symbol.ilike(q_like),
            StockInfo.name.ilike(q_like),
            StockInfo.name_zh.ilike(q_like),
        )
    )
    
    if market:
        stmt = stmt.where(StockInfo.market == market)
    
    # å„ªå…ˆé¡¯ç¤ºå®Œå…¨åŒ¹é…
    stmt = stmt.order_by(
        (StockInfo.symbol == q_upper).desc(),
        StockInfo.is_popular.desc(),
        StockInfo.symbol
    ).limit(limit)
    
    result = await db.execute(stmt)
    stocks = result.scalars().all()
    
    return {
        "success": True,
        "query": q,
        "data": [s.to_dict() for s in stocks],
        "total": len(stocks),
    }


@router.get("/popular", summary="ç†±é–€è‚¡ç¥¨")
async def get_popular_stocks(
    market: Optional[str] = Query(None, pattern="^(us|tw|crypto)$"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_async_session),
):
    """å–å¾—ç†±é–€è‚¡ç¥¨åˆ—è¡¨"""
    stmt = select(StockInfo).where(
        StockInfo.is_active == True,
        StockInfo.is_popular == True
    )
    
    if market:
        stmt = stmt.where(StockInfo.market == market)
    
    stmt = stmt.order_by(StockInfo.symbol).limit(limit)
    
    result = await db.execute(stmt)
    stocks = result.scalars().all()
    
    return {
        "success": True,
        "data": [s.to_dict() for s in stocks],
        "total": len(stocks),
    }


@router.get("/by-market/{market}", summary="ä¾å¸‚å ´å–å¾—è‚¡ç¥¨")
async def get_stocks_by_market(
    market: str,
    sector: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
):
    """ä¾å¸‚å ´å–å¾—è‚¡ç¥¨åˆ—è¡¨"""
    if market not in ("us", "tw", "crypto"):
        raise HTTPException(status_code=400, detail="ç„¡æ•ˆçš„å¸‚å ´")
    
    stmt = select(StockInfo).where(
        StockInfo.is_active == True,
        StockInfo.market == market
    )
    
    if sector:
        stmt = stmt.where(StockInfo.sector == sector)
    
    stmt = stmt.order_by(StockInfo.is_popular.desc(), StockInfo.symbol)
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    stocks = result.scalars().all()
    
    return {
        "success": True,
        "market": market,
        "data": [s.to_dict() for s in stocks],
        "total": len(stocks),
    }


@router.get("/sectors", summary="å–å¾—ç”¢æ¥­åˆ†é¡ž")
async def get_sectors(
    market: Optional[str] = Query(None, pattern="^(us|tw|crypto)$"),
    db: AsyncSession = Depends(get_async_session),
):
    """å–å¾—æ‰€æœ‰ç”¢æ¥­åˆ†é¡ž"""
    from sqlalchemy import func, distinct
    
    stmt = select(distinct(StockInfo.sector)).where(
        StockInfo.is_active == True,
        StockInfo.sector.isnot(None)
    )
    
    if market:
        stmt = stmt.where(StockInfo.market == market)
    
    result = await db.execute(stmt)
    sectors = [row[0] for row in result.all() if row[0]]
    
    return {
        "success": True,
        "sectors": sorted(sectors),
    }


@router.get("/{symbol}", summary="å–å¾—è‚¡ç¥¨è³‡è¨Š")
async def get_stock_info(
    symbol: str,
    db: AsyncSession = Depends(get_async_session),
):
    """å–å¾—å–®ä¸€è‚¡ç¥¨çš„è©³ç´°è³‡è¨Š"""
    stmt = select(StockInfo).where(
        StockInfo.symbol == symbol.upper()
    )
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"æ‰¾ä¸åˆ°è‚¡ç¥¨: {symbol}")
    
    return {
        "success": True,
        "data": stock.to_dict(),
    }


# ============================================================
# ç®¡ç†å“¡ API
# ============================================================

@router.post("/admin/init", summary="åˆå§‹åŒ–ç¨®å­è³‡æ–™")
async def init_stock_info(
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """åˆå§‹åŒ–é è¨­è‚¡ç¥¨è³‡è¨Š"""
    added = 0
    skipped = 0
    
    for stock_data in DEFAULT_STOCK_INFO:
        # æª¢æŸ¥æ˜¯å¦å·²å­˜åœ¨
        stmt = select(StockInfo).where(StockInfo.symbol == stock_data["symbol"])
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            skipped += 1
            continue
        
        stock = StockInfo(**stock_data)
        db.add(stock)
        added += 1
    
    await db.commit()
    
    logger.info(f"ç®¡ç†å“¡ {admin.display_name} åˆå§‹åŒ–è‚¡ç¥¨è³‡è¨Š: æ–°å¢ž {added}, è·³éŽ {skipped}")
    
    return {
        "success": True,
        "message": f"åˆå§‹åŒ–å®Œæˆï¼šæ–°å¢ž {added} ç­†ï¼Œè·³éŽ {skipped} ç­†",
        "added": added,
        "skipped": skipped,
    }


@router.post("/admin/add", summary="æ–°å¢žè‚¡ç¥¨è³‡è¨Š")
async def add_stock_info(
    data: StockInfoCreate,
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """æ–°å¢žè‚¡ç¥¨è³‡è¨Š"""
    symbol = data.symbol.upper()
    
    # æª¢æŸ¥æ˜¯å¦å·²å­˜åœ¨
    stmt = select(StockInfo).where(StockInfo.symbol == symbol)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"è‚¡ç¥¨ {symbol} å·²å­˜åœ¨")
    
    stock = StockInfo(
        symbol=symbol,
        name=data.name,
        name_zh=data.name_zh,
        market=data.market,
        exchange=data.exchange,
        sector=data.sector,
        industry=data.industry,
        is_popular=data.is_popular,
    )
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    
    logger.info(f"ç®¡ç†å“¡ {admin.display_name} æ–°å¢žè‚¡ç¥¨: {symbol}")
    
    return {
        "success": True,
        "message": f"å·²æ–°å¢ž {symbol}",
        "data": stock.to_dict(),
    }


@router.put("/admin/{symbol}", summary="æ›´æ–°è‚¡ç¥¨è³‡è¨Š")
async def update_stock_info(
    symbol: str,
    data: StockInfoUpdate,
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """æ›´æ–°è‚¡ç¥¨è³‡è¨Š"""
    stmt = select(StockInfo).where(StockInfo.symbol == symbol.upper())
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"æ‰¾ä¸åˆ°è‚¡ç¥¨: {symbol}")
    
    # æ›´æ–°æ¬„ä½
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stock, key, value)
    
    await db.commit()
    await db.refresh(stock)
    
    logger.info(f"ç®¡ç†å“¡ {admin.display_name} æ›´æ–°è‚¡ç¥¨: {symbol}")
    
    return {
        "success": True,
        "message": f"å·²æ›´æ–° {symbol}",
        "data": stock.to_dict(),
    }


@router.delete("/admin/{symbol}", summary="åˆªé™¤è‚¡ç¥¨è³‡è¨Š")
async def delete_stock_info(
    symbol: str,
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """åˆªé™¤è‚¡ç¥¨è³‡è¨Š"""
    stmt = select(StockInfo).where(StockInfo.symbol == symbol.upper())
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"æ‰¾ä¸åˆ°è‚¡ç¥¨: {symbol}")
    
    await db.delete(stock)
    await db.commit()
    
    logger.info(f"ç®¡ç†å“¡ {admin.display_name} åˆªé™¤è‚¡ç¥¨: {symbol}")
    
    return {
        "success": True,
        "message": f"å·²åˆªé™¤ {symbol}",
    }


@router.post("/admin/batch-add", summary="æ‰¹æ¬¡æ–°å¢žè‚¡ç¥¨")
async def batch_add_stocks(
    stocks: List[StockInfoCreate],
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """æ‰¹æ¬¡æ–°å¢žè‚¡ç¥¨è³‡è¨Š"""
    added = []
    errors = []
    
    for stock_data in stocks:
        symbol = stock_data.symbol.upper()
        
        try:
            # æª¢æŸ¥æ˜¯å¦å·²å­˜åœ¨
            stmt = select(StockInfo).where(StockInfo.symbol == symbol)
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                errors.append({"symbol": symbol, "error": "å·²å­˜åœ¨"})
                continue
            
            stock = StockInfo(
                symbol=symbol,
                name=stock_data.name,
                name_zh=stock_data.name_zh,
                market=stock_data.market,
                exchange=stock_data.exchange,
                sector=stock_data.sector,
                industry=stock_data.industry,
                is_popular=stock_data.is_popular,
            )
            db.add(stock)
            added.append(symbol)
        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})
    
    await db.commit()
    
    logger.info(f"ç®¡ç†å“¡ {admin.display_name} æ‰¹æ¬¡æ–°å¢žè‚¡ç¥¨: æˆåŠŸ {len(added)}, å¤±æ•— {len(errors)}")
    
    return {
        "success": True,
        "message": f"æ‰¹æ¬¡æ–°å¢žå®Œæˆï¼šæˆåŠŸ {len(added)} ç­†ï¼Œå¤±æ•— {len(errors)} ç­†",
        "added": added,
        "errors": errors,
    }


@router.get("/admin/stats", summary="è‚¡ç¥¨è³‡è¨Šçµ±è¨ˆ")
async def get_stock_info_stats(
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """å–å¾—è‚¡ç¥¨è³‡è¨Šçµ±è¨ˆ"""
    from sqlalchemy import func
    
    # ç¸½æ•¸
    total_stmt = select(func.count(StockInfo.id))
    total = await db.scalar(total_stmt)
    
    # ä¾å¸‚å ´çµ±è¨ˆ
    market_stmt = (
        select(StockInfo.market, func.count(StockInfo.id))
        .group_by(StockInfo.market)
    )
    market_result = await db.execute(market_stmt)
    by_market = {row[0]: row[1] for row in market_result.all()}
    
    # ç†±é–€è‚¡æ•¸é‡
    popular_stmt = select(func.count(StockInfo.id)).where(StockInfo.is_popular == True)
    popular = await db.scalar(popular_stmt)
    
    return {
        "success": True,
        "stats": {
            "total": total or 0,
            "by_market": by_market,
            "popular": popular or 0,
        }
    }