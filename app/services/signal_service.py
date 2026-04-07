"""
è¨Šè™Ÿåµæ¸¬æœå‹™
åµæ¸¬æŠ€è¡“æŒ‡æ¨™è¨Šè™Ÿï¼ˆé»ƒé‡‘äº¤å‰ã€æ­»äº¡äº¤å‰ã€è¶…è²·è¶…è³£ç­‰ï¼‰
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """è¨Šè™Ÿé¡žåž‹"""
    # å‡ç·š
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
    
    # å¸ƒæž—é€šé“
    BOLLINGER_BREAKOUT = "bollinger_breakout"
    BOLLINGER_BREAKDOWN = "bollinger_breakdown"
    
    # æˆäº¤é‡
    VOLUME_SURGE = "volume_surge"
    
    # å¸‚å ´æƒ…ç·’
    SENTIMENT_EXTREME_FEAR = "sentiment_extreme_fear"
    SENTIMENT_EXTREME_GREED = "sentiment_extreme_greed"


@dataclass
class Signal:
    """è¨Šè™Ÿè³‡æ–™"""
    symbol: str
    asset_type: str  # stock / crypto
    signal_type: SignalType
    indicator: str
    message: str
    price: float
    details: Dict[str, Any]
    timestamp: datetime


class SignalService:
    """è¨Šè™Ÿåµæ¸¬æœå‹™"""
    
    # è¨Šè™Ÿé¡žåž‹ä¸­æ–‡å°ç…§
    SIGNAL_NAMES = {
        SignalType.MA_GOLDEN_CROSS: "å‡ç·šé»ƒé‡‘äº¤å‰",
        SignalType.MA_DEATH_CROSS: "å‡ç·šæ­»äº¡äº¤å‰",
        SignalType.APPROACHING_BREAKOUT: "æŽ¥è¿‘å‘ä¸Šçªç ´",
        SignalType.APPROACHING_BREAKDOWN: "æŽ¥è¿‘å‘ä¸‹è·Œç ´",
        SignalType.BREAKOUT: "å‘ä¸Šçªç ´",
        SignalType.BREAKDOWN: "å‘ä¸‹è·Œç ´",
        SignalType.RSI_OVERBOUGHT: "RSI è¶…è²·",
        SignalType.RSI_OVERSOLD: "RSI è¶…è³£",
        SignalType.MACD_GOLDEN_CROSS: "MACD é»ƒé‡‘äº¤å‰",
        SignalType.MACD_DEATH_CROSS: "MACD æ­»äº¡äº¤å‰",
        SignalType.KD_GOLDEN_CROSS: "KD é»ƒé‡‘äº¤å‰",
        SignalType.KD_DEATH_CROSS: "KD æ­»äº¡äº¤å‰",
        SignalType.BOLLINGER_BREAKOUT: "çªç ´å¸ƒæž—ä¸Šè»Œ",
        SignalType.BOLLINGER_BREAKDOWN: "è·Œç ´å¸ƒæž—ä¸‹è»Œ",
        SignalType.VOLUME_SURGE: "æˆäº¤é‡æš´å¢ž",
        SignalType.SENTIMENT_EXTREME_FEAR: "æ¥µåº¦ææ‡¼",
        SignalType.SENTIMENT_EXTREME_GREED: "æ¥µåº¦è²ªå©ª",
    }
    
    # è¨Šè™Ÿ Emoji
    SIGNAL_EMOJI = {
        SignalType.MA_GOLDEN_CROSS: "ðŸŸ¢",
        SignalType.MA_DEATH_CROSS: "ðŸ”´",
        SignalType.APPROACHING_BREAKOUT: "â¬†ï¸",
        SignalType.APPROACHING_BREAKDOWN: "â¬‡ï¸",
        SignalType.BREAKOUT: "âœ…",
        SignalType.BREAKDOWN: "âŒ",
        SignalType.RSI_OVERBOUGHT: "âš ï¸",
        SignalType.RSI_OVERSOLD: "ðŸŸ¢",
        SignalType.MACD_GOLDEN_CROSS: "ðŸŸ¢",
        SignalType.MACD_DEATH_CROSS: "ðŸ”´",
        SignalType.KD_GOLDEN_CROSS: "ðŸŸ¢",
        SignalType.KD_DEATH_CROSS: "ðŸ”´",
        SignalType.BOLLINGER_BREAKOUT: "ðŸ“ˆ",
        SignalType.BOLLINGER_BREAKDOWN: "ðŸ“‰",
        SignalType.VOLUME_SURGE: "ðŸ“Š",
        SignalType.SENTIMENT_EXTREME_FEAR: "ðŸ˜±",
        SignalType.SENTIMENT_EXTREME_GREED: "ðŸ¤‘",
    }
    
    def __init__(self):
        # é è¨­åƒæ•¸ï¼ˆå¯è¢«ç”¨æˆ¶è¨­å®šè¦†è“‹ï¼‰
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
            "breakout_threshold": 2.0,  # æŽ¥è¿‘çªç ´é–€æª» (%)
            "volume_alert_ratio": 2.0,  # é‡æ¯”è­¦æˆ’å€æ•¸
        }
    
    def detect_signals(
        self, 
        symbol: str, 
        indicators: Dict[str, Any],
        asset_type: str = "stock",
        params: Optional[Dict] = None
    ) -> List[Signal]:
        """
        åµæ¸¬è‚¡ç¥¨/åŠ å¯†è²¨å¹£çš„æŠ€è¡“æŒ‡æ¨™è¨Šè™Ÿ
        
        Args:
            symbol: è‚¡ç¥¨/å¹£ç¨®ä»£è™Ÿ
            indicators: æŠ€è¡“æŒ‡æ¨™è³‡æ–™ï¼ˆä¾†è‡ª indicator_serviceï¼‰
            asset_type: stock / crypto
            params: ç”¨æˆ¶è‡ªè¨‚åƒæ•¸ï¼ˆå¯é¸ï¼‰
            
        Returns:
            åµæ¸¬åˆ°çš„è¨Šè™Ÿåˆ—è¡¨
        """
        signals = []
        p = {**self.default_params, **(params or {})}
        
        current_price = indicators.get("current_price", 0)
        if not current_price:
            logger.warning(f"{symbol} ç„¡æ³•å–å¾—ç¾åƒ¹")
            return signals
        
        now = datetime.now()
        
        # 1. å‡ç·šè¨Šè™Ÿ
        ma_signals = self._detect_ma_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(ma_signals)
        
        # 2. RSI è¨Šè™Ÿ
        rsi_signals = self._detect_rsi_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(rsi_signals)
        
        # 3. MACD è¨Šè™Ÿ
        macd_signals = self._detect_macd_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(macd_signals)
        
        # 4. KD è¨Šè™Ÿ
        kd_signals = self._detect_kd_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(kd_signals)
        
        # 5. å¸ƒæž—é€šé“è¨Šè™Ÿ
        bb_signals = self._detect_bollinger_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(bb_signals)
        
        # 6. æˆäº¤é‡è¨Šè™Ÿ
        vol_signals = self._detect_volume_signals(symbol, indicators, current_price, p, now, asset_type)
        signals.extend(vol_signals)
        
        logger.info(f"{symbol} åµæ¸¬åˆ° {len(signals)} å€‹è¨Šè™Ÿ")
        return signals
    
    def _detect_ma_signals(
        self, symbol: str, indicators: Dict, price: float, 
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """åµæ¸¬å‡ç·šè¨Šè™Ÿ"""
        signals = []
        ma = indicators.get("ma", {})
        
        if not ma:
            return signals
        
        ma20 = ma.get("ma20")
        ma50 = ma.get("ma50")
        ma200 = ma.get("ma200")
        
        # å‡ç·šäº¤å‰ï¼ˆéœ€è¦æœ‰å‰ä¸€æ—¥è³‡æ–™æ‰èƒ½åˆ¤æ–·ï¼Œé€™è£¡ç°¡åŒ–ç‚ºæª¢æŸ¥ç•¶å‰ç‹€æ…‹ï¼‰
        # å¯¦éš›ä¸Šéœ€è¦æ¯”è¼ƒæ˜¨æ—¥å’Œä»Šæ—¥çš„ MA å€¼
        
        # æŽ¥è¿‘çªç ´/è·Œç ´æª¢æ¸¬
        threshold_pct = params["breakout_threshold"] / 100
        
        for ma_name, ma_value in [("MA20", ma20), ("MA50", ma50), ("MA200", ma200)]:
            if ma_value is None or ma_value <= 0:
                continue
            
            diff_pct = (price - ma_value) / ma_value
            
            # æŽ¥è¿‘å‘ä¸Šçªç ´ï¼ˆåƒ¹æ ¼åœ¨å‡ç·šä¸‹æ–¹ï¼Œå·®è·å°æ–¼é–€æª»ï¼‰
            if -threshold_pct < diff_pct < 0:
                signals.append(Signal(
                    symbol=symbol,
                    asset_type=asset_type,
                    signal_type=SignalType.APPROACHING_BREAKOUT,
                    indicator=ma_name,
                    message=f"{symbol} æŽ¥è¿‘çªç ´ {ma_name} ({ma_value:.2f})ï¼Œå·®è· {abs(diff_pct)*100:.1f}%",
                    price=price,
                    details={"ma_name": ma_name, "ma_value": ma_value, "diff_pct": diff_pct},
                    timestamp=now,
                ))
            
            # æŽ¥è¿‘å‘ä¸‹è·Œç ´ï¼ˆåƒ¹æ ¼åœ¨å‡ç·šä¸Šæ–¹ï¼Œå·®è·å°æ–¼é–€æª»ï¼‰
            elif 0 < diff_pct < threshold_pct:
                signals.append(Signal(
                    symbol=symbol,
                    asset_type=asset_type,
                    signal_type=SignalType.APPROACHING_BREAKDOWN,
                    indicator=ma_name,
                    message=f"{symbol} æŽ¥è¿‘è·Œç ´ {ma_name} ({ma_value:.2f})ï¼Œå·®è· {diff_pct*100:.1f}%",
                    price=price,
                    details={"ma_name": ma_name, "ma_value": ma_value, "diff_pct": diff_pct},
                    timestamp=now,
                ))
        
        # é»ƒé‡‘äº¤å‰/æ­»äº¡äº¤å‰ï¼ˆMA20 vs MA50ï¼‰
        if ma20 and ma50:
            cross_info = ma.get("cross_info", {})
            if cross_info.get("type") == "golden_cross" and cross_info.get("days_ago", 999) <= 3:
                signals.append(Signal(
                    symbol=symbol,
                    asset_type=asset_type,
                    signal_type=SignalType.MA_GOLDEN_CROSS,
                    indicator="MA20/MA50",
                    message=f"{symbol} MA20 é»ƒé‡‘äº¤å‰ MA50",
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
                    message=f"{symbol} MA20 æ­»äº¡äº¤å‰ MA50",
                    price=price,
                    details={"ma20": ma20, "ma50": ma50},
                    timestamp=now,
                ))
        
        return signals
    
    def _detect_rsi_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """åµæ¸¬ RSI è¨Šè™Ÿ"""
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
                message=f"{symbol} RSI é” {rsi_value:.1f}ï¼Œé€²å…¥è¶…è²·å€",
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
                message=f"{symbol} RSI è·Œè‡³ {rsi_value:.1f}ï¼Œé€²å…¥è¶…è³£å€",
                price=price,
                details={"rsi": rsi_value, "threshold": oversold},
                timestamp=now,
            ))
        
        return signals
    
    def _detect_macd_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """åµæ¸¬ MACD è¨Šè™Ÿ"""
        signals = []
        macd_data = indicators.get("macd", {})
        
        if not macd_data:
            return signals
        
        dif = macd_data.get("dif")
        macd = macd_data.get("macd")
        histogram = macd_data.get("histogram")
        status = macd_data.get("status", "")
        
        # æ ¹æ“š status åˆ¤æ–·ï¼ˆindicator_service å·²ç¶“è¨ˆç®—å¥½ï¼‰
        if "golden_cross" in status.lower() or status == "bullish_cross":
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.MACD_GOLDEN_CROSS,
                indicator="MACD",
                message=f"{symbol} MACD é»ƒé‡‘äº¤å‰",
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
                message=f"{symbol} MACD æ­»äº¡äº¤å‰",
                price=price,
                details={"dif": dif, "macd": macd, "histogram": histogram},
                timestamp=now,
            ))
        
        return signals
    
    def _detect_kd_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """åµæ¸¬ KD è¨Šè™Ÿ"""
        signals = []
        kd_data = indicators.get("kd", {})
        
        if not kd_data:
            return signals
        
        k = kd_data.get("k")
        d = kd_data.get("d")
        status = kd_data.get("status", "")
        
        # KD äº¤å‰
        if "golden" in status.lower():
            signals.append(Signal(
                symbol=symbol,
                asset_type=asset_type,
                signal_type=SignalType.KD_GOLDEN_CROSS,
                indicator="KD",
                message=f"{symbol} KD é»ƒé‡‘äº¤å‰ (K={k:.1f}, D={d:.1f})",
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
                message=f"{symbol} KD æ­»äº¡äº¤å‰ (K={k:.1f}, D={d:.1f})",
                price=price,
                details={"k": k, "d": d},
                timestamp=now,
            ))
        
        return signals
    
    def _detect_bollinger_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """åµæ¸¬å¸ƒæž—é€šé“è¨Šè™Ÿ"""
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
                message=f"{symbol} çªç ´å¸ƒæž—ä¸Šè»Œ ({upper:.2f})",
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
                message=f"{symbol} è·Œç ´å¸ƒæž—ä¸‹è»Œ ({lower:.2f})",
                price=price,
                details={"upper": upper, "lower": lower, "price": price},
                timestamp=now,
            ))
        
        return signals
    
    def _detect_volume_signals(
        self, symbol: str, indicators: Dict, price: float,
        params: Dict, now: datetime, asset_type: str
    ) -> List[Signal]:
        """åµæ¸¬æˆäº¤é‡è¨Šè™Ÿ"""
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
                message=f"{symbol} æˆäº¤é‡æš´å¢ž (é‡æ¯” {ratio:.1f})",
                price=price,
                details={"ratio": ratio, "threshold": alert_ratio},
                timestamp=now,
            ))
        
        return signals
    
    def detect_sentiment_signals(
        self, sentiment_data: Dict[str, Any]
    ) -> List[Signal]:
        """
        åµæ¸¬å¸‚å ´æƒ…ç·’è¨Šè™Ÿ
        
        Args:
            sentiment_data: æƒ…ç·’è³‡æ–™ {"stock": {...}, "crypto": {...}}
            
        Returns:
            åµæ¸¬åˆ°çš„è¨Šè™Ÿåˆ—è¡¨
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
            market_name = "ç¾Žè‚¡" if market == "stock" else "å¹£åœˆ"
            
            if value <= 20:
                signals.append(Signal(
                    symbol=market_name,
                    asset_type=asset_type,
                    signal_type=SignalType.SENTIMENT_EXTREME_FEAR,
                    indicator="Fear & Greed",
                    message=f"{market_name}æ¥µåº¦ææ‡¼ ({value})ï¼Œç•™æ„è²·å…¥æ©Ÿæœƒ",
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
                    message=f"{market_name}æ¥µåº¦è²ªå©ª ({value})ï¼Œç•™æ„é¢¨éšª",
                    price=0,
                    details={"value": value, "classification": data.get("classification")},
                    timestamp=now,
                ))
        
        return signals
    
    def format_signal_message(self, signal: Signal) -> str:
        """æ ¼å¼åŒ–è¨Šè™Ÿè¨Šæ¯ï¼ˆç”¨æ–¼ LINE æŽ¨æ’­ï¼‰"""
        emoji = self.SIGNAL_EMOJI.get(signal.signal_type, "ðŸ“¢")
        return f"{emoji} {signal.message}"
    
    def format_signals_summary(self, signals: List[Signal]) -> str:
        """
        æ ¼å¼åŒ–å¤šå€‹è¨Šè™Ÿç‚ºæ‘˜è¦è¨Šæ¯
        
        Args:
            signals: è¨Šè™Ÿåˆ—è¡¨
            
        Returns:
            æ ¼å¼åŒ–çš„è¨Šæ¯æ–‡å­—
        """
        if not signals:
            return ""
        
        # æŒ‰è‚¡ç¥¨åˆ†çµ„
        by_symbol = {}
        for s in signals:
            if s.symbol not in by_symbol:
                by_symbol[s.symbol] = []
            by_symbol[s.symbol].append(s)
        
        lines = ["ðŸ“Š æŠ€è¡“è¨Šè™Ÿé€šçŸ¥", ""]
        
        for symbol, symbol_signals in by_symbol.items():
            lines.append(f"ã€{symbol}ã€‘")
            for s in symbol_signals:
                emoji = self.SIGNAL_EMOJI.get(s.signal_type, "â€¢")
                name = self.SIGNAL_NAMES.get(s.signal_type, str(s.signal_type))
                if s.price > 0:
                    lines.append(f"  {emoji} {name} @ ${s.price:.2f}")
                else:
                    lines.append(f"  {emoji} {s.message}")
            lines.append("")
        
        lines.append(f"â° {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(lines)


# å–®ä¾‹
signal_service = SignalService()