"""
加密貨幣價格歷史資料模型
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class CryptoPrice(Base):
    """加密貨幣價格歷史"""
    
    __tablename__ = "crypto_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)  # BTC, ETH
    date = Column(Date, nullable=False, index=True)
    price = Column(Numeric(18, 8))  # USD 價格
    volume_24h = Column(Numeric(18, 2))  # 24 小時成交量
    market_cap = Column(Numeric(18, 2))  # 市值
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_crypto_symbol_date', 'symbol', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<CryptoPrice(symbol={self.symbol}, date={self.date}, price={self.price})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "date": self.date.isoformat() if self.date else None,
            "price": float(self.price) if self.price else None,
            "volume_24h": float(self.volume_24h) if self.volume_24h else None,
            "market_cap": float(self.market_cap) if self.market_cap else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
