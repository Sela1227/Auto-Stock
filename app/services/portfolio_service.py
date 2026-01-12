"""
投資組合業務邏輯服務
處理交易紀錄的 CRUD 和持股計算
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
import logging

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import PortfolioTransaction, PortfolioHolding
from app.models.price_cache import StockPriceCache

logger = logging.getLogger(__name__)


class PortfolioService:
    """投資組合服務"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============================================================
    # 交易紀錄 CRUD
    # ============================================================
    
    async def create_transaction(
        self,
        user_id: int,
        symbol: str,
        market: str,
        transaction_type: str,
        quantity: int,
        price: float,
        transaction_date: date,
        name: Optional[str] = None,
        fee: float = 0,
        tax: float = 0,
        note: Optional[str] = None,
    ) -> PortfolioTransaction:
        """新增交易紀錄"""
        
        # 驗證
        if transaction_type not in ("buy", "sell"):
            raise ValueError("transaction_type 必須是 'buy' 或 'sell'")
        if market not in ("tw", "us"):
            raise ValueError("market 必須是 'tw' 或 'us'")
        if quantity <= 0:
            raise ValueError("quantity 必須大於 0")
        if price <= 0:
            raise ValueError("price 必須大於 0")
        
        # 標準化 symbol
        symbol = symbol.upper().strip()
        
        # 建立交易紀錄
        transaction = PortfolioTransaction(
            user_id=user_id,
            symbol=symbol,
            name=name,
            market=market,
            transaction_type=transaction_type,
            quantity=quantity,
            price=Decimal(str(price)),
            fee=Decimal(str(fee)) if fee else Decimal("0"),
            tax=Decimal(str(tax)) if tax else Decimal("0"),
            transaction_date=transaction_date,
            note=note,
        )
        
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        
        logger.info(f"新增交易: user={user_id}, {transaction_type} {quantity} {symbol} @ {price}")
        
        # 更新持股彙總
        await self._update_holding(user_id, symbol, market, name)
        
        return transaction
    
    async def get_transaction(self, transaction_id: int, user_id: int) -> Optional[PortfolioTransaction]:
        """取得單筆交易"""
        stmt = select(PortfolioTransaction).where(
            and_(
                PortfolioTransaction.id == transaction_id,
                PortfolioTransaction.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_transactions(
        self,
        user_id: int,
        market: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PortfolioTransaction]:
        """取得交易紀錄列表"""
        stmt = select(PortfolioTransaction).where(
            PortfolioTransaction.user_id == user_id
        )
        
        if market:
            stmt = stmt.where(PortfolioTransaction.market == market)
        if symbol:
            stmt = stmt.where(PortfolioTransaction.symbol == symbol.upper())
        
        stmt = stmt.order_by(PortfolioTransaction.transaction_date.desc())
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update_transaction(
        self,
        transaction_id: int,
        user_id: int,
        **kwargs,
    ) -> Optional[PortfolioTransaction]:
        """更新交易紀錄"""
        transaction = await self.get_transaction(transaction_id, user_id)
        if not transaction:
            return None
        
        old_symbol = transaction.symbol
        old_market = transaction.market
        
        # 更新欄位
        allowed_fields = {
            'symbol', 'name', 'market', 'transaction_type',
            'quantity', 'price', 'fee', 'tax', 'transaction_date', 'note'
        }
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                if key in ('price', 'fee', 'tax'):
                    value = Decimal(str(value))
                if key == 'symbol':
                    value = value.upper().strip()
                setattr(transaction, key, value)
        
        await self.db.commit()
        await self.db.refresh(transaction)
        
        # 更新持股彙總
        await self._update_holding(user_id, transaction.symbol, transaction.market, transaction.name)
        
        # 如果 symbol 或 market 改變，也要更新舊的
        if old_symbol != transaction.symbol or old_market != transaction.market:
            await self._update_holding(user_id, old_symbol, old_market)
        
        logger.info(f"更新交易: id={transaction_id}")
        return transaction
    
    async def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """刪除交易紀錄"""
        transaction = await self.get_transaction(transaction_id, user_id)
        if not transaction:
            return False
        
        symbol = transaction.symbol
        market = transaction.market
        
        await self.db.delete(transaction)
        await self.db.commit()
        
        # 更新持股彙總
        await self._update_holding(user_id, symbol, market)
        
        logger.info(f"刪除交易: id={transaction_id}")
        return True
    
    # ============================================================
    # 持股彙總
    # ============================================================
    
    async def _update_holding(
        self,
        user_id: int,
        symbol: str,
        market: str,
        name: Optional[str] = None,
    ):
        """更新單一股票的持股彙總"""
        
        # 取得該股票的所有交易
        stmt = select(PortfolioTransaction).where(
            and_(
                PortfolioTransaction.user_id == user_id,
                PortfolioTransaction.symbol == symbol,
                PortfolioTransaction.market == market,
            )
        ).order_by(PortfolioTransaction.transaction_date.asc())
        
        result = await self.db.execute(stmt)
        transactions = list(result.scalars().all())
        
        # 計算持股
        total_shares = 0
        total_cost = Decimal("0")
        realized_profit = Decimal("0")
        latest_name = name
        
        for tx in transactions:
            if tx.name:
                latest_name = tx.name
            
            if tx.transaction_type == "buy":
                total_shares += tx.quantity
                total_cost += Decimal(str(tx.quantity)) * tx.price + (tx.fee or Decimal("0"))
            else:  # sell
                if total_shares > 0:
                    # 計算已實現損益（先進先出）
                    avg_cost = total_cost / Decimal(str(total_shares)) if total_shares > 0 else Decimal("0")
                    sell_revenue = Decimal(str(tx.quantity)) * tx.price - (tx.fee or Decimal("0")) - (tx.tax or Decimal("0"))
                    sell_cost = avg_cost * Decimal(str(tx.quantity))
                    realized_profit += sell_revenue - sell_cost
                    
                    # 更新持股和成本
                    total_shares -= tx.quantity
                    total_cost -= sell_cost
                    
                    if total_shares <= 0:
                        total_shares = 0
                        total_cost = Decimal("0")
        
        # 計算平均成本
        avg_cost = total_cost / Decimal(str(total_shares)) if total_shares > 0 else Decimal("0")
        
        # 更新或建立 Holding
        stmt = select(PortfolioHolding).where(
            and_(
                PortfolioHolding.user_id == user_id,
                PortfolioHolding.symbol == symbol,
                PortfolioHolding.market == market,
            )
        )
        result = await self.db.execute(stmt)
        holding = result.scalar_one_or_none()
        
        if total_shares > 0 or realized_profit != 0:
            if holding:
                holding.total_shares = total_shares
                holding.avg_cost = avg_cost
                holding.total_invested = total_cost
                holding.realized_profit = realized_profit
                if latest_name:
                    holding.name = latest_name
            else:
                holding = PortfolioHolding(
                    user_id=user_id,
                    symbol=symbol,
                    name=latest_name,
                    market=market,
                    total_shares=total_shares,
                    avg_cost=avg_cost,
                    total_invested=total_cost,
                    realized_profit=realized_profit,
                )
                self.db.add(holding)
            
            await self.db.commit()
        elif holding:
            # 沒有持股也沒有已實現損益，刪除 Holding
            await self.db.delete(holding)
            await self.db.commit()
    
    async def get_holdings(
        self,
        user_id: int,
        market: Optional[str] = None,
    ) -> List[PortfolioHolding]:
        """取得持股列表"""
        stmt = select(PortfolioHolding).where(
            PortfolioHolding.user_id == user_id
        )
        
        if market:
            stmt = stmt.where(PortfolioHolding.market == market)
        
        stmt = stmt.order_by(PortfolioHolding.symbol)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_holdings_with_prices(
        self,
        user_id: int,
        market: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """取得持股列表（含現價）"""
        holdings = await self.get_holdings(user_id, market)
        
        if not holdings:
            return []
        
        # 取得價格快取
        symbols = [h.symbol for h in holdings]
        cache_stmt = select(StockPriceCache).where(
            StockPriceCache.symbol.in_(symbols)
        )
        cache_result = await self.db.execute(cache_stmt)
        price_cache = {r.symbol: r for r in cache_result.scalars().all()}
        
        # 組合資料
        result = []
        for h in holdings:
            cache = price_cache.get(h.symbol)
            current_price = float(cache.price) if cache and cache.price else None
            
            # 計算未實現損益
            unrealized_profit = None
            unrealized_profit_pct = None
            current_value = None
            
            if current_price and h.total_shares > 0:
                current_value = current_price * h.total_shares
                cost_basis = float(h.avg_cost) * h.total_shares if h.avg_cost else 0
                unrealized_profit = current_value - cost_basis
                if cost_basis > 0:
                    unrealized_profit_pct = (unrealized_profit / cost_basis) * 100
            
            result.append({
                **h.to_dict(),
                "current_price": current_price,
                "current_value": current_value,
                "unrealized_profit": unrealized_profit,
                "unrealized_profit_pct": unrealized_profit_pct,
                "price_change_pct": float(cache.change_pct) if cache and cache.change_pct else None,
            })
        
        return result
    
    async def get_summary(self, user_id: int) -> Dict[str, Any]:
        """取得投資摘要"""
        holdings = await self.get_holdings_with_prices(user_id)
        
        # 分類統計
        tw_holdings = [h for h in holdings if h['market'] == 'tw']
        us_holdings = [h for h in holdings if h['market'] == 'us']
        
        # 計算總值
        total_invested = sum(float(h['total_invested'] or 0) for h in holdings)
        total_current_value = sum(h['current_value'] or 0 for h in holdings if h['current_value'])
        total_realized = sum(float(h['realized_profit'] or 0) for h in holdings)
        total_unrealized = sum(h['unrealized_profit'] or 0 for h in holdings if h['unrealized_profit'])
        
        # 報酬率
        return_rate = None
        if total_invested > 0:
            total_profit = total_realized + total_unrealized
            return_rate = (total_profit / total_invested) * 100
        
        return {
            "total_invested": total_invested,
            "current_value": total_current_value,
            "realized_profit": total_realized,
            "unrealized_profit": total_unrealized,
            "total_profit": total_realized + total_unrealized,
            "return_rate": return_rate,
            "tw_count": len([h for h in tw_holdings if h['total_shares'] > 0]),
            "us_count": len([h for h in us_holdings if h['total_shares'] > 0]),
            "total_positions": len([h for h in holdings if h['total_shares'] > 0]),
        }
