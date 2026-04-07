"""
å¸‚å ´æŒ‡æ•¸åƒ¹æ ¼æ­·å²è³‡æ–™æ¨¡åž‹
æ”¯æ´ S&P 500, é“ç“Š, ç´æ–¯é”å…‹, å°è‚¡åŠ æ¬Š
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


# æŒ‡æ•¸ä»£è™Ÿå°ç…§
INDEX_SYMBOLS = {
    "^GSPC": {"name": "S&P 500", "name_zh": "æ¨™æ™®500"},
    "^DJI": {"name": "Dow Jones", "name_zh": "é“ç“Šå·¥æ¥­"},
    "^IXIC": {"name": "NASDAQ", "name_zh": "ç´æ–¯é”å…‹"},
    "^TWII": {"name": "TAIEX", "name_zh": "å°è‚¡åŠ æ¬Š"},
}


class IndexPrice(Base):
    """å¸‚å ´æŒ‡æ•¸åƒ¹æ ¼æ­·å²"""
    
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
    change = Column(Numeric(10, 2))  # æ¼²è·Œé»žæ•¸
    change_pct = Column(Numeric(6, 2))  # æ¼²è·Œå¹… %
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_index_symbol_date', 'symbol', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<IndexPrice(symbol={self.symbol}, date={self.date}, close={self.close})>"
    
    @property
    def name_zh(self) -> str:
        """å–å¾—ä¸­æ–‡åç¨±"""
        info = INDEX_SYMBOLS.get(self.symbol, {})
        return info.get("name_zh", self.name or self.symbol)
    
    def to_dict(self):
        def safe_float(val):
            """å®‰å…¨è½‰æ› floatï¼Œè™•ç† NaN å’Œ Infinity"""
            if val is None:
                return None
            try:
                f = float(val)
                # æª¢æŸ¥ NaN å’Œ Infinity
                import math
                if math.isnan(f) or math.isinf(f):
                    return None
                return f
            except (ValueError, TypeError):
                return None
        
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "name_zh": self.name_zh,
            "date": self.date.isoformat() if self.date else None,
            "open": safe_float(self.open),
            "high": safe_float(self.high),
            "low": safe_float(self.low),
            "close": safe_float(self.close),
            "volume": self.volume,
            "change": safe_float(self.change),
            "change_pct": safe_float(self.change_pct),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }