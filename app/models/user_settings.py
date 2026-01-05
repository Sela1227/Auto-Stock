"""
用戶設定資料模型
包含指標顯示設定、通知設定、參數設定
"""
from sqlalchemy import Column, Integer, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class UserIndicatorSettings(Base):
    """用戶指標顯示設定"""
    
    __tablename__ = "user_indicator_settings"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    show_ma = Column(Boolean, default=True)
    show_rsi = Column(Boolean, default=True)
    show_macd = Column(Boolean, default=True)
    show_kd = Column(Boolean, default=False)
    show_bollinger = Column(Boolean, default=True)
    show_obv = Column(Boolean, default=False)
    show_volume = Column(Boolean, default=True)
    
    # 關聯
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
        """建立預設設定"""
        return cls(user_id=user_id)


class UserAlertSettings(Base):
    """用戶通知設定"""
    
    __tablename__ = "user_alert_settings"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    alert_ma_cross = Column(Boolean, default=True)      # 均線交叉通知
    alert_ma_breakout = Column(Boolean, default=True)   # 均線突破通知
    alert_rsi = Column(Boolean, default=True)           # RSI 超買超賣通知
    alert_macd = Column(Boolean, default=True)          # MACD 交叉通知
    alert_kd = Column(Boolean, default=False)           # KD 交叉通知
    alert_bollinger = Column(Boolean, default=False)    # 布林突破通知
    alert_volume = Column(Boolean, default=False)       # 量能異常通知
    alert_sentiment = Column(Boolean, default=True)     # 情緒極端通知
    
    # 關聯
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
        """建立預設設定"""
        return cls(user_id=user_id)


class UserIndicatorParams(Base):
    """用戶指標參數設定"""
    
    __tablename__ = "user_indicator_params"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # 均線
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
    
    # 布林通道
    bollinger_period = Column(Integer, default=20)
    bollinger_std = Column(Numeric(3, 1), default=2.0)
    
    # 警戒值
    breakout_threshold = Column(Numeric(4, 2), default=2.00)  # 突破預警門檻 (%)
    volume_alert_ratio = Column(Numeric(3, 1), default=2.0)   # 量比警戒倍數
    
    # 關聯
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
        """建立預設設定"""
        return cls(user_id=user_id)
