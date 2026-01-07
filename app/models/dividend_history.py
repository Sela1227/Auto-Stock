"""
股票配息歷史資料模型
用於計算含息年化報酬率
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class DividendHistory(Base):
    """股票配息歷史"""
    
    __tablename__ = "dividend_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)  # 除息日
    amount = Column(Numeric(10, 4), nullable=False)  # 每股配息金額
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_dividend_symbol_date', 'symbol', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<DividendHistory(symbol={self.symbol}, date={self.date}, amount={self.amount})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "date": self.date.isoformat() if self.date else None,
            "amount": float(self.amount) if self.amount else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
