"""
訂閱精選相關 Model
- SubscriptionSource: 訂閱源（如美股大叔）
- AutoPick: 自動抓取的標的
- UserSubscription: 用戶訂閱關係
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.database import Base


class SubscriptionSource(Base):
    """訂閱源"""
    __tablename__ = "subscription_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)          # "美股大叔"
    slug = Column(String(50), unique=True, nullable=False)  # "uncle-stock"
    url = Column(String(500), nullable=False)           # RSS feed URL
    type = Column(String(20), default="substack")       # substack, rss, etc.
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    last_fetched_at = Column(DateTime)                  # 最後抓取時間
    created_at = Column(DateTime, default=datetime.now)
    
    # 關聯
    auto_picks = relationship("AutoPick", back_populates="source")
    subscribers = relationship("UserSubscription", back_populates="source")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "url": self.url,
            "type": self.type,
            "description": self.description,
            "enabled": self.enabled,
            "last_fetched_at": self.last_fetched_at.isoformat() if self.last_fetched_at else None,
        }


class AutoPick(Base):
    """自動抓取的標的"""
    __tablename__ = "auto_picks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("subscription_sources.id"), nullable=False)
    symbol = Column(String(20), nullable=False)         # 股票代碼
    article_url = Column(String(500))                   # 出處連結
    article_title = Column(String(300))                 # 文章標題
    article_date = Column(Date)                         # 文章日期
    first_seen_at = Column(DateTime, default=datetime.now)  # 首次發現
    last_seen_at = Column(DateTime, default=datetime.now)   # 最近提及
    expires_at = Column(DateTime)                       # last_seen_at + 30天
    mention_count = Column(Integer, default=1)          # 提及次數
    created_at = Column(DateTime, default=datetime.now)
    
    # 關聯
    source = relationship("SubscriptionSource", back_populates="auto_picks")
    
    # 複合唯一：同來源 + 同代碼
    __table_args__ = (
        UniqueConstraint('source_id', 'symbol', name='uq_source_symbol'),
    )
    
    def update_mention(self, article_url: str = None, article_title: str = None, article_date: Date = None):
        """更新提及：重算過期時間、累加計數"""
        self.last_seen_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=30)
        self.mention_count += 1
        if article_url:
            self.article_url = article_url
        if article_title:
            self.article_title = article_title
        if article_date:
            self.article_date = article_date
    
    @property
    def is_active(self) -> bool:
        """是否仍在有效期內"""
        if not self.expires_at:
            return False
        return self.expires_at > datetime.now()
    
    @property
    def days_remaining(self) -> int:
        """剩餘天數"""
        if not self.expires_at:
            return 0
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)
    
    def to_dict(self):
        return {
            "id": self.id,
            "source_id": self.source_id,
            "symbol": self.symbol,
            "article_url": self.article_url,
            "article_title": self.article_title,
            "article_date": self.article_date.isoformat() if self.article_date else None,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "days_remaining": self.days_remaining,
            "mention_count": self.mention_count,
            "is_active": self.is_active,
        }


class UserSubscription(Base):
    """用戶訂閱關係"""
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("subscription_sources.id"), nullable=False)
    subscribed_at = Column(DateTime, default=datetime.now)
    
    # 關聯
    source = relationship("SubscriptionSource", back_populates="subscribers")
    
    # 複合唯一
    __table_args__ = (
        UniqueConstraint('user_id', 'source_id', name='uq_user_source'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "source_id": self.source_id,
            "subscribed_at": self.subscribed_at.isoformat() if self.subscribed_at else None,
        }
