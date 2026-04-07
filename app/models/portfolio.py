"""
å€‹äººæŠ•è³‡è¨˜éŒ„æ¨¡åž‹
ç”¨æ–¼è¨˜éŒ„ç”¨æˆ¶çš„è‚¡ç¥¨è²·è³£äº¤æ˜“åŠåŒ¯çŽ‡
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, Index, Text, Float
from sqlalchemy.sql import func

from app.database import Base


class PortfolioTransaction(Base):
    """äº¤æ˜“ç´€éŒ„"""
    
    __tablename__ = "portfolio_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # è‚¡ç¥¨è³‡è¨Š
    symbol = Column(String(20), nullable=False)           # è‚¡ç¥¨ä»£ç¢¼
    name = Column(String(100))                            # è‚¡ç¥¨åç¨±
    market = Column(String(10), nullable=False)           # tw / us
    
    # äº¤æ˜“è³‡è¨Š
    transaction_type = Column(String(10), nullable=False) # buy / sell
    quantity = Column(Integer, nullable=False)            # ç¸½è‚¡æ•¸ï¼ˆå°è‚¡ï¼šå¼µÃ—1000 + é›¶è‚¡ï¼‰
    price = Column(Numeric(12, 4), nullable=False)        # æˆäº¤åƒ¹
    fee = Column(Numeric(10, 2), default=0)               # æ‰‹çºŒè²»
    tax = Column(Numeric(10, 2), default=0)               # äº¤æ˜“ç¨…ï¼ˆè³£å‡ºæ™‚ï¼‰
    transaction_date = Column(Date, nullable=False)       # äº¤æ˜“æ—¥æœŸ
    
    # å‚™è¨»
    note = Column(Text)
    
    # åˆ¸å•†
    broker_id = Column(Integer, ForeignKey("brokers.id", ondelete="SET NULL"), nullable=True)
    
    # æ™‚é–“æˆ³
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # ç´¢å¼•
    __table_args__ = (
        Index('idx_portfolio_user', 'user_id'),
        Index('idx_portfolio_symbol', 'symbol'),
        Index('idx_portfolio_market', 'market'),
        Index('idx_portfolio_date', 'transaction_date'),
        Index('idx_portfolio_user_symbol', 'user_id', 'symbol'),
    )
    
    @property
    def total_amount(self) -> float:
        """äº¤æ˜“ç¸½é¡ï¼ˆä¸å«æ‰‹çºŒè²»ï¼‰"""
        return float(self.quantity) * float(self.price)
    
    @property
    def total_cost(self) -> float:
        """ç¸½æˆæœ¬ï¼ˆå«æ‰‹çºŒè²»ã€ç¨…ï¼‰"""
        base = self.total_amount
        fee = float(self.fee or 0)
        tax = float(self.tax or 0)
        
        if self.transaction_type == "buy":
            return base + fee
        else:  # sell
            return base - fee - tax
    
    def format_quantity_display(self) -> str:
        """æ ¼å¼åŒ–é¡¯ç¤ºè‚¡æ•¸ï¼ˆå°è‚¡é¡¯ç¤ºå¼µ+é›¶è‚¡ï¼‰"""
        if self.market == 'tw':
            lots = self.quantity // 1000
            odd = self.quantity % 1000
            if lots > 0 and odd > 0:
                return f"{lots}å¼µ{odd}è‚¡"
            elif lots > 0:
                return f"{lots}å¼µ"
            else:
                return f"{odd}è‚¡"
        else:
            return f"{self.quantity}è‚¡"
    
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
    æŒè‚¡å½™ç¸½
    ç”±äº¤æ˜“ç´€éŒ„è¨ˆç®—è€Œä¾†ï¼Œç”¨æ–¼å¿«é€ŸæŸ¥è©¢
    """
    
    __tablename__ = "portfolio_holdings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100))
    market = Column(String(10), nullable=False)
    
    # æŒè‚¡è³‡è¨Š
    total_shares = Column(Integer, default=0)              # ç¸½æŒè‚¡
    avg_cost = Column(Numeric(12, 4), default=0)           # å¹³å‡æˆæœ¬
    total_invested = Column(Numeric(14, 2), default=0)     # ç¸½æŠ•å…¥é‡‘é¡
    realized_profit = Column(Numeric(14, 2), default=0)    # å·²å¯¦ç¾æç›Š
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_holding_user_symbol', 'user_id', 'symbol', 'market', unique=True),
        Index('idx_holding_user', 'user_id'),
    )
    
    def format_quantity_display(self) -> str:
        """æ ¼å¼åŒ–é¡¯ç¤ºè‚¡æ•¸ï¼ˆå°è‚¡é¡¯ç¤ºå¼µ+é›¶è‚¡ï¼‰"""
        if self.market == 'tw':
            lots = self.total_shares // 1000
            odd = self.total_shares % 1000
            if lots > 0 and odd > 0:
                return f"{lots}å¼µ{odd}è‚¡"
            elif lots > 0:
                return f"{lots}å¼µ"
            else:
                return f"{odd}è‚¡"
        else:
            return f"{self.total_shares}è‚¡"
    
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
    """åŒ¯çŽ‡è¡¨"""
    
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_currency = Column(String(10), nullable=False)    # USD
    to_currency = Column(String(10), nullable=False)      # TWD
    rate = Column(Float, nullable=False)                  # åŒ¯çŽ‡
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