"""
è¿½è¹¤æ¸…å–®åˆ†çµ„æ¨™ç±¤
==================
æ”¯æ´ç”¨æˆ¶è‡ªè¨‚æ¨™ç±¤ä¾†åˆ†é¡žè¿½è¹¤çš„è‚¡ç¥¨

P1 åŠŸèƒ½ï¼šè¿½è¹¤æ¸…å–®åˆ†çµ„ Tag
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


# å¤šå°å¤šé—œè¯è¡¨ï¼šè¿½è¹¤é …ç›® <-> æ¨™ç±¤
# æ³¨æ„ï¼šWatchlist è¡¨åæ˜¯ "watchlists"ï¼ˆæœ‰ sï¼‰
watchlist_tags = Table(
    'watchlist_tags',
    Base.metadata,
    Column('watchlist_id', Integer, ForeignKey('watchlists.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('user_tags.id', ondelete='CASCADE'), primary_key=True),
)


class UserTag(Base):
    """ç”¨æˆ¶è‡ªè¨‚æ¨™ç±¤"""
    
    __tablename__ = "user_tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # æ¨™ç±¤è³‡è¨Š
    name = Column(String(50), nullable=False)      # æ¨™ç±¤åç¨±
    color = Column(String(20), default="#3B82F6")  # æ¨™ç±¤é¡è‰² (hex)
    icon = Column(String(50), default="fa-tag")    # æ¨™ç±¤åœ–ç¤º
    sort_order = Column(Integer, default=0)        # æŽ’åºé †åº
    
    # æ™‚é–“æˆ³
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # ç´¢å¼•
    __table_args__ = (
        Index('idx_user_tags_user_id', 'user_id'),
        Index('idx_user_tags_user_name', 'user_id', 'name', unique=True),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "color": self.color,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<UserTag {self.name}>"


# ============================================================
# é è¨­æ¨™ç±¤é¡è‰²é¸é …
# ============================================================

TAG_COLORS = [
    {"name": "è—è‰²", "value": "#3B82F6"},
    {"name": "ç¶ è‰²", "value": "#10B981"},
    {"name": "ç´…è‰²", "value": "#EF4444"},
    {"name": "é»ƒè‰²", "value": "#F59E0B"},
    {"name": "ç´«è‰²", "value": "#8B5CF6"},
    {"name": "ç²‰è‰²", "value": "#EC4899"},
    {"name": "é›è‰²", "value": "#6366F1"},
    {"name": "é’è‰²", "value": "#06B6D4"},
    {"name": "æ©™è‰²", "value": "#F97316"},
    {"name": "ç°è‰²", "value": "#6B7280"},
]

TAG_ICONS = [
    {"name": "æ¨™ç±¤", "value": "fa-tag"},
    {"name": "æ˜Ÿæ˜Ÿ", "value": "fa-star"},
    {"name": "å¿ƒå½¢", "value": "fa-heart"},
    {"name": "æ›¸ç±¤", "value": "fa-bookmark"},
    {"name": "æ——å¹Ÿ", "value": "fa-flag"},
    {"name": "è³‡æ–™å¤¾", "value": "fa-folder"},
    {"name": "ç«ç„°", "value": "fa-fire"},
    {"name": "é–ƒé›»", "value": "fa-bolt"},
    {"name": "çŽç›ƒ", "value": "fa-trophy"},
    {"name": "æ”¾å¤§é¡", "value": "fa-search"},
]

# é è¨­æ¨™ç±¤ç¯„ä¾‹
DEFAULT_TAGS = [
    {"name": "é•·æœŸæŒæœ‰", "color": "#10B981", "icon": "fa-star"},
    {"name": "è§€æœ›ä¸­", "color": "#F59E0B", "icon": "fa-search"},
    {"name": "çŸ­ç·šäº¤æ˜“", "color": "#EF4444", "icon": "fa-bolt"},
    {"name": "ETF", "color": "#3B82F6", "icon": "fa-layer-group"},
    {"name": "é«˜è‚¡æ¯", "color": "#8B5CF6", "icon": "fa-coins"},
]