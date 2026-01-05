"""
股票價格歷史資料模型
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class StockPrice(Base):
    """美股價格歷史"""
    
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    volume = Column(BigInteger)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_stock_symbol_date', 'symbol', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<StockPrice(symbol={self.symbol}, date={self.date}, close={self.close})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "date": self.date.isoformat() if self.date else None,
            "open": float(self.open) if self.open else None,
            "high": float(self.high) if self.high else None,
            "low": float(self.low) if self.low else None,
            "close": float(self.close) if self.close else None,
            "volume": self.volume,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
