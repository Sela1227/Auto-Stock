"""
Pydantic Schemas
API è«‹æ±‚/å›žæ‡‰è³‡æ–™æ¨¡åž‹
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


# ==================== é€šç”¨ ====================

class ResponseBase(BaseModel):
    """åŸºç¤Žå›žæ‡‰"""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """éŒ¯èª¤å›žæ‡‰"""
    success: bool = False
    error: Dict[str, str]


# ==================== ç”¨æˆ¶ ====================

class UserBase(BaseModel):
    """ç”¨æˆ¶åŸºæœ¬è³‡è¨Š"""
    display_name: Optional[str] = None
    picture_url: Optional[str] = None
    email: Optional[str] = None


class UserResponse(UserBase):
    """ç”¨æˆ¶å›žæ‡‰"""
    id: int
    line_user_id: str
    is_active: bool
    is_admin: bool = False  # ç®¡ç†å“¡æ¬Šé™
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LoginResponse(ResponseBase):
    """ç™»å…¥å›žæ‡‰"""
    token: str
    user: UserResponse
    is_new_user: bool = False


# ==================== è¿½è¹¤æ¸…å–® ====================

class WatchlistAdd(BaseModel):
    """æ–°å¢žè¿½è¹¤æ¸…å–®è«‹æ±‚"""
    symbol: str = Field(..., min_length=1, max_length=10)
    note: Optional[str] = Field(None, max_length=200)


class WatchlistUpdate(BaseModel):
    """æ›´æ–°è¿½è¹¤æ¸…å–®è«‹æ±‚"""
    note: Optional[str] = Field(None, max_length=200)


class WatchlistItem(BaseModel):
    """è¿½è¹¤æ¸…å–®é …ç›®"""
    id: int
    symbol: str
    asset_type: str
    note: Optional[str] = None
    added_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WatchlistResponse(ResponseBase):
    """è¿½è¹¤æ¸…å–®å›žæ‡‰"""
    data: Optional[WatchlistItem] = None


class WatchlistListResponse(ResponseBase):
    """è¿½è¹¤æ¸…å–®åˆ—è¡¨å›žæ‡‰"""
    data: List[WatchlistItem] = []
    total: int = 0


class WatchlistOverviewItem(BaseModel):
    """è¿½è¹¤æ¸…å–®ç¸½è¦½é …ç›®"""
    id: int
    symbol: str
    name: Optional[str] = None
    price: Optional[float] = None
    change_day: Optional[float] = None
    change_24h: Optional[float] = None
    ma_alignment: Optional[str] = None
    rsi: Optional[float] = None
    score: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    added_at: Optional[str] = None


class SentimentItem(BaseModel):
    """æƒ…ç·’æŒ‡æ•¸é …ç›®"""
    value: int
    classification: str
    classification_zh: str
    timestamp: str
    market: str


class WatchlistOverviewResponse(ResponseBase):
    """è¿½è¹¤æ¸…å–®ç¸½è¦½å›žæ‡‰"""
    stocks: List[WatchlistOverviewItem] = []
    crypto: List[WatchlistOverviewItem] = []
    sentiment: Optional[Dict[str, SentimentItem]] = None
    total_count: int = 0


# ==================== è¨­å®š ====================

class IndicatorSettingsUpdate(BaseModel):
    """æŒ‡æ¨™é¡¯ç¤ºè¨­å®šæ›´æ–°"""
    show_ma: Optional[bool] = None
    show_rsi: Optional[bool] = None
    show_macd: Optional[bool] = None
    show_kd: Optional[bool] = None
    show_bollinger: Optional[bool] = None
    show_obv: Optional[bool] = None
    show_volume: Optional[bool] = None


class IndicatorSettingsResponse(ResponseBase):
    """æŒ‡æ¨™é¡¯ç¤ºè¨­å®šå›žæ‡‰"""
    data: Dict[str, bool] = {}


class AlertSettingsUpdate(BaseModel):
    """é€šçŸ¥è¨­å®šæ›´æ–°"""
    alert_ma_cross: Optional[bool] = None
    alert_ma_breakout: Optional[bool] = None
    alert_rsi: Optional[bool] = None
    alert_macd: Optional[bool] = None
    alert_kd: Optional[bool] = None
    alert_bollinger: Optional[bool] = None
    alert_volume: Optional[bool] = None
    alert_sentiment: Optional[bool] = None


class AlertSettingsResponse(ResponseBase):
    """é€šçŸ¥è¨­å®šå›žæ‡‰"""
    data: Dict[str, bool] = {}


class IndicatorParamsUpdate(BaseModel):
    """æŒ‡æ¨™åƒæ•¸æ›´æ–°"""
    ma_short: Optional[int] = Field(None, ge=5, le=50)
    ma_mid: Optional[int] = Field(None, ge=20, le=100)
    ma_long: Optional[int] = Field(None, ge=50, le=300)
    rsi_period: Optional[int] = Field(None, ge=5, le=30)
    rsi_overbought: Optional[int] = Field(None, ge=60, le=90)
    rsi_oversold: Optional[int] = Field(None, ge=10, le=40)
    macd_fast: Optional[int] = Field(None, ge=5, le=20)
    macd_slow: Optional[int] = Field(None, ge=15, le=40)
    macd_signal: Optional[int] = Field(None, ge=5, le=15)
    kd_period: Optional[int] = Field(None, ge=5, le=20)
    bollinger_period: Optional[int] = Field(None, ge=10, le=30)
    bollinger_std: Optional[float] = Field(None, ge=1.0, le=3.0)
    breakout_threshold: Optional[float] = Field(None, ge=0.5, le=5.0)
    volume_alert_ratio: Optional[float] = Field(None, ge=1.0, le=5.0)


class IndicatorParamsResponse(ResponseBase):
    """æŒ‡æ¨™åƒæ•¸å›žæ‡‰"""
    data: Dict[str, Any] = {}


# ==================== è‚¡ç¥¨/åŠ å¯†è²¨å¹£ ====================

class PriceInfo(BaseModel):
    """åƒ¹æ ¼è³‡è¨Š"""
    current: float
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    ath: Optional[float] = None
    from_high_pct: Optional[float] = None
    from_low_pct: Optional[float] = None
    from_ath_pct: Optional[float] = None


class ChangeInfo(BaseModel):
    """æ¼²è·Œå¹…è³‡è¨Š"""
    day: Optional[float] = None
    week: Optional[float] = None
    month: Optional[float] = None
    quarter: Optional[float] = None
    year: Optional[float] = None


class VolumeInfo(BaseModel):
    """æˆäº¤é‡è³‡è¨Š"""
    today: Optional[int] = None
    avg_20d: Optional[int] = None
    ratio: Optional[float] = None


class SignalItem(BaseModel):
    """è¨Šè™Ÿé …ç›®"""
    type: str
    indicator: str
    description: str


class ScoreInfo(BaseModel):
    """è©•åˆ†è³‡è¨Š"""
    buy_score: int = 0
    sell_score: int = 0
    rating: str = "neutral"
    details: List[str] = []


class StockAnalysisResponse(ResponseBase):
    """è‚¡ç¥¨åˆ†æžå›žæ‡‰"""
    symbol: str
    name: str
    asset_type: str = "stock"
    price: PriceInfo
    change: ChangeInfo
    volume: Optional[VolumeInfo] = None
    indicators: Dict[str, Any] = {}
    signals: List[SignalItem] = []
    score: ScoreInfo
    updated_at: Optional[str] = None


class CryptoAnalysisResponse(ResponseBase):
    """åŠ å¯†è²¨å¹£åˆ†æžå›žæ‡‰"""
    symbol: str
    name: str
    asset_type: str = "crypto"
    price: PriceInfo
    change: ChangeInfo
    market: Optional[Dict[str, Any]] = None
    indicators: Dict[str, Any] = {}
    signals: List[SignalItem] = []
    score: ScoreInfo
    updated_at: Optional[str] = None


# ==================== å¸‚å ´æƒ…ç·’ ====================

class MarketSentimentResponse(ResponseBase):
    """å¸‚å ´æƒ…ç·’å›žæ‡‰"""
    stock: Optional[SentimentItem] = None
    crypto: Optional[SentimentItem] = None