"""
è‚¡ç¥¨é…æ¯æ­·å²è³‡æ–™æ¨¡åž‹
ç”¨æ–¼è¨ˆç®—å«æ¯å¹´åŒ–å ±é…¬çŽ‡
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class DividendHistory(Base):
    """è‚¡ç¥¨é…æ¯æ­·å²"""
    
    __tablename__ = "dividend_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)  # é™¤æ¯æ—¥
    amount = Column(Numeric(10, 4), nullable=False)  # æ¯è‚¡é…æ¯é‡‘é¡
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