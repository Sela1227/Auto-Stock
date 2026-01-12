"""
個人投資記錄 API 路由
"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.services.auth_service import AuthService
from app.services.portfolio_service import PortfolioService
from app.services.exchange_rate_service import get_exchange_rate, set_exchange_rate
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["個人投資記錄"])


# ============================================================
# Pydantic Schemas
# ============================================================

class TransactionCreate(BaseModel):
    """新增交易請求"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代碼")
    name: Optional[str] = Field(None, max_length=100, description="股票名稱")
    market: str = Field(..., pattern="^(tw|us)$", description="市場 (tw/us)")
    transaction_type: str = Field(..., pattern="^(buy|sell)$", description="交易類型 (buy/sell)")
    quantity: int = Field(..., gt=0, description="股數（台股：張×1000 + 零股）")
    price: float = Field(..., gt=0, description="成交價")
    fee: Optional[float] = Field(0, ge=0, description="手續費")
    tax: Optional[float] = Field(0, ge=0, description="交易稅")
    transaction_date: date = Field(..., description="交易日期")
    note: Optional[str] = Field(None, max_length=500, description="備註")


class TransactionUpdate(BaseModel):
    """更新交易請求"""
    symbol: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, max_length=100)
    market: Optional[str] = Field(None, pattern="^(tw|us)$")
    transaction_type: Optional[str] = Field(None, pattern="^(buy|sell)$")
    quantity: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, gt=0)
    fee: Optional[float] = Field(None, ge=0)
    tax: Optional[float] = Field(None, ge=0)
    transaction_date: Optional[date] = None
    note: Optional[str] = Field(None, max_length=500)


class ExchangeRateUpdate(BaseModel):
    """更新匯率請求"""
    rate: float = Field(..., gt=0, description="USD/TWD 匯率")


# ============================================================
# 依賴注入
# ============================================================

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """驗證用戶身份"""
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
# 匯率 API
# ============================================================

@router.get("/exchange-rate", summary="取得匯率")
async def get_rate(
    db: AsyncSession = Depends(get_async_session),
):
    """取得目前的 USD/TWD 匯率"""
    rate_info = await get_exchange_rate(db)
    return {
        "success": True,
        "data": rate_info,
    }


@router.put("/exchange-rate", summary="設定匯率")
async def update_rate(
    data: ExchangeRateUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """手動設定 USD/TWD 匯率"""
    rate_info = await set_exchange_rate(db, data.rate)
    return {
        "success": True,
        "message": "匯率已更新",
        "data": rate_info,
    }


# ============================================================
# 交易紀錄 API
# ============================================================

@router.post("/transactions", summary="新增交易紀錄")
async def create_transaction(
    data: TransactionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    新增一筆股票交易紀錄
    
    - **symbol**: 股票代碼（如 AAPL、2330）
    - **market**: 市場類型（tw=台股, us=美股）
    - **transaction_type**: buy=買入, sell=賣出
    - **quantity**: 總股數（台股：張×1000 + 零股）
    - **price**: 成交價
    - **fee**: 手續費（可選）
    - **tax**: 交易稅（可選，賣出時）
    """
    logger.info(f"新增交易: user={user.id}, {data.transaction_type} {data.quantity} {data.symbol}")
    
    try:
        service = PortfolioService(db)
        transaction = await service.create_transaction(
            user_id=user.id,
            symbol=data.symbol,
            name=data.name,
            market=data.market,
            transaction_type=data.transaction_type,
            quantity=data.quantity,
            price=data.price,
            fee=data.fee or 0,
            tax=data.tax or 0,
            transaction_date=data.transaction_date,
            note=data.note,
        )
        
        return {
            "success": True,
            "message": "交易紀錄已新增",
            "data": transaction.to_dict(),
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"新增交易失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="新增交易失敗")


@router.get("/transactions", summary="取得交易紀錄")
async def get_transactions(
    market: Optional[str] = Query(None, pattern="^(tw|us)$", description="篩選市場"),
    symbol: Optional[str] = Query(None, description="篩選股票"),
    limit: int = Query(100, ge=1, le=500, description="筆數上限"),
    offset: int = Query(0, ge=0, description="偏移量"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得用戶的交易紀錄列表"""
    try:
        service = PortfolioService(db)
        transactions = await service.get_transactions(
            user_id=user.id,
            market=market,
            symbol=symbol,
            limit=limit,
            offset=offset,
        )
        
        return {
            "success": True,
            "data": [t.to_dict() for t in transactions],
            "total": len(transactions),
        }
        
    except Exception as e:
        logger.error(f"取得交易紀錄失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="取得交易紀錄失敗")


@router.get("/transactions/{transaction_id}", summary="取得單筆交易")
async def get_transaction(
    transaction_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得單筆交易紀錄詳情"""
    service = PortfolioService(db)
    transaction = await service.get_transaction(transaction_id, user.id)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="找不到交易紀錄")
    
    return {
        "success": True,
        "data": transaction.to_dict(),
    }


@router.put("/transactions/{transaction_id}", summary="更新交易紀錄")
async def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """更新交易紀錄"""
    logger.info(f"更新交易: user={user.id}, id={transaction_id}")
    
    try:
        service = PortfolioService(db)
        
        # 只傳入有值的欄位
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        
        transaction = await service.update_transaction(
            transaction_id=transaction_id,
            user_id=user.id,
            **update_data,
        )
        
        if not transaction:
            raise HTTPException(status_code=404, detail="找不到交易紀錄")
        
        return {
            "success": True,
            "message": "交易紀錄已更新",
            "data": transaction.to_dict(),
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新交易失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新交易失敗")


@router.delete("/transactions/{transaction_id}", summary="刪除交易紀錄")
async def delete_transaction(
    transaction_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """刪除交易紀錄"""
    logger.info(f"刪除交易: user={user.id}, id={transaction_id}")
    
    service = PortfolioService(db)
    success = await service.delete_transaction(transaction_id, user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="找不到交易紀錄")
    
    return {
        "success": True,
        "message": "交易紀錄已刪除",
    }


# ============================================================
# 持股 API
# ============================================================

@router.get("/holdings", summary="取得持股總覽")
async def get_holdings(
    market: Optional[str] = Query(None, pattern="^(tw|us)$", description="篩選市場"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶的持股列表（含現價和損益）
    
    - 現價來自價格快取
    - 包含未實現損益計算
    """
    try:
        service = PortfolioService(db)
        holdings = await service.get_holdings_with_prices(user.id, market)
        
        # 分類
        tw_holdings = [h for h in holdings if h['market'] == 'tw' and h['total_shares'] > 0]
        us_holdings = [h for h in holdings if h['market'] == 'us' and h['total_shares'] > 0]
        
        return {
            "success": True,
            "data": {
                "tw": tw_holdings,
                "us": us_holdings,
            },
            "total": len(tw_holdings) + len(us_holdings),
        }
        
    except Exception as e:
        logger.error(f"取得持股失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="取得持股失敗")


@router.get("/summary", summary="取得投資摘要")
async def get_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得投資組合摘要統計
    
    包含：
    - 匯率資訊
    - 台股統計
    - 美股統計
    - 總計（換算 TWD）
    """
    try:
        service = PortfolioService(db)
        summary = await service.get_summary(user.id)
        
        return {
            "success": True,
            "data": summary,
        }
        
    except Exception as e:
        logger.error(f"取得投資摘要失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="取得投資摘要失敗")
