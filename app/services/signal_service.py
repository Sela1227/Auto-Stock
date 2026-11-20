"""
訊號偵測服務
偵測技術指標訊號（黃金交叉、死亡交叉、超買超賣等）
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """訊號類型"""
    # 均線
    MA_GOLDEN_CROSS = "ma_golden_cross"
    MA_DEATH_CROSS = "ma_death_cross"
    APPROACHING_BREAKOUT = "approaching_breakout"
    APPROACHING_BREAKDOWN = "approaching_breakdown"
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    
    # RSI
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    
    # MACD
    MACD_GOLDEN_CROSS = "macd_golden_cross"
    MACD_DEATH_CROSS = "macd_death_cross"
    
    # KD
    KD_GOLDEN_CROSS = "kd_golden_cross"
    KD_DEATH_CROSS = "kd_death_cross"
    
    # 布林通道
    BOLLINGER_BREAKOUT = "bollinger_breakout"
    BOLLINGER_BREAKDOWN = "bollinger_breakdown"
    
    # 成交量
    VOLUME_SURGE = "volume_surge"
    
    # 市場情緒
    SENTIMENT_EXTREME_FEAR = "sentiment_extreme_fear"
    SENTIMENT_EXTREME_GREED = "sentiment_extreme_greed"


@dataclass
class Signal:
    """訊號資料"""
    symbol: str
    asset_type: str  # stock / crypto
    signal_type: SignalType
    indicator: str
    message: str
    price: float
    details: Dict[str, Any]
    timestamp: datetime


class SignalService:
    """訊號偵測服務"""
    
    # 訊號類型中文對照
    SIGNAL_NAMES = {
        SignalType.MA_GOLDEN_CROSS: "均線黃金交叉",
        SignalType.MA_DEATH_CROSS: "均線死亡交叉",
        SignalType.APPROACHING_BREAKOUT: "接近向上突破",
        SignalType.APPROACHING_BREAKDOWN: "接近向下跌破",
        SignalType.BREAKOUT: "向上突破",
        SignalType.BREAKDOWN: "向下跌破",
        SignalType.RSI_OVERBOUGHT: "RSI 超買",
        SignalType.RSI_OVERSOLD: "RSI 超賣",
        SignalType.MACD_GOLDEN_CROSS: "MACD 黃金交叉",
        SignalType.MACD_DEATH_CROSS: "MACD 死亡交叉",
        SignalType.KD_GOLDEN_CROSS: "KD 黃金交叉",
        SignalType.KD_DEATH_CROSS: "KD 死亡交叉",
        SignalType.BOLLINGER_BREAKOUT: "突破布林上軌",
        SignalType.BOLLINGER_BREAKDOWN: "跌破布林下軌",
        SignalType.VOLUME_SURGE: "成交量暴增",
        SignalType.SENTIMENT_EXTREME_FEAR: "極度恐懼",
        SignalType.SENTIMENT_EXTREME_GREED: "極度貪婪",
    }
    
    
    
    
# 單例
signal_service = SignalService()
