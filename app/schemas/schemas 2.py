"""
Pydantic Schemas
API 請求/回應資料模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


# ==================== 通用 ====================

class ResponseBase(BaseModel):
    """基礎回應"""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """錯誤回應"""
    success: bool = False
    error: Dict[str, str]


# ==================== 用戶 ====================

class UserBase(BaseModel):
    """用戶基本資訊"""
    display_name: Optional[str] = None
    picture_url: Optional[str] = None
    email: Optional[str] = None


class UserResponse(UserBase):
    """用戶回應"""
    id: int
    line_user_id: str
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LoginResponse(ResponseBase):
    """登入回應"""
    token: str
    user: UserResponse
    is_new_user: bool = False


# ==================== 追蹤清單 ====================

class WatchlistAdd(BaseModel):
    """新增追蹤清單請求"""
    symbol: str = Field(..., min_length=1, max_length=10)
    note: Optional[str] = Field(None, max_length=200)


class WatchlistUpdate(BaseModel):
    """更新追蹤清單請求"""
    note: Optional[str] = Field(None, max_length=200)


class WatchlistItem(BaseModel):
    """追蹤清單項目"""
    id: int
    symbol: str
    asset_type: str
    note: Optional[str] = None
    added_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WatchlistResponse(ResponseBase):
    """追蹤清單回應"""
    data: Optional[WatchlistItem] = None


class WatchlistListResponse(ResponseBase):
    """追蹤清單列表回應"""
    data: List[WatchlistItem] = []
    total: int = 0


class WatchlistOverviewItem(BaseModel):
    """追蹤清單總覽項目"""
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
    """情緒指數項目"""
    value: int
    classification: str
    classification_zh: str
    timestamp: str
    market: str


class WatchlistOverviewResponse(ResponseBase):
    """追蹤清單總覽回應"""
    stocks: List[WatchlistOverviewItem] = []
    crypto: List[WatchlistOverviewItem] = []
    sentiment: Optional[Dict[str, SentimentItem]] = None
    total_count: int = 0


# ==================== 設定 ====================

class IndicatorSettingsUpdate(BaseModel):
    """指標顯示設定更新"""
    show_ma: Optional[bool] = None
    show_rsi: Optional[bool] = None
    show_macd: Optional[bool] = None
    show_kd: Optional[bool] = None
    show_bollinger: Optional[bool] = None
    show_obv: Optional[bool] = None
    show_volume: Optional[bool] = None


class IndicatorSettingsResponse(ResponseBase):
    """指標顯示設定回應"""
    data: Dict[str, bool] = {}


class AlertSettingsUpdate(BaseModel):
    """通知設定更新"""
    alert_ma_cross: Optional[bool] = None
    alert_ma_breakout: Optional[bool] = None
    alert_rsi: Optional[bool] = None
    alert_macd: Optional[bool] = None
    alert_kd: Optional[bool] = None
    alert_bollinger: Optional[bool] = None
    alert_volume: Optional[bool] = None
    alert_sentiment: Optional[bool] = None


class AlertSettingsResponse(ResponseBase):
    """通知設定回應"""
    data: Dict[str, bool] = {}


class IndicatorParamsUpdate(BaseModel):
    """指標參數更新"""
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
    """指標參數回應"""
    data: Dict[str, Any] = {}


# ==================== 股票/加密貨幣 ====================

class PriceInfo(BaseModel):
    """價格資訊"""
    current: float
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    ath: Optional[float] = None
    from_high_pct: Optional[float] = None
    from_low_pct: Optional[float] = None
    from_ath_pct: Optional[float] = None


class ChangeInfo(BaseModel):
    """漲跌幅資訊"""
    day: Optional[float] = None
    week: Optional[float] = None
    month: Optional[float] = None
    quarter: Optional[float] = None
    year: Optional[float] = None


class VolumeInfo(BaseModel):
    """成交量資訊"""
    today: Optional[int] = None
    avg_20d: Optional[int] = None
    ratio: Optional[float] = None


class SignalItem(BaseModel):
    """訊號項目"""
    type: str
    indicator: str
    description: str


class ScoreInfo(BaseModel):
    """評分資訊"""
    buy_score: int = 0
    sell_score: int = 0
    rating: str = "neutral"
    details: List[str] = []


class StockAnalysisResponse(ResponseBase):
    """股票分析回應"""
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
    """加密貨幣分析回應"""
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


# ==================== 市場情緒 ====================

class MarketSentimentResponse(ResponseBase):
    """市場情緒回應"""
    stock: Optional[SentimentItem] = None
    crypto: Optional[SentimentItem] = None
