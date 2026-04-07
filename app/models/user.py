"""
ç”¨æˆ¶è³‡æ–™æ¨¡åž‹
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """ç”¨æˆ¶è³‡æ–™"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    line_user_id = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    picture_url = Column(String(500))
    email = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # ç®¡ç†å“¡
    is_blocked = Column(Boolean, default=False)  # å°éŽ–
    blocked_reason = Column(String(200))  # å°éŽ–åŽŸå› 
    blocked_at = Column(DateTime)  # å°éŽ–æ™‚é–“
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # é—œè¯
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    indicator_settings = relationship("UserIndicatorSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    alert_settings = relationship("UserAlertSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    login_logs = relationship("LoginLog", back_populates="user", cascade="all, delete-orphan")
    
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
            "is_admin": self.is_admin,
            "is_blocked": self.is_blocked,
            "blocked_reason": self.blocked_reason,
            "blocked_at": self.blocked_at.isoformat() if self.blocked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class LoginLog(Base):
    """ç™»å…¥æ—¥èªŒ"""
    
    __tablename__ = "login_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(20), nullable=False)  # login, logout, token_refresh
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    
    # é—œè¯
    user = relationship("User", back_populates="login_logs")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TokenBlacklist(Base):
    """Token é»‘åå–®ï¼ˆç”¨æ–¼è¸¢å‡ºç”¨æˆ¶ï¼‰"""
    
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_jti = Column(String(100), unique=True, nullable=False, index=True)  # JWT ID
    user_id = Column(Integer, index=True)
    reason = Column(String(100))  # kicked, logout, blocked
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)  # Token éŽæœŸæ™‚é–“ï¼ˆéŽæœŸå¾Œå¯æ¸…ç†ï¼‰
    
    def to_dict(self):
        return {
            "id": self.id,
            "token_jti": self.token_jti,
            "user_id": self.user_id,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SystemConfig(Base):
    """ç³»çµ±è¨­å®š"""
    
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(String(200))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }