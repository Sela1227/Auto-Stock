"""
å ±é…¬çŽ‡æ¯”è¼ƒçµ„åˆ Model
å„²å­˜ç”¨æˆ¶çš„è‡ªè¨‚æ¯”è¼ƒçµ„åˆ
"""
from datetime import datetime
from typing import List, Optional
import json

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Comparison(Base):
    """ç”¨æˆ¶å„²å­˜çš„æ¯”è¼ƒçµ„åˆ"""
    __tablename__ = "comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # çµ„åˆåç¨±
    symbols_json = Column(Text, nullable=False)  # JSON æ ¼å¼å„²å­˜ ["AAPL","MSFT"]
    benchmark = Column(String(20), nullable=True, default="^GSPC")  # åŸºæº–æŒ‡æ•¸
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # é—œè¯
    user = relationship("User", backref="comparisons")
    
    @property
    def symbols(self) -> List[str]:
        """å–å¾—æ¨™çš„åˆ—è¡¨"""
        try:
            return json.loads(self.symbols_json)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @symbols.setter
    def symbols(self, value: List[str]):
        """è¨­å®šæ¨™çš„åˆ—è¡¨"""
        self.symbols_json = json.dumps(value)
    
    def to_dict(self) -> dict:
        """è½‰æ›ç‚ºå­—å…¸"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "symbols": self.symbols,
            "benchmark": self.benchmark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Comparison(id={self.id}, name='{self.name}', symbols={self.symbols})>"