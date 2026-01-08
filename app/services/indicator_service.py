"""
技術指標計算服務
包含 MA、RSI、MACD、KD、布林通道、OBV 等指標計算
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from app.config import settings


class TrendDirection(Enum):
    """趨勢方向"""
    BULLISH = "bullish"      # 多頭
    BEARISH = "bearish"      # 空頭
    NEUTRAL = "neutral"      # 中性


class SignalType(Enum):
    """訊號類型"""
    GOLDEN_CROSS = "golden_cross"      # 黃金交叉
    DEATH_CROSS = "death_cross"        # 死亡交叉
    OVERBOUGHT = "overbought"          # 超買
    OVERSOLD = "oversold"              # 超賣
    BREAKOUT = "breakout"              # 突破
    BREAKDOWN = "breakdown"            # 跌破
    APPROACHING_BREAKOUT = "approaching_breakout"  # 接近突破
    APPROACHING_BREAKDOWN = "approaching_breakdown"  # 接近跌破


@dataclass
class Signal:
    """交易訊號"""
    type: SignalType
    indicator: str
    description: str
    value: Optional[float] = None
    date: Optional[str] = None


class IndicatorService:
    """技術指標計算服務"""
    
    def __init__(
        self,
        ma_short: int = None,
        ma_mid: int = None,
        ma_long: int = None,
        rsi_period: int = None,
        rsi_overbought: int = None,
        rsi_oversold: int = None,
        macd_fast: int = None,
        macd_slow: int = None,
        macd_signal: int = None,
        kd_period: int = None,
        bollinger_period: int = None,
        bollinger_std: float = None,
        breakout_threshold: float = None,
    ):
        """
        初始化指標參數
        若未指定，則使用 config 中的預設值
        """
        self.ma_short = ma_short or settings.MA_SHORT
        self.ma_mid = ma_mid or settings.MA_MID
        self.ma_long = ma_long or settings.MA_LONG
        self.rsi_period = rsi_period or settings.RSI_PERIOD
        self.rsi_overbought = rsi_overbought or settings.RSI_OVERBOUGHT
        self.rsi_oversold = rsi_oversold or settings.RSI_OVERSOLD
        self.macd_fast = macd_fast or settings.MACD_FAST
        self.macd_slow = macd_slow or settings.MACD_SLOW
        self.macd_signal = macd_signal or settings.MACD_SIGNAL
        self.kd_period = kd_period or settings.KD_PERIOD
        self.bollinger_period = bollinger_period or settings.BOLLINGER_PERIOD
        self.bollinger_std = bollinger_std or settings.BOLLINGER_STD
        self.breakout_threshold = breakout_threshold or settings.BREAKOUT_THRESHOLD
    
    # ==================== 移動平均線 (MA) ====================
    
    def calculate_ma(self, df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
        """計算簡單移動平均線 (SMA)"""
        return df[column].rolling(window=period).mean()
    
    def calculate_ema(self, df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
        """計算指數移動平均線 (EMA)"""
        return df[column].ewm(span=period, adjust=False).mean()
    
    def add_ma_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        新增移動平均線指標
        
        Returns:
            新增 ma20, ma50, ma200, ma250 欄位的 DataFrame
        """
        df = df.copy()
        df[f"ma{self.ma_short}"] = self.calculate_ma(df, self.ma_short)
        df[f"ma{self.ma_mid}"] = self.calculate_ma(df, self.ma_mid)
        df[f"ma{self.ma_long}"] = self.calculate_ma(df, self.ma_long)
        df["ma250"] = self.calculate_ma(df, 250)  # 添加 MA250
        return df
    
    def get_ma_alignment(self, df: pd.DataFrame) -> Tuple[TrendDirection, str]:
        """
        判斷均線排列
        
        Returns:
            (趨勢方向, 描述)
        """
        if len(df) < self.ma_long:
            return TrendDirection.NEUTRAL, "資料不足"
        
        latest = df.iloc[-1]
        ma_short = latest.get(f"ma{self.ma_short}")
        ma_mid = latest.get(f"ma{self.ma_mid}")
        ma_long = latest.get(f"ma{self.ma_long}")
        price = latest["close"]
        
        if pd.isna(ma_short) or pd.isna(ma_mid) or pd.isna(ma_long):
            return TrendDirection.NEUTRAL, "均線資料不足"
        
        # 多頭排列：價格 > 短均 > 中均 > 長均
        if price > ma_short > ma_mid > ma_long:
            return TrendDirection.BULLISH, "多頭排列"
        
        # 空頭排列：價格 < 短均 < 中均 < 長均
        if price < ma_short < ma_mid < ma_long:
            return TrendDirection.BEARISH, "空頭排列"
        
        return TrendDirection.NEUTRAL, "盤整"
    
    def check_ma_cross(self, df: pd.DataFrame, short_ma: str, long_ma: str) -> Optional[Signal]:
        """
        檢查均線交叉
        
        Args:
            df: 含有均線資料的 DataFrame
            short_ma: 短均線欄位名稱 (如 "ma20")
            long_ma: 長均線欄位名稱 (如 "ma50")
            
        Returns:
            Signal 物件或 None
        """
        if len(df) < 2:
            return None
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        short_today = today.get(short_ma)
        short_yesterday = yesterday.get(short_ma)
        long_today = today.get(long_ma)
        long_yesterday = yesterday.get(long_ma)
        
        if any(pd.isna(x) for x in [short_today, short_yesterday, long_today, long_yesterday]):
            return None
        
        # 黃金交叉：短均線由下往上穿越長均線
        if short_yesterday < long_yesterday and short_today > long_today:
            return Signal(
                type=SignalType.GOLDEN_CROSS,
                indicator=f"{short_ma}/{long_ma}",
                description=f"{short_ma.upper()} 黃金交叉 {long_ma.upper()}",
            )
        
        # 死亡交叉：短均線由上往下穿越長均線
        if short_yesterday > long_yesterday and short_today < long_today:
            return Signal(
                type=SignalType.DEATH_CROSS,
                indicator=f"{short_ma}/{long_ma}",
                description=f"{short_ma.upper()} 死亡交叉 {long_ma.upper()}",
            )
        
        return None
    
    def check_price_vs_ma(
        self,
        price: float,
        ma_value: float,
        ma_name: str,
    ) -> Optional[Signal]:
        """
        檢查價格與均線的關係（接近突破/跌破）
        
        Args:
            price: 當前價格
            ma_value: 均線值
            ma_name: 均線名稱 (如 "MA20")
            
        Returns:
            Signal 物件或 None
        """
        if pd.isna(ma_value):
            return None
        
        distance_pct = ((price - ma_value) / ma_value) * 100
        
        # 價格在均線下方，且距離小於門檻 -> 接近向上突破
        if -self.breakout_threshold < distance_pct < 0:
            return Signal(
                type=SignalType.APPROACHING_BREAKOUT,
                indicator=ma_name,
                description=f"接近突破 {ma_name} ({abs(distance_pct):.1f}%)",
                value=distance_pct,
            )
        
        # 價格在均線上方，且距離小於門檻 -> 接近向下跌破
        if 0 < distance_pct < self.breakout_threshold:
            return Signal(
                type=SignalType.APPROACHING_BREAKDOWN,
                indicator=ma_name,
                description=f"接近跌破 {ma_name} ({distance_pct:.1f}%)",
                value=distance_pct,
            )
        
        return None
    
    # ==================== RSI ====================
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = None) -> pd.Series:
        """
        計算 RSI（相對強弱指標）
        
        RSI = 100 - (100 / (1 + RS))
        RS = 平均漲幅 / 平均跌幅
        """
        period = period or self.rsi_period
        
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def add_rsi_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """新增 RSI 指標"""
        df = df.copy()
        df["rsi"] = self.calculate_rsi(df)
        return df
    
    def get_rsi_status(self, rsi_value: float) -> Tuple[str, str]:
        """
        取得 RSI 狀態
        
        Returns:
            (狀態, 描述)
        """
        if pd.isna(rsi_value):
            return "unknown", "資料不足"
        
        if rsi_value >= self.rsi_overbought:
            return "overbought", f"超買 ({rsi_value:.1f})"
        elif rsi_value <= self.rsi_oversold:
            return "oversold", f"超賣 ({rsi_value:.1f})"
        else:
            return "neutral", f"中性 ({rsi_value:.1f})"
    
    def check_rsi_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        """檢查 RSI 訊號"""
        if len(df) < 2 or "rsi" not in df.columns:
            return None
        
        rsi_today = df["rsi"].iloc[-1]
        rsi_yesterday = df["rsi"].iloc[-2]
        
        if pd.isna(rsi_today) or pd.isna(rsi_yesterday):
            return None
        
        # 進入超買區
        if rsi_yesterday < self.rsi_overbought <= rsi_today:
            return Signal(
                type=SignalType.OVERBOUGHT,
                indicator="RSI",
                description=f"RSI 進入超買區 ({rsi_today:.1f})",
                value=rsi_today,
            )
        
        # 進入超賣區
        if rsi_yesterday > self.rsi_oversold >= rsi_today:
            return Signal(
                type=SignalType.OVERSOLD,
                indicator="RSI",
                description=f"RSI 進入超賣區 ({rsi_today:.1f})",
                value=rsi_today,
            )
        
        return None
    
    # ==================== MACD ====================
    
    def calculate_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        計算 MACD
        
        Returns:
            (DIF, MACD/DEA, Histogram)
        """
        ema_fast = self.calculate_ema(df, self.macd_fast)
        ema_slow = self.calculate_ema(df, self.macd_slow)
        
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = dif - dea
        
        return dif, dea, histogram
    
    def add_macd_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """新增 MACD 指標"""
        df = df.copy()
        df["macd_dif"], df["macd_dea"], df["macd_hist"] = self.calculate_macd(df)
        return df
    
    def check_macd_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        """檢查 MACD 交叉訊號"""
        if len(df) < 2:
            return None
        
        dif_today = df["macd_dif"].iloc[-1]
        dif_yesterday = df["macd_dif"].iloc[-2]
        dea_today = df["macd_dea"].iloc[-1]
        dea_yesterday = df["macd_dea"].iloc[-2]
        
        if any(pd.isna(x) for x in [dif_today, dif_yesterday, dea_today, dea_yesterday]):
            return None
        
        # 黃金交叉：DIF 由下往上穿越 DEA
        if dif_yesterday < dea_yesterday and dif_today > dea_today:
            position = "零軸上方" if dif_today > 0 else "零軸下方"
            return Signal(
                type=SignalType.GOLDEN_CROSS,
                indicator="MACD",
                description=f"MACD 黃金交叉 ({position})",
                value=dif_today,
            )
        
        # 死亡交叉：DIF 由上往下穿越 DEA
        if dif_yesterday > dea_yesterday and dif_today < dea_today:
            position = "零軸上方" if dif_today > 0 else "零軸下方"
            return Signal(
                type=SignalType.DEATH_CROSS,
                indicator="MACD",
                description=f"MACD 死亡交叉 ({position})",
                value=dif_today,
            )
        
        return None
    
    # ==================== KD ====================
    
    def calculate_kd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        計算 KD（隨機指標）
        
        RSV = (今日收盤 - N日最低) / (N日最高 - N日最低) × 100
        K = 2/3 × 昨日K + 1/3 × RSV
        D = 2/3 × 昨日D + 1/3 × K
        
        Returns:
            (K, D)
        """
        period = self.kd_period
        
        lowest = df["low"].rolling(window=period).min()
        highest = df["high"].rolling(window=period).max()
        
        rsv = ((df["close"] - lowest) / (highest - lowest)) * 100
        
        # 初始化 K, D
        k = pd.Series(index=df.index, dtype=float)
        d = pd.Series(index=df.index, dtype=float)
        
        # 第一個有效值設為 50
        first_valid = rsv.first_valid_index()
        if first_valid is not None:
            idx = df.index.get_loc(first_valid)
            k.iloc[idx] = 50
            d.iloc[idx] = 50
            
            # 迭代計算
            for i in range(idx + 1, len(df)):
                k.iloc[i] = (2/3) * k.iloc[i-1] + (1/3) * rsv.iloc[i]
                d.iloc[i] = (2/3) * d.iloc[i-1] + (1/3) * k.iloc[i]
        
        return k, d
    
    def add_kd_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """新增 KD 指標"""
        df = df.copy()
        df["kd_k"], df["kd_d"] = self.calculate_kd(df)
        return df
    
    def check_kd_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        """檢查 KD 交叉訊號"""
        if len(df) < 2:
            return None
        
        k_today = df["kd_k"].iloc[-1]
        k_yesterday = df["kd_k"].iloc[-2]
        d_today = df["kd_d"].iloc[-1]
        d_yesterday = df["kd_d"].iloc[-2]
        
        if any(pd.isna(x) for x in [k_today, k_yesterday, d_today, d_yesterday]):
            return None
        
        # 黃金交叉：K 由下往上穿越 D
        if k_yesterday < d_yesterday and k_today > d_today:
            zone = "超賣區" if k_today < 20 else ("超買區" if k_today > 80 else "中性區")
            return Signal(
                type=SignalType.GOLDEN_CROSS,
                indicator="KD",
                description=f"KD 黃金交叉 ({zone}, K={k_today:.1f})",
                value=k_today,
            )
        
        # 死亡交叉：K 由上往下穿越 D
        if k_yesterday > d_yesterday and k_today < d_today:
            zone = "超賣區" if k_today < 20 else ("超買區" if k_today > 80 else "中性區")
            return Signal(
                type=SignalType.DEATH_CROSS,
                indicator="KD",
                description=f"KD 死亡交叉 ({zone}, K={k_today:.1f})",
                value=k_today,
            )
        
        return None
    
    # ==================== 布林通道 ====================
    
    def calculate_bollinger(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        計算布林通道
        
        Returns:
            (上軌, 中軌, 下軌)
        """
        middle = df["close"].rolling(window=self.bollinger_period).mean()
        std = df["close"].rolling(window=self.bollinger_period).std()
        
        upper = middle + (self.bollinger_std * std)
        lower = middle - (self.bollinger_std * std)
        
        return upper, middle, lower
    
    def add_bollinger_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """新增布林通道指標"""
        df = df.copy()
        df["bb_upper"], df["bb_middle"], df["bb_lower"] = self.calculate_bollinger(df)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
        return df
    
    def get_bollinger_position(self, price: float, upper: float, middle: float, lower: float) -> str:
        """取得價格在布林通道中的位置"""
        if pd.isna(upper) or pd.isna(lower):
            return "unknown"
        
        if price >= upper:
            return "above_upper"
        elif price <= lower:
            return "below_lower"
        elif price >= middle:
            return "upper_half"
        else:
            return "lower_half"
    
    # ==================== OBV ====================
    
    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """
        計算 OBV（能量潮指標）
        
        若今日收盤 > 昨日收盤：OBV = 昨日 OBV + 今日成交量
        若今日收盤 < 昨日收盤：OBV = 昨日 OBV - 今日成交量
        若今日收盤 = 昨日收盤：OBV = 昨日 OBV
        """
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df["volume"].iloc[0]
        
        for i in range(1, len(df)):
            if df["close"].iloc[i] > df["close"].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df["volume"].iloc[i]
            elif df["close"].iloc[i] < df["close"].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df["volume"].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def add_obv_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """新增 OBV 指標"""
        df = df.copy()
        # 檢查是否有 volume 欄位
        if "volume" not in df.columns:
            df["obv"] = None
            return df
        df["obv"] = self.calculate_obv(df)
        return df
    
    def get_obv_trend(self, df: pd.DataFrame, lookback: int = 5) -> str:
        """
        判斷 OBV 趨勢
        
        Args:
            df: 含有 OBV 的 DataFrame
            lookback: 回顧天數
            
        Returns:
            趨勢字串 ("rising", "falling", "flat")
        """
        if "obv" not in df.columns or len(df) < lookback:
            return "unknown"
        
        obv_recent = df["obv"].iloc[-lookback:]
        
        if obv_recent.is_monotonic_increasing:
            return "rising"
        elif obv_recent.is_monotonic_decreasing:
            return "falling"
        else:
            # 比較首尾
            change_pct = (obv_recent.iloc[-1] - obv_recent.iloc[0]) / abs(obv_recent.iloc[0]) * 100
            if change_pct > 5:
                return "rising"
            elif change_pct < -5:
                return "falling"
            else:
                return "flat"
    
    # ==================== 成交量分析 ====================
    
    def calculate_volume_ratio(self, df: pd.DataFrame, ma_period: int = 20) -> pd.Series:
        """計算量比（今日成交量 / N日均量）"""
        avg_volume = df["volume"].rolling(window=ma_period).mean()
        return df["volume"] / avg_volume
    
    def add_volume_indicator(self, df: pd.DataFrame) -> pd.DataFrame:
        """新增成交量指標"""
        df = df.copy()
        # 檢查是否有 volume 欄位
        if "volume" not in df.columns:
            df["volume_ma20"] = None
            df["volume_ratio"] = None
            return df
        df["volume_ma20"] = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = self.calculate_volume_ratio(df)
        return df
    
    # ==================== 綜合計算 ====================
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算所有技術指標"""
        df = self.add_ma_indicators(df)
        df = self.add_rsi_indicator(df)
        df = self.add_macd_indicator(df)
        df = self.add_kd_indicator(df)
        df = self.add_bollinger_indicator(df)
        df = self.add_obv_indicator(df)
        df = self.add_volume_indicator(df)
        return df
    
    def get_all_signals(self, df: pd.DataFrame) -> List[Signal]:
        """取得所有訊號"""
        signals = []
        
        # MA 交叉
        ma_cross_20_50 = self.check_ma_cross(df, f"ma{self.ma_short}", f"ma{self.ma_mid}")
        if ma_cross_20_50:
            signals.append(ma_cross_20_50)
        
        ma_cross_50_200 = self.check_ma_cross(df, f"ma{self.ma_mid}", f"ma{self.ma_long}")
        if ma_cross_50_200:
            signals.append(ma_cross_50_200)
        
        # RSI
        rsi_signal = self.check_rsi_signal(df)
        if rsi_signal:
            signals.append(rsi_signal)
        
        # MACD
        macd_signal = self.check_macd_signal(df)
        if macd_signal:
            signals.append(macd_signal)
        
        # KD
        kd_signal = self.check_kd_signal(df)
        if kd_signal:
            signals.append(kd_signal)
        
        # 價格接近均線
        if len(df) > 0:
            latest = df.iloc[-1]
            price = latest["close"]
            
            for ma_col in [f"ma{self.ma_short}", f"ma{self.ma_mid}", f"ma{self.ma_long}"]:
                if ma_col in df.columns:
                    signal = self.check_price_vs_ma(price, latest[ma_col], ma_col.upper())
                    if signal:
                        signals.append(signal)
        
        return signals
    
    def calculate_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        計算綜合評分
        
        Returns:
            {
                "buy_score": int,
                "sell_score": int,
                "rating": str,
                "details": list
            }
        """
        buy_score = 0
        sell_score = 0
        details = []
        
        if len(df) < self.ma_long:
            return {
                "buy_score": 0,
                "sell_score": 0,
                "rating": "insufficient_data",
                "details": ["資料不足，無法評分"],
            }
        
        latest = df.iloc[-1]
        
        # 1. 均線排列
        alignment, alignment_desc = self.get_ma_alignment(df)
        if alignment == TrendDirection.BULLISH:
            buy_score += 1
            details.append(f"✅ {alignment_desc}")
        elif alignment == TrendDirection.BEARISH:
            sell_score += 1
            details.append(f"❌ {alignment_desc}")
        
        # 2. RSI
        if "rsi" in df.columns:
            rsi = latest["rsi"]
            if not pd.isna(rsi):
                if rsi <= self.rsi_oversold:
                    buy_score += 1
                    details.append(f"✅ RSI 超賣 ({rsi:.1f})")
                elif rsi >= self.rsi_overbought:
                    sell_score += 1
                    details.append(f"❌ RSI 超買 ({rsi:.1f})")
        
        # 3. MACD
        if "macd_hist" in df.columns and len(df) >= 2:
            hist_today = latest["macd_hist"]
            hist_yesterday = df["macd_hist"].iloc[-2]
            if not pd.isna(hist_today) and not pd.isna(hist_yesterday):
                if hist_today > 0 and hist_today > hist_yesterday:
                    buy_score += 1
                    details.append("✅ MACD 動能增強")
                elif hist_today < 0 and hist_today < hist_yesterday:
                    sell_score += 1
                    details.append("❌ MACD 動能減弱")
        
        # 4. KD
        if "kd_k" in df.columns:
            k = latest["kd_k"]
            d = latest["kd_d"]
            if not pd.isna(k) and not pd.isna(d):
                if k < 20 and k > d:
                    buy_score += 1
                    details.append(f"✅ KD 低檔黃金交叉 (K={k:.1f})")
                elif k > 80 and k < d:
                    sell_score += 1
                    details.append(f"❌ KD 高檔死亡交叉 (K={k:.1f})")
        
        # 5. 布林通道
        if "bb_lower" in df.columns:
            price = latest["close"]
            bb_lower = latest["bb_lower"]
            bb_upper = latest["bb_upper"]
            bb_middle = latest["bb_middle"]
            
            if not pd.isna(bb_lower):
                if price <= bb_lower:
                    buy_score += 1
                    details.append("✅ 觸及布林下軌")
                elif price >= bb_upper:
                    sell_score += 1
                    details.append("❌ 觸及布林上軌")
                elif price < bb_middle and len(df) >= 2:
                    if df["close"].iloc[-2] >= bb_middle:
                        sell_score += 1
                        details.append("❌ 跌破布林中軌")
        
        # 6. 量能
        if "volume_ratio" in df.columns:
            vol_ratio = latest["volume_ratio"]
            if not pd.isna(vol_ratio):
                if vol_ratio >= 2.0:
                    details.append(f"📊 成交量爆增 (量比 {vol_ratio:.1f})")
        
        # 7. OBV
        if "obv" in df.columns:
            obv_trend = self.get_obv_trend(df)
            if obv_trend == "rising":
                buy_score += 1
                details.append("✅ OBV 上升趨勢")
            elif obv_trend == "falling":
                sell_score += 1
                details.append("❌ OBV 下降趨勢")
        
        # 計算評等
        if buy_score >= 5:
            rating = "strong_buy"
        elif buy_score >= 3:
            rating = "buy"
        elif sell_score >= 5:
            rating = "strong_sell"
        elif sell_score >= 3:
            rating = "sell"
        else:
            rating = "neutral"
        
        return {
            "buy_score": buy_score,
            "sell_score": sell_score,
            "rating": rating,
            "details": details,
        }
    
    # ==================== 年化報酬率（CAGR）計算 ====================
    
    def calculate_cagr(
        self,
        df: pd.DataFrame,
        years: float,
    ) -> Optional[float]:
        """
        計算年化複合成長率（CAGR）
        
        公式: CAGR = (終值/初值)^(1/年數) - 1
        
        Args:
            df: 股價 DataFrame（需有 'close' 欄位）
            years: 計算的年數
            
        Returns:
            年化報酬率（百分比），例如 15.5 表示 15.5%
            如果資料不足則返回 None
        """
        if df is None or df.empty:
            return None
        
        # 計算需要的天數（假設一年約 252 個交易日）
        trading_days = int(years * 252)
        
        if len(df) < trading_days:
            return None
        
        try:
            # 取得終值（最新價格）
            end_price = float(df['close'].iloc[-1])
            
            # 取得初值（N年前價格）
            start_price = float(df['close'].iloc[-trading_days])
            
            if start_price <= 0 or end_price <= 0:
                return None
            
            # 計算 CAGR
            cagr = (end_price / start_price) ** (1 / years) - 1
            
            # 轉換為百分比
            return round(cagr * 100, 2)
        except Exception:
            return None
    
    def calculate_all_cagr(
        self,
        df: pd.DataFrame,
    ) -> Dict[str, Optional[float]]:
        """
        計算所有時間範圍的年化報酬率
        
        Returns:
            {
                "cagr_1y": 15.5,   # 1 年年化
                "cagr_3y": 12.3,   # 3 年年化
                "cagr_5y": 18.7,   # 5 年年化
                "cagr_10y": 14.2,  # 10 年年化
            }
        """
        return {
            "cagr_1y": self.calculate_cagr(df, 1),
            "cagr_3y": self.calculate_cagr(df, 3),
            "cagr_5y": self.calculate_cagr(df, 5),
            "cagr_10y": self.calculate_cagr(df, 10),
        }
    
    def calculate_cagr_from_prices(
        self,
        start_price: float,
        end_price: float,
        years: float,
    ) -> Optional[float]:
        """
        從起始和結束價格計算 CAGR
        
        Args:
            start_price: 起始價格
            end_price: 結束價格
            years: 年數
            
        Returns:
            年化報酬率（百分比）
        """
        if start_price <= 0 or end_price <= 0 or years <= 0:
            return None
        
        try:
            cagr = (end_price / start_price) ** (1 / years) - 1
            return round(cagr * 100, 2)
        except Exception:
            return None


# 建立預設實例
indicator_service = IndicatorService()
