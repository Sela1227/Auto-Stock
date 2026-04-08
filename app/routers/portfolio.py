"""
個人投資記錄 API 路由
🔧 P0修復：使用統一認證模組
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import logging
import json
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_session
from app.services.portfolio_service import PortfolioService
from app.services.exchange_rate_service import get_exchange_rate, set_exchange_rate
from app.models.user import User
from app.models.portfolio import PortfolioTransaction

# 🔧 使用統一認證模組
from app.dependencies import get_current_user

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
    broker_id: Optional[int] = Field(None, description="券商 ID")


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
    broker_id: Optional[int] = None


class ExchangeRateUpdate(BaseModel):
    """更新匯率請求"""
    rate: float = Field(..., gt=0, description="USD/TWD 匯率")


class TransactionImportItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: str = "tw"
    transaction_type: str = "buy"
    quantity: int
    price: float
    fee: Optional[float] = 0
    tax: Optional[float] = 0
    transaction_date: str  # YYYY-MM-DD format
    note: Optional[str] = None


class TransactionImportRequest(BaseModel):
    items: List[TransactionImportItem]


# ============================================================
# 匯出匯入 API
# ============================================================

@router.get("/export", summary="匯出交易記錄")
async def export_transactions(
    format: str = "json",
    market: Optional[str] = Query(None, pattern="^(tw|us)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    匯出用戶的交易記錄
    
    - format: json 或 csv
    - market: 選擇性篩選市場 (tw/us)
    """
    logger.info(f"API: 匯出交易記錄 - user_id={user.id}, format={format}, market={market}")

    try:
        service = PortfolioService(db)
        transactions = await service.get_transactions(
            user_id=user.id,
            market=market,
            limit=9999,
            offset=0,
        )

        if not transactions:
            raise HTTPException(status_code=404, detail="交易記錄為空")

        # 準備匯出資料
        export_data = []
        for t in transactions:
            export_data.append({
                "symbol": t.symbol,
                "name": t.name or "",
                "market": t.market,
                "transaction_type": t.transaction_type,
                "quantity": t.quantity,
                "price": float(t.price),
                "fee": float(t.fee) if t.fee else 0,
                "tax": float(t.tax) if t.tax else 0,
                "transaction_date": t.transaction_date.isoformat() if t.transaction_date else "",
                "note": t.note or "",
            })

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        market_suffix = f"_{market}" if market else ""

        if format.lower() == "csv":
            # CSV 格式
            output = io.StringIO()
            fieldnames = ["symbol", "name", "market", "transaction_type", "quantity", 
                         "price", "fee", "tax", "transaction_date", "note"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_data)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=portfolio{market_suffix}_{timestamp}.csv"
                }
            )
        else:
            # JSON 格式
            json_str = json.dumps({
                "export_time": datetime.now().isoformat(),
                "market": market,
                "total": len(export_data),
                "items": export_data
            }, ensure_ascii=False, indent=2)
            
            return StreamingResponse(
                iter([json_str]),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=portfolio{market_suffix}_{timestamp}.json"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"匯出交易記錄失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", summary="匯入交易記錄")
async def import_transactions(
    data: TransactionImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    匯入交易記錄
    
    - 逐筆新增交易記錄
    - 返回成功/失敗的統計
    """
    logger.info(f"API: 匯入交易記錄 - user_id={user.id}, items={len(data.items)}")

    try:
        service = PortfolioService(db)
        added = []
        errors = []

        for item in data.items:
            try:
                # 解析日期
                trans_date = datetime.strptime(item.transaction_date, "%Y-%m-%d").date()
                
                transaction = await service.create_transaction(
                    user_id=user.id,
                    symbol=item.symbol.upper().strip(),
                    name=item.name,
                    market=item.market,
                    transaction_type=item.transaction_type,
                    quantity=item.quantity,
                    price=item.price,
                    fee=item.fee or 0,
                    tax=item.tax or 0,
                    transaction_date=trans_date,
                    note=item.note,
                )
                added.append({
                    "id": transaction.id,
                    "symbol": transaction.symbol,
                    "transaction_type": transaction.transaction_type,
                })
            except Exception as e:
                errors.append({
                    "symbol": item.symbol,
                    "date": item.transaction_date,
                    "error": str(e)
                })

        return {
            "success": True,
            "message": f"匯入完成：成功 {len(added)} 筆，失敗 {len(errors)} 筆",
            "data": {
                "added": added,
                "errors": errors,
                "total_added": len(added),
                "total_errors": len(errors),
            }
        }

    except Exception as e:
        logger.error(f"匯入交易記錄失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
            broker_id=getattr(data, "broker_id", None),
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




@router.get("/transactions/last-price/{symbol}", summary="取得股票最後交易價格")
async def get_last_transaction_price(
    symbol: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶對該股票的最後一筆交易價格
    用於新增交易時自動帶入預設價格
    """
    try:
        stmt = select(PortfolioTransaction).where(
            PortfolioTransaction.user_id == user.id,
            PortfolioTransaction.symbol == symbol
        ).order_by(PortfolioTransaction.transaction_date.desc(), PortfolioTransaction.id.desc()).limit(1)
        
        result = await db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if transaction:
            return {
                "success": True,
                "price": float(transaction.price),
                "date": str(transaction.transaction_date),
                "type": transaction.transaction_type,
            }
        else:
            return {
                "success": False,
                "message": "無歷史交易記錄"
            }
    except Exception as e:
        logger.error(f"查詢最後交易價格失敗: {e}")
        return {
            "success": False,
            "message": str(e)
        }

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
