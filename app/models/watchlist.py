"""
追蹤清單資料模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Watchlist(Base):
    """用戶追蹤清單"""
    
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(10), nullable=False)
    asset_type = Column(String(10), nullable=False)  # stock / crypto
    note = Column(String(200))  # 自訂備註
    added_at = Column(DateTime, server_default=func.now())
    
    # 關聯
    user = relationship("User", back_populates="watchlists")
    
    __table_args__ = (
        Index('idx_watchlist_user', 'user_id'),
        Index('idx_watchlist_unique', 'user_id', 'symbol', 'asset_type', unique=True),
    )
    
    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, symbol={self.symbol}, asset_type={self.asset_type})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "asset_type": self.asset_type,
            "note": self.note,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }
