"""
è¨‚é–±ç²¾é¸ç›¸é—œ Model
- SubscriptionSource: è¨‚é–±æºï¼ˆå¦‚ç¾Žè‚¡å¤§å”ï¼‰
- AutoPick: è‡ªå‹•æŠ“å–çš„æ¨™çš„
- UserSubscription: ç”¨æˆ¶è¨‚é–±é—œä¿‚
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.database import Base


class SubscriptionSource(Base):
    """è¨‚é–±æº"""
    __tablename__ = "subscription_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)          # "ç¾Žè‚¡å¤§å”"
    slug = Column(String(50), unique=True, nullable=False)  # "uncle-stock"
    url = Column(String(500), nullable=False)           # RSS feed URL
    type = Column(String(20), default="substack")       # substack, rss, etc.
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    last_fetched_at = Column(DateTime)                  # æœ€å¾ŒæŠ“å–æ™‚é–“
    created_at = Column(DateTime, default=datetime.now)
    
    # é—œè¯
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
    """è‡ªå‹•æŠ“å–çš„æ¨™çš„"""
    __tablename__ = "auto_picks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("subscription_sources.id"), nullable=False)
    symbol = Column(String(20), nullable=False)         # è‚¡ç¥¨ä»£ç¢¼
    article_url = Column(String(500))                   # å‡ºè™•é€£çµ
    article_title = Column(String(300))                 # æ–‡ç« æ¨™é¡Œ
    article_date = Column(Date)                         # æ–‡ç« æ—¥æœŸ
    first_seen_at = Column(DateTime, default=datetime.now)  # é¦–æ¬¡ç™¼ç¾
    last_seen_at = Column(DateTime, default=datetime.now)   # æœ€è¿‘æåŠ
    expires_at = Column(DateTime)                       # last_seen_at + 30å¤©
    mention_count = Column(Integer, default=1)          # æåŠæ¬¡æ•¸
    created_at = Column(DateTime, default=datetime.now)
    
    # é—œè¯
    source = relationship("SubscriptionSource", back_populates="auto_picks")
    
    # è¤‡åˆå”¯ä¸€ï¼šåŒä¾†æº + åŒä»£ç¢¼
    __table_args__ = (
        UniqueConstraint('source_id', 'symbol', name='uq_source_symbol'),
    )
    
    def update_mention(self, article_url: str = None, article_title: str = None, article_date: Date = None):
        """æ›´æ–°æåŠï¼šé‡ç®—éŽæœŸæ™‚é–“ã€ç´¯åŠ è¨ˆæ•¸"""
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
        """æ˜¯å¦ä»åœ¨æœ‰æ•ˆæœŸå…§"""
        if not self.expires_at:
            return False
        return self.expires_at > datetime.now()
    
    @property
    def days_remaining(self) -> int:
        """å‰©é¤˜å¤©æ•¸"""
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
    """ç”¨æˆ¶è¨‚é–±é—œä¿‚"""
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("subscription_sources.id"), nullable=False)
    subscribed_at = Column(DateTime, default=datetime.now)
    
    # é—œè¯
    source = relationship("SubscriptionSource", back_populates="subscribers")
    
    # è¤‡åˆå”¯ä¸€
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