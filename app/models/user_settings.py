"""
ç”¨æˆ¶è¨­å®šè³‡æ–™æ¨¡åž‹
åŒ…å«æŒ‡æ¨™é¡¯ç¤ºè¨­å®šã€é€šçŸ¥è¨­å®šã€åƒæ•¸è¨­å®š
"""
from sqlalchemy import Column, Integer, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class UserIndicatorSettings(Base):
    """ç”¨æˆ¶æŒ‡æ¨™é¡¯ç¤ºè¨­å®š"""
    
    __tablename__ = "user_indicator_settings"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    show_ma = Column(Boolean, default=True)
    show_rsi = Column(Boolean, default=True)
    show_macd = Column(Boolean, default=True)
    show_kd = Column(Boolean, default=False)
    show_bollinger = Column(Boolean, default=True)
    show_obv = Column(Boolean, default=False)
    show_volume = Column(Boolean, default=True)
    
    # é—œè¯
    user = relationship("User", back_populates="indicator_settings")
    
    def __repr__(self):
        return f"<UserIndicatorSettings(user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "show_ma": self.show_ma,
            "show_rsi": self.show_rsi,
            "show_macd": self.show_macd,
            "show_kd": self.show_kd,
            "show_bollinger": self.show_bollinger,
            "show_obv": self.show_obv,
            "show_volume": self.show_volume,
        }
    
    @classmethod
    def create_default(cls, user_id: int):
        """å»ºç«‹é è¨­è¨­å®š"""
        return cls(user_id=user_id)


class UserAlertSettings(Base):
    """ç”¨æˆ¶é€šçŸ¥è¨­å®š"""
    
    __tablename__ = "user_alert_settings"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    alert_ma_cross = Column(Boolean, default=True)      # å‡ç·šäº¤å‰é€šçŸ¥
    alert_ma_breakout = Column(Boolean, default=True)   # å‡ç·šçªç ´é€šçŸ¥
    alert_rsi = Column(Boolean, default=True)           # RSI è¶…è²·è¶…è³£é€šçŸ¥
    alert_macd = Column(Boolean, default=True)          # MACD äº¤å‰é€šçŸ¥
    alert_kd = Column(Boolean, default=False)           # KD äº¤å‰é€šçŸ¥
    alert_bollinger = Column(Boolean, default=False)    # å¸ƒæž—çªç ´é€šçŸ¥
    alert_volume = Column(Boolean, default=False)       # é‡èƒ½ç•°å¸¸é€šçŸ¥
    alert_sentiment = Column(Boolean, default=True)     # æƒ…ç·’æ¥µç«¯é€šçŸ¥
    
    # é—œè¯
    user = relationship("User", back_populates="alert_settings")
    
    def __repr__(self):
        return f"<UserAlertSettings(user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "alert_ma_cross": self.alert_ma_cross,
            "alert_ma_breakout": self.alert_ma_breakout,
            "alert_rsi": self.alert_rsi,
            "alert_macd": self.alert_macd,
            "alert_kd": self.alert_kd,
            "alert_bollinger": self.alert_bollinger,
            "alert_volume": self.alert_volume,
            "alert_sentiment": self.alert_sentiment,
        }
    
    @classmethod
    def create_default(cls, user_id: int):
        """å»ºç«‹é è¨­è¨­å®š"""
        return cls(user_id=user_id)


class UserIndicatorParams(Base):
    """ç”¨æˆ¶æŒ‡æ¨™åƒæ•¸è¨­å®š"""
    
    __tablename__ = "user_indicator_params"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # å‡ç·š
    ma_short = Column(Integer, default=20)
    ma_mid = Column(Integer, default=50)
    ma_long = Column(Integer, default=200)
    
    # RSI
    rsi_period = Column(Integer, default=14)
    rsi_overbought = Column(Integer, default=70)
    rsi_oversold = Column(Integer, default=30)
    
    # MACD
    macd_fast = Column(Integer, default=12)
    macd_slow = Column(Integer, default=26)
    macd_signal = Column(Integer, default=9)
    
    # KD
    kd_period = Column(Integer, default=9)
    
    # å¸ƒæž—é€šé“
    bollinger_period = Column(Integer, default=20)
    bollinger_std = Column(Numeric(3, 1), default=2.0)
    
    # è­¦æˆ’å€¼
    breakout_threshold = Column(Numeric(4, 2), default=2.00)  # çªç ´é è­¦é–€æª» (%)
    volume_alert_ratio = Column(Numeric(3, 1), default=2.0)   # é‡æ¯”è­¦æˆ’å€æ•¸
    
    # é—œè¯
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserIndicatorParams(user_id={self.user_id})>"
    
    def to_dict(self):
        return {
            "ma_short": self.ma_short,
            "ma_mid": self.ma_mid,
            "ma_long": self.ma_long,
            "rsi_period": self.rsi_period,
            "rsi_overbought": self.rsi_overbought,
            "rsi_oversold": self.rsi_oversold,
            "macd_fast": self.macd_fast,
            "macd_slow": self.macd_slow,
            "macd_signal": self.macd_signal,
            "kd_period": self.kd_period,
            "bollinger_period": self.bollinger_period,
            "bollinger_std": float(self.bollinger_std) if self.bollinger_std else 2.0,
            "breakout_threshold": float(self.breakout_threshold) if self.breakout_threshold else 2.0,
            "volume_alert_ratio": float(self.volume_alert_ratio) if self.volume_alert_ratio else 2.0,
        }
    
    @classmethod
    def create_default(cls, user_id: int):
        """å»ºç«‹é è¨­è¨­å®š"""
        return cls(user_id=user_id)