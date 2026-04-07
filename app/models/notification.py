"""
é€šçŸ¥è¨˜éŒ„è³‡æ–™æ¨¡åž‹
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Notification(Base):
    """é€šçŸ¥è¨˜éŒ„"""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(10), nullable=False)
    asset_type = Column(String(10), nullable=False)  # stock / crypto
    alert_type = Column(String(30), nullable=False)  # é€šçŸ¥é¡žåž‹
    indicator = Column(String(20))  # ç›¸é—œæŒ‡æ¨™
    message = Column(Text)  # é€šçŸ¥å…§å®¹
    price_at_trigger = Column(Numeric(18, 8))  # è§¸ç™¼æ™‚åƒ¹æ ¼
    triggered_at = Column(DateTime, server_default=func.now())
    sent = Column(Boolean, default=False)  # æ˜¯å¦å·²ç™¼é€
    sent_at = Column(DateTime)  # ç™¼é€æ™‚é–“
    
    # é—œè¯
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_notification_user', 'user_id'),
        Index('idx_notification_symbol', 'symbol'),
        Index('idx_notification_triggered', 'triggered_at'),
    )
    
    # é€šçŸ¥é¡žåž‹å¸¸æ•¸
    ALERT_TYPES = {
        "ma_golden_cross": "å‡ç·šé»ƒé‡‘äº¤å‰",
        "ma_death_cross": "å‡ç·šæ­»äº¡äº¤å‰",
        "approaching_breakout": "æŽ¥è¿‘å‘ä¸Šçªç ´",
        "approaching_breakdown": "æŽ¥è¿‘å‘ä¸‹è·Œç ´",
        "breakout": "å·²çªç ´",
        "breakdown": "å·²è·Œç ´",
        "rsi_overbought": "RSI è¶…è²·",
        "rsi_oversold": "RSI è¶…è³£",
        "macd_golden_cross": "MACD é»ƒé‡‘äº¤å‰",
        "macd_death_cross": "MACD æ­»äº¡äº¤å‰",
        "kd_golden_cross": "KD é»ƒé‡‘äº¤å‰",
        "kd_death_cross": "KD æ­»äº¡äº¤å‰",
        "bollinger_breakout": "å¸ƒæž—ä¸Šè»Œçªç ´",
        "bollinger_breakdown": "å¸ƒæž—ä¸‹è»Œè·Œç ´",
        "volume_surge": "æˆäº¤é‡æš´å¢ž",
        "sentiment_extreme_fear": "æ¥µåº¦ææ‡¼",
        "sentiment_extreme_greed": "æ¥µåº¦è²ªå©ª",
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