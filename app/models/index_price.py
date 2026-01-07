"""
市場指數價格歷史資料模型
支援 S&P 500, 道瓊, 納斯達克
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


# 三大指數代號對照
INDEX_SYMBOLS = {
    "^GSPC": {"name": "S&P 500", "name_zh": "標普500"},
    "^DJI": {"name": "Dow Jones", "name_zh": "道瓊工業"},
    "^IXIC": {"name": "NASDAQ", "name_zh": "納斯達克"},
}


class IndexPrice(Base):
    """市場指數價格歷史"""
    
    __tablename__ = "index_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)  # ^GSPC, ^DJI, ^IXIC
    name = Column(String(50))  # S&P 500, Dow Jones, NASDAQ
    date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(12, 2))
    high = Column(Numeric(12, 2))
    low = Column(Numeric(12, 2))
    close = Column(Numeric(12, 2))
    volume = Column(BigInteger)
    change = Column(Numeric(10, 2))  # 漲跌點數
    change_pct = Column(Numeric(6, 2))  # 漲跌幅 %
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_index_symbol_date', 'symbol', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<IndexPrice(symbol={self.symbol}, date={self.date}, close={self.close})>"
    
    @property
    def name_zh(self) -> str:
        """取得中文名稱"""
        info = INDEX_SYMBOLS.get(self.symbol, {})
        return info.get("name_zh", self.name or self.symbol)
    
    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "name_zh": self.name_zh,
            "date": self.date.isoformat() if self.date else None,
            "open": float(self.open) if self.open else None,
            "high": float(self.high) if self.high else None,
            "low": float(self.low) if self.low else None,
            "close": float(self.close) if self.close else None,
            "volume": self.volume,
            "change": float(self.change) if self.change else None,
            "change_pct": float(self.change_pct) if self.change_pct else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
