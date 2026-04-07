"""
通知記錄資料模型
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Notification(Base):
    """通知記錄"""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(10), nullable=False)
    asset_type = Column(String(10), nullable=False)  # stock / crypto
    alert_type = Column(String(30), nullable=False)  # 通知類型
    indicator = Column(String(20))  # 相關指標
    message = Column(Text)  # 通知內容
    price_at_trigger = Column(Numeric(18, 8))  # 觸發時價格
    triggered_at = Column(DateTime, server_default=func.now())
    sent = Column(Boolean, default=False)  # 是否已發送
    sent_at = Column(DateTime)  # 發送時間
    
    # 關聯
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_notification_user', 'user_id'),
        Index('idx_notification_symbol', 'symbol'),
        Index('idx_notification_triggered', 'triggered_at'),
    )
    
    # 通知類型常數
    ALERT_TYPES = {
        "ma_golden_cross": "均線黃金交叉",
        "ma_death_cross": "均線死亡交叉",
        "approaching_breakout": "接近向上突破",
        "approaching_breakdown": "接近向下跌破",
        "breakout": "已突破",
        "breakdown": "已跌破",
        "rsi_overbought": "RSI 超買",
        "rsi_oversold": "RSI 超賣",
        "macd_golden_cross": "MACD 黃金交叉",
        "macd_death_cross": "MACD 死亡交叉",
        "kd_golden_cross": "KD 黃金交叉",
        "kd_death_cross": "KD 死亡交叉",
        "bollinger_breakout": "布林上軌突破",
        "bollinger_breakdown": "布林下軌跌破",
        "volume_surge": "成交量暴增",
        "sentiment_extreme_fear": "極度恐懼",
        "sentiment_extreme_greed": "極度貪婪",
    }
    
    def __repr__(self):
        return f"<Notification(user_id={self.user_id}, symbol={self.symbol}, alert_type={self.alert_type})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "asset_type": self.asset_type,
            "alert_type": self.alert_type,
            "alert_type_zh": self.ALERT_TYPES.get(self.alert_type, self.alert_type),
            "indicator": self.indicator,
            "message": self.message,
            "price_at_trigger": float(self.price_at_trigger) if self.price_at_trigger else None,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "sent": self.sent,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }
