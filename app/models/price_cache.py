"""
股票價格快取 Model
"""
from sqlalchemy import Column, String, Numeric, BigInteger, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class StockPriceCache(Base):
    """股票即時價格快取"""
    
    __tablename__ = "stock_price_cache"
    
    symbol = Column(String(20), primary_key=True)
    name = Column(String(100))
    price = Column(Numeric(12, 4))
    prev_close = Column(Numeric(12, 4))
    change = Column(Numeric(12, 4))
    change_pct = Column(Numeric(8, 4))
    volume = Column(BigInteger)
    asset_type = Column(String(10), default="stock")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": float(self.price) if self.price else None,
            "change_pct": float(self.change_pct) if self.change_pct else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
