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
    
    # 訊號 Emoji
    SIGNAL_EMOJI = {
        SignalType.MA_GOLDEN_CROSS: "🟢",
        SignalType.MA_DEATH_CROSS: "🔴",
        SignalType.APPROACHING_BREAKOUT: "⬆️",
        SignalType.APPROACHING_BREAKDOWN: "⬇️",
        SignalType.BREAKOUT: "✅",
        SignalType.BREAKDOWN: "❌",
        SignalType.RSI_OVERBOUGHT: "⚠️",
        SignalType.RSI_OVERSOLD: "🟢",
        SignalType.MACD_GOLDEN_CROSS: "🟢",
        SignalType.MACD_DEATH_CROSS: "🔴",
        SignalType.KD_GOLDEN_CROSS: "🟢",
        SignalType.KD_DEATH_CROSS: "🔴",
        SignalType.BOLLINGER_BREAKOUT: "📈",
        SignalType.BOLLINGER_BREAKDOWN: "📉",
        SignalType.VOLUME_SURGE: "📊",
        SignalType.SENTIMENT_EXTREME_FEAR: "😱",
        SignalType.SENTIMENT_EXTREME_GREED: "🤑",
    }
    
    def __init__(self):
        # 預設參數（可被用戶設定覆蓋）
        self.default_params = {
            "ma_short": 20,
            "ma_mid": 50,
            "ma_long": 200,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "kd_period": 9,
            "bollinger_period": 20,
            "bollinger_std": 2.0,
            "breakout_threshold": 2.0,  # 接近突破門檻 (%)
            "volume_alert_ratio": 2.0,  # 量比警戒倍數
        }
    
    def detect_signals(
        self, 
        symbol: str, 
        indicators: Dict[str, Any],
        asset_type: str = "stock",
        params: Optional[Dict] = None
    ) -> List[Signal]:
        """
        偵測股票/加密貨幣的技術指標訊號
        
        Args:
            symbol: 股票/幣種代號
            indicators: 技術指標資料（來自 indicator_service）
            asset_type: stock / crypto
            params: 用戶自訂參數（可選）
            
        Returns:
            偵測到的訊號列表
        """
        signals = []
        p = {**self.default_params, **(params or {})}
        
        current_price = indicators.get("current_price", 0)
        if not current_price:
            logger.warning(f"{symbol} 無法取得現價")
            return signals
        
        now = datetime.now()
        
        # 1. 均線訊號
        ma_signals = self._detect_ma_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(ma_signals)
        
        # 2. RSI 訊號
        rsi_signals = self._detect_rsi_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(rsi_signals)
        
        # 3. MACD 訊號
        macd_signals = self._detect_macd_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(macd_signals)
        
        # 4. KD 訊號
        kd_signals = self._detect_kd_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(kd_signals)
        
        # 5. 布林通道訊號
        bb_signals = self._detect_bollinger_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(bb_signals)
        
        # 6. 成交量訊號
        vol_signals = self._detect_volume_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(vol_signals)
        
        logger.info(f"{symbol} 偵測到 {len(signals)} 個訊號")
        return signals
    
    def _detect_ma_signals(
        self, symbol: str, indicators: Dict, price: float, 
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """偵測均線訊號"""
        signals = []
        ma = indicators.get("ma", {})
        
        if not ma:
            return signals
        
        ma20 = ma.get("ma20")
        ma50 = ma.get("ma50")
        ma200 = ma.get("ma200")
        
        # 均線交叉（需要有前一日資料才能判斷，這裡簡化為檢查當前狀態）
        # 實際上需要比較昨日和今日的 MA 值
        
        # 接近突破/跌破檢測
        threshold_pct = params["breakout_threshold"] / 100
        
        for ma_name, ma_value in [("MA20", ma20), ("MA50", ma50), ("MA200", ma200)]:
            if ma_value is None or ma_value <= 0:
                continue
            
            diff_pct = (price - ma_value) / ma_value
            
            # 接近向上突破（價格在均線下方，差距小於門檻）
            if -threshold_pct < diff_pct < 0:
                signals.append(Signal(
                    symbol=symbol,
                    asset_type=asset_type,
                    signal_type=SignalType.APPROACHING_BREAKOUT,
                    indicator=ma_name,
                    message=f"{symbol} 接近突破 {ma_name} ({ma_value:.2f})，差距 {abs(diff_pct)*100:.1f}%",
                    price=price,
                    details={"ma_name": ma_name, "ma_value": ma_value, "diff_pct": diff_pct},
                    timestamp=now,
                ))
            
            # 接近向下跌破（價格在均線上方，差距小於門檻）
            elif 0 < diff_pct < threshold_pct:
                signals.append(Signal(
                    symbol=symbol,
                    asset_type=asset_type,
                    signal_type=SignalType.APPROACHING_BREAKDOWN,
                    indicator=ma_name,
                    message=f"{symbol} 接近跌破 {ma_name} ({ma_value:.2f})，差距 {diff_pct*100:.1f}%",
                    price=price,
                    details={"ma_name": ma_name, "ma_value": ma_value, "diff_pct": diff_pct},
                    timestamp=now,
                ))
        
        # 黃金交叉/死亡交叉（MA20 vs MA50）
        if ma20 and ma50:
            cross_info = ma.get("cross_info", {})
            if cross_info.get("type") == "golden_cross" and cross_info.get("days_ago", 999) <= 3:
                signals.append(Signal(
                    symbol=symbol,
                    asset_type=asset_type,
                    signal_type=SignalType.MA_GOLDEN_CROSS,
                    indicator="MA20/MA50",
                    message=f"{symbol} MA20 黃金交叉 MA50",
                    price=price,
                    details={"ma20": ma20, "ma50": ma50},
                    timestamp=now,
                ))
            elif cross_info.get("type") == "death_cross" and cross_info.get("days_ago", 999) <= 3:
                signals.append(Signal(
                    symbol=symbol,
                    asset_type=asset_type,
                    signal_type=SignalType.MA_DEATH_CROSS,
                    indicator="MA20/MA50",
                    message=f"{symbol} MA20 死亡交叉 MA50",
                    price=price,
                    details={"ma20": ma20, "ma50": ma50},
                    timestamp=now,
                ))
        
        return signals
    
    def _detect_rsi_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """偵測 RSI 訊號"""
        signals = []
        rsi_data = indicators.get("rsi", {})
        
        if not rsi_data:
            return signals
        
        rsi_value = rsi_data.get("value")
        if rsi_value is None:
            return signals
        
        overbought = params["rsi_overbought"]
        oversold = params["rsi_oversold"]
        
        if rsi_value >= overbought:
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.RSI_OVERBOUGHT,
                indicator="RSI",
                message=f"{symbol} RSI 達 {rsi_value:.1f}，進入超買區",
                price=price,
                details={"rsi": rsi_value, "threshold": overbought},
                timestamp=now,
            ))
        elif rsi_value <= oversold:
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.RSI_OVERSOLD,
                indicator="RSI",
                message=f"{symbol} RSI 跌至 {rsi_value:.1f}，進入超賣區",
                price=price,
                details={"rsi": rsi_value, "threshold": oversold},
                timestamp=now,
            ))
        
        return signals
    
    def _detect_macd_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """偵測 MACD 訊號"""
        signals = []
        macd_data = indicators.get("macd", {})
        
        if not macd_data:
            return signals
        
        dif = macd_data.get("dif")
        macd = macd_data.get("macd")
        histogram = macd_data.get("histogram")
        status = macd_data.get("status", "")
        
        # 根據 status 判斷（indicator_service 已經計算好）
        if "golden_cross" in status.lower() or status == "bullish_cross":
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.MACD_GOLDEN_CROSS,
                indicator="MACD",
                message=f"{symbol} MACD 黃金交叉",
                price=price,
                details={"dif": dif, "macd": macd, "histogram": histogram},
                timestamp=now,
            ))
        elif "death_cross" in status.lower() or status == "bearish_cross":
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.MACD_DEATH_CROSS,
                indicator="MACD",
                message=f"{symbol} MACD 死亡交叉",
                price=price,
                details={"dif": dif, "macd": macd, "histogram": histogram},
                timestamp=now,
            ))
        
        return signals
    
    def _detect_kd_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """偵測 KD 訊號"""
        signals = []
        kd_data = indicators.get("kd", {})
        
        if not kd_data:
            return signals
        
        k = kd_data.get("k")
        d = kd_data.get("d")
        status = kd_data.get("status", "")
        
        # KD 交叉
        if "golden" in status.lower():
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.KD_GOLDEN_CROSS,
                indicator="KD",
                message=f"{symbol} KD 黃金交叉 (K={k:.1f}, D={d:.1f})",
                price=price,
                details={"k": k, "d": d},
                timestamp=now,
            ))
        elif "death" in status.lower():
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.KD_DEATH_CROSS,
                indicator="KD",
                message=f"{symbol} KD 死亡交叉 (K={k:.1f}, D={d:.1f})",
                price=price,
                details={"k": k, "d": d},
                timestamp=now,
            ))
        
        return signals
    
    def _detect_bollinger_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """偵測布林通道訊號"""
        signals = []
        bb_data = indicators.get("bollinger", {})
        
        if not bb_data:
            return signals
        
        upper = bb_data.get("upper")
        lower = bb_data.get("lower")
        position = bb_data.get("position", "")
        
        if upper and price >= upper:
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.BOLLINGER_BREAKOUT,
                indicator="Bollinger",
                message=f"{symbol} 突破布林上軌 ({upper:.2f})",
                price=price,
                details={"upper": upper, "lower": lower, "price": price},
                timestamp=now,
            ))
        elif lower and price <= lower:
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.BOLLINGER_BREAKDOWN,
                indicator="Bollinger",
                message=f"{symbol} 跌破布林下軌 ({lower:.2f})",
                price=price,
                details={"upper": upper, "lower": lower, "price": price},
                timestamp=now,
            ))
        
        return signals
    
    def _detect_volume_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """偵測成交量訊號"""
        signals = []
        vol_data = indicators.get("volume", {})
        
        if not vol_data:
            return signals
        
        ratio = vol_data.get("ratio")
        alert_ratio = params["volume_alert_ratio"]
        
        if ratio and ratio >= alert_ratio:
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.VOLUME_SURGE,
                indicator="Volume",
                message=f"{symbol} 成交量暴增 (量比 {ratio:.1f})",
                price=price,
                details={"ratio": ratio, "threshold": alert_ratio},
                timestamp=now,
            ))
        
        return signals
    
    def detect_sentiment_signals(
        self, sentiment_data: Dict[str, Any]
    ) -> List[Signal]:
        """
        偵測市場情緒訊號
        
        Args:
            sentiment_data: 情緒資料 {"stock": {...}, "crypto": {...}}
            
        Returns:
            偵測到的訊號列表
        """
        signals = []
        now = datetime.now()
        
        for market, data in sentiment_data.items():
            if not data:
                continue
            
            value = data.get("value")
            if value is None:
                continue
            
            asset_type = "stock" if market == "stock" else "crypto"
            market_name = "美股" if market == "stock" else "幣圈"
            
            if value <= 20:
                signals.append(Signal(
                    symbol=market_name,
                    asset_type=asset_type,
                    signal_type=SignalType.SENTIMENT_EXTREME_FEAR,
                    indicator="Fear & Greed",
                    message=f"{market_name}極度恐懼 ({value})，留意買入機會",
                    price=0,
                    details={"value": value, "classification": data.get("classification")},
                    timestamp=now,
                ))
            elif value >= 80:
                signals.append(Signal(
                    symbol=market_name,
                    asset_type=asset_type,
                    signal_type=SignalType.SENTIMENT_EXTREME_GREED,
                    indicator="Fear & Greed",
                    message=f"{market_name}極度貪婪 ({value})，留意風險",
                    price=0,
                    details={"value": value, "classification": data.get("classification")},
                    timestamp=now,
                ))
        
        return signals
    
    def format_signal_message(self, signal: Signal) -> str:
        """格式化訊號訊息（用於 LINE 推播）"""
        emoji = self.SIGNAL_EMOJI.get(signal.signal_type, "📢")
        return f"{emoji} {signal.message}"
    
    def format_signals_summary(self, signals: List[Signal]) -> str:
        """
        格式化多個訊號為摘要訊息
        
        Args:
            signals: 訊號列表
            
        Returns:
            格式化的訊息文字
        """
        if not signals:
            return ""
        
        # 按股票分組
        by_symbol = {}
        for s in signals:
            if s.symbol not in by_symbol:
                by_symbol[s.symbol] = []
            by_symbol[s.symbol].append(s)
        
        lines = ["📊 技術訊號通知", ""]
        
        for symbol, symbol_signals in by_symbol.items():
            lines.append(f"【{symbol}】")
            for s in symbol_signals:
                emoji = self.SIGNAL_EMOJI.get(s.signal_type, "•")
                name = self.SIGNAL_NAMES.get(s.signal_type, str(s.signal_type))
                if s.price > 0:
                    lines.append(f"  {emoji} {name} @ ${s.price:.2f}")
                else:
                    lines.append(f"  {emoji} {s.message}")
            lines.append("")
        
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(lines)


# 單例
signal_service = SignalService()
