"""
券商模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.sql import func
from app.database import Base


class Broker(Base):
    """券商"""
    
    __tablename__ = "brokers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)          # 券商名稱
    color = Column(String(20), default="#6B7280")      # 顏色
    is_default = Column(Boolean, default=False)        # 預設券商
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_broker_user', 'user_id'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "is_default": self.is_default,
        }
