"""
追蹤清單分組標籤
==================
支援用戶自訂標籤來分類追蹤的股票

P1 功能：追蹤清單分組 Tag
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


# 多對多關聯表：追蹤項目 <-> 標籤
# 注意：Watchlist 表名是 "watchlists"（有 s）
watchlist_tags = Table(
    'watchlist_tags',
    Base.metadata,
    Column('watchlist_id', Integer, ForeignKey('watchlists.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('user_tags.id', ondelete='CASCADE'), primary_key=True),
)


class UserTag(Base):
    """用戶自訂標籤"""
    
    __tablename__ = "user_tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # 標籤資訊
    name = Column(String(50), nullable=False)      # 標籤名稱
    color = Column(String(20), default="#3B82F6")  # 標籤顏色 (hex)
    icon = Column(String(50), default="fa-tag")    # 標籤圖示
    sort_order = Column(Integer, default=0)        # 排序順序
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 索引
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
# 預設標籤顏色選項
# ============================================================

TAG_COLORS = [
    {"name": "藍色", "value": "#3B82F6"},
    {"name": "綠色", "value": "#10B981"},
    {"name": "紅色", "value": "#EF4444"},
    {"name": "黃色", "value": "#F59E0B"},
    {"name": "紫色", "value": "#8B5CF6"},
    {"name": "粉色", "value": "#EC4899"},
    {"name": "靛色", "value": "#6366F1"},
    {"name": "青色", "value": "#06B6D4"},
    {"name": "橙色", "value": "#F97316"},
    {"name": "灰色", "value": "#6B7280"},
]

TAG_ICONS = [
    {"name": "標籤", "value": "fa-tag"},
    {"name": "星星", "value": "fa-star"},
    {"name": "心形", "value": "fa-heart"},
    {"name": "書籤", "value": "fa-bookmark"},
    {"name": "旗幟", "value": "fa-flag"},
    {"name": "資料夾", "value": "fa-folder"},
    {"name": "火焰", "value": "fa-fire"},
    {"name": "閃電", "value": "fa-bolt"},
    {"name": "獎盃", "value": "fa-trophy"},
    {"name": "放大鏡", "value": "fa-search"},
]

# 預設標籤範例
DEFAULT_TAGS = [
    {"name": "長期持有", "color": "#10B981", "icon": "fa-star"},
    {"name": "觀望中", "color": "#F59E0B", "icon": "fa-search"},
    {"name": "短線交易", "color": "#EF4444", "icon": "fa-bolt"},
    {"name": "ETF", "color": "#3B82F6", "icon": "fa-layer-group"},
    {"name": "高股息", "color": "#8B5CF6", "icon": "fa-coins"},
]
