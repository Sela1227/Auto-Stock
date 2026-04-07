"""
股票資訊 API 路由
==================
stock_info 種子表查詢與管理

P1 功能
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

router = APIRouter(prefix="/api/stock-info", tags=["股票資訊"])


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
# 公開 API
# ============================================================

@router.get("/search", summary="搜尋股票")
async def search_stocks(
    q: str = Query(..., min_length=1, description="搜尋關鍵字"),
    market: Optional[str] = Query(None, pattern="^(us|tw|crypto)$"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
):
    """
    搜尋股票資訊
    - 支援代號、名稱、中文名稱模糊搜尋
    - 可篩選市場
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
    
    # 優先顯示完全匹配
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


@router.get("/popular", summary="熱門股票")
async def get_popular_stocks(
    market: Optional[str] = Query(None, pattern="^(us|tw|crypto)$"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_async_session),
):
    """取得熱門股票列表"""
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


@router.get("/by-market/{market}", summary="依市場取得股票")
async def get_stocks_by_market(
    market: str,
    sector: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
):
    """依市場取得股票列表"""
    if market not in ("us", "tw", "crypto"):
        raise HTTPException(status_code=400, detail="無效的市場")
    
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


@router.get("/sectors", summary="取得產業分類")
async def get_sectors(
    market: Optional[str] = Query(None, pattern="^(us|tw|crypto)$"),
    db: AsyncSession = Depends(get_async_session),
):
    """取得所有產業分類"""
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


@router.get("/{symbol}", summary="取得股票資訊")
async def get_stock_info(
    symbol: str,
    db: AsyncSession = Depends(get_async_session),
):
    """取得單一股票的詳細資訊"""
    stmt = select(StockInfo).where(
        StockInfo.symbol == symbol.upper()
    )
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"找不到股票: {symbol}")
    
    return {
        "success": True,
        "data": stock.to_dict(),
    }


# ============================================================
# 管理員 API
# ============================================================

@router.post("/admin/init", summary="初始化種子資料")
async def init_stock_info(
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """初始化預設股票資訊"""
    added = 0
    skipped = 0
    
    for stock_data in DEFAULT_STOCK_INFO:
        # 檢查是否已存在
        stmt = select(StockInfo).where(StockInfo.symbol == stock_data["symbol"])
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            skipped += 1
            continue
        
        stock = StockInfo(**stock_data)
        db.add(stock)
        added += 1
    
    await db.commit()
    
    logger.info(f"管理員 {admin.display_name} 初始化股票資訊: 新增 {added}, 跳過 {skipped}")
    
    return {
        "success": True,
        "message": f"初始化完成：新增 {added} 筆，跳過 {skipped} 筆",
        "added": added,
        "skipped": skipped,
    }


@router.post("/admin/add", summary="新增股票資訊")
async def add_stock_info(
    data: StockInfoCreate,
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """新增股票資訊"""
    symbol = data.symbol.upper()
    
    # 檢查是否已存在
    stmt = select(StockInfo).where(StockInfo.symbol == symbol)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"股票 {symbol} 已存在")
    
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
    
    logger.info(f"管理員 {admin.display_name} 新增股票: {symbol}")
    
    return {
        "success": True,
        "message": f"已新增 {symbol}",
        "data": stock.to_dict(),
    }


@router.put("/admin/{symbol}", summary="更新股票資訊")
async def update_stock_info(
    symbol: str,
    data: StockInfoUpdate,
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """更新股票資訊"""
    stmt = select(StockInfo).where(StockInfo.symbol == symbol.upper())
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"找不到股票: {symbol}")
    
    # 更新欄位
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(stock, key, value)
    
    await db.commit()
    await db.refresh(stock)
    
    logger.info(f"管理員 {admin.display_name} 更新股票: {symbol}")
    
    return {
        "success": True,
        "message": f"已更新 {symbol}",
        "data": stock.to_dict(),
    }


@router.delete("/admin/{symbol}", summary="刪除股票資訊")
async def delete_stock_info(
    symbol: str,
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """刪除股票資訊"""
    stmt = select(StockInfo).where(StockInfo.symbol == symbol.upper())
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"找不到股票: {symbol}")
    
    await db.delete(stock)
    await db.commit()
    
    logger.info(f"管理員 {admin.display_name} 刪除股票: {symbol}")
    
    return {
        "success": True,
        "message": f"已刪除 {symbol}",
    }


@router.post("/admin/batch-add", summary="批次新增股票")
async def batch_add_stocks(
    stocks: List[StockInfoCreate],
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """批次新增股票資訊"""
    added = []
    errors = []
    
    for stock_data in stocks:
        symbol = stock_data.symbol.upper()
        
        try:
            # 檢查是否已存在
            stmt = select(StockInfo).where(StockInfo.symbol == symbol)
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                errors.append({"symbol": symbol, "error": "已存在"})
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
    
    logger.info(f"管理員 {admin.display_name} 批次新增股票: 成功 {len(added)}, 失敗 {len(errors)}")
    
    return {
        "success": True,
        "message": f"批次新增完成：成功 {len(added)} 筆，失敗 {len(errors)} 筆",
        "added": added,
        "errors": errors,
    }


@router.get("/admin/stats", summary="股票資訊統計")
async def get_stock_info_stats(
    admin = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得股票資訊統計"""
    from sqlalchemy import func
    
    # 總數
    total_stmt = select(func.count(StockInfo.id))
    total = await db.scalar(total_stmt)
    
    # 依市場統計
    market_stmt = (
        select(StockInfo.market, func.count(StockInfo.id))
        .group_by(StockInfo.market)
    )
    market_result = await db.execute(market_stmt)
    by_market = {row[0]: row[1] for row in market_result.all()}
    
    # 熱門股數量
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
