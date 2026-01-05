"""
用戶資料模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """用戶資料"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    line_user_id = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    picture_url = Column(String(500))
    email = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 關聯
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    indicator_settings = relationship("UserIndicatorSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    alert_settings = relationship("UserAlertSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, line_user_id={self.line_user_id}, display_name={self.display_name})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "line_user_id": self.line_user_id,
            "display_name": self.display_name,
            "picture_url": self.picture_url,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
