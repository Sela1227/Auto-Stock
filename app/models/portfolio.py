"""
個人投資記錄模型
用於記錄用戶的股票買賣交易及匯率
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, Index, Text, Float
from sqlalchemy.sql import func

from app.database import Base


class PortfolioTransaction(Base):
    """交易紀錄"""
    
    __tablename__ = "portfolio_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 股票資訊
    symbol = Column(String(20), nullable=False)           # 股票代碼
    name = Column(String(100))                            # 股票名稱
    market = Column(String(10), nullable=False)           # tw / us
    
    # 交易資訊
    transaction_type = Column(String(10), nullable=False) # buy / sell
    quantity = Column(Integer, nullable=False)            # 總股數（台股：張×1000 + 零股）
    price = Column(Numeric(12, 4), nullable=False)        # 成交價
    fee = Column(Numeric(10, 2), default=0)               # 手續費
    tax = Column(Numeric(10, 2), default=0)               # 交易稅（賣出時）
    transaction_date = Column(Date, nullable=False)       # 交易日期
    
    # 備註
    note = Column(Text)
    
    # 券商
    broker_id = Column(Integer, ForeignKey("brokers.id", ondelete="SET NULL"), nullable=True)
    
    # 時間戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_portfolio_user', 'user_id'),
        Index('idx_portfolio_symbol', 'symbol'),
        Index('idx_portfolio_market', 'market'),
        Index('idx_portfolio_date', 'transaction_date'),
        Index('idx_portfolio_user_symbol', 'user_id', 'symbol'),
    )
    
    @property
    def total_amount(self) -> float:
        """交易總額（不含手續費）"""
        return float(self.quantity) * float(self.price)
    
    @property
    def total_cost(self) -> float:
        """總成本（含手續費、稅）"""
        base = self.total_amount
        fee = float(self.fee or 0)
        tax = float(self.tax or 0)
        
        if self.transaction_type == "buy":
            return base + fee
        else:  # sell
            return base - fee - tax
    
    def format_quantity_display(self) -> str:
        """格式化顯示股數（台股顯示張+零股）"""
        if self.market == 'tw':
            lots = self.quantity // 1000
            odd = self.quantity % 1000
            if lots > 0 and odd > 0:
                return f"{lots}張{odd}股"
            elif lots > 0:
                return f"{lots}張"
            else:
                return f"{odd}股"
        else:
            return f"{self.quantity}股"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "transaction_type": self.transaction_type,
            "quantity": self.quantity,
            "quantity_display": self.format_quantity_display(),
            "price": float(self.price),
            "fee": float(self.fee or 0),
            "tax": float(self.tax or 0),
            "total_amount": self.total_amount,
            "total_cost": self.total_cost,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PortfolioHolding(Base):
    """
    持股彙總
    由交易紀錄計算而來，用於快速查詢
    """
    
    __tablename__ = "portfolio_holdings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100))
    market = Column(String(10), nullable=False)
    
    # 持股資訊
    total_shares = Column(Integer, default=0)              # 總持股
    avg_cost = Column(Numeric(12, 4), default=0)           # 平均成本
    total_invested = Column(Numeric(14, 2), default=0)     # 總投入金額
    realized_profit = Column(Numeric(14, 2), default=0)    # 已實現損益
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_holding_user_symbol', 'user_id', 'symbol', 'market', unique=True),
        Index('idx_holding_user', 'user_id'),
    )
    
    def format_quantity_display(self) -> str:
        """格式化顯示股數（台股顯示張+零股）"""
        if self.market == 'tw':
            lots = self.total_shares // 1000
            odd = self.total_shares % 1000
            if lots > 0 and odd > 0:
                return f"{lots}張{odd}股"
            elif lots > 0:
                return f"{lots}張"
            else:
                return f"{odd}股"
        else:
            return f"{self.total_shares}股"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "total_shares": self.total_shares,
            "quantity_display": self.format_quantity_display(),
            "avg_cost": float(self.avg_cost) if self.avg_cost else 0,
            "total_invested": float(self.total_invested) if self.total_invested else 0,
            "realized_profit": float(self.realized_profit) if self.realized_profit else 0,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ExchangeRate(Base):
    """匯率表"""
    
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_currency = Column(String(10), nullable=False)    # USD
    to_currency = Column(String(10), nullable=False)      # TWD
    rate = Column(Float, nullable=False)                  # 匯率
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_exchange_pair', 'from_currency', 'to_currency', unique=True),
    )
    
    def to_dict(self) -> dict:
        return {
            "from_currency": self.from_currency,
            "to_currency": self.to_currency,
            "rate": self.rate,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
