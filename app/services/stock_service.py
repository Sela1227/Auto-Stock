"""
è‚¡ç¥¨æœå‹™
æ•´åˆè³‡æ–™æŠ“å–ã€å¿«å–å’ŒæŠ€è¡“æŒ‡æ¨™è¨ˆç®—
"""
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import logging

from app.models.stock_price import StockPrice
from app.data_sources.yahoo_finance import yahoo_finance
from app.services.indicator_service import indicator_service, TrendDirection
from app.config import settings

logger = logging.getLogger(__name__)


class StockService:
    """è‚¡ç¥¨æœå‹™"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """
        æª¢æŸ¥å¿«å–æ˜¯å¦æœ‰æ•ˆ
        
        è¦å‰‡ï¼š
        1. æœ‰ä»Šæ—¥è³‡æ–™
        2. æˆ–æ˜¯é€±æœ«/å‡æ—¥æ™‚æœ‰æœ€è¿‘äº¤æ˜“æ—¥è³‡æ–™
        """
        today = date.today()
        
        # æŸ¥è©¢æœ€æ–°è³‡æ–™
        stmt = (
            select(StockPrice)
            .where(StockPrice.symbol == symbol.upper())
            .order_by(StockPrice.date.desc())
            .limit(1)
        )
        result = self.db.execute(stmt).scalar_one_or_none()
        
        if not result:
            return False
        
        # å¦‚æžœæœ‰ä»Šæ—¥è³‡æ–™ï¼Œå¿«å–æœ‰æ•ˆ
        if result.date == today:
            return True
        
        # æª¢æŸ¥æ˜¯å¦ç‚ºé€±æœ«
        if today.weekday() >= 5:  # é€±å…­=5, é€±æ—¥=6
            # é€±æœ«æ™‚ï¼Œåªè¦æœ‰é€±äº”çš„è³‡æ–™å°±ç®—æœ‰æ•ˆ
            friday = today - timedelta(days=(today.weekday() - 4))
            if result.date >= friday:
                return True
        
        # æª¢æŸ¥æ›´æ–°æ™‚é–“æ˜¯å¦åœ¨å¿«å–æ™‚é–“å…§
        if result.updated_at:
            cache_hours = settings.STOCK_DATA_CACHE_HOURS
            cache_deadline = datetime.now() - timedelta(hours=cache_hours)
            if result.updated_at > cache_deadline:
                return True
        
        return False
    
    def _save_prices_to_db(self, df: pd.DataFrame) -> int:
        """
        å„²å­˜åƒ¹æ ¼è³‡æ–™åˆ°è³‡æ–™åº«
        
        Returns:
            å„²å­˜çš„ç­†æ•¸
        """
        if df is None or df.empty:
            return 0
        
        count = 0
        for _, row in df.iterrows():
            # æª¢æŸ¥æ˜¯å¦å·²å­˜åœ¨
            stmt = select(StockPrice).where(
                and_(
                    StockPrice.symbol == row["symbol"],
                    StockPrice.date == row["date"],
                )
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if existing:
                # æ›´æ–°ç¾æœ‰è³‡æ–™
                existing.open = row["open"]
                existing.high = row["high"]
                existing.low = row["low"]
                existing.close = row["close"]
                existing.volume = row["volume"]
            else:
                # æ–°å¢žè³‡æ–™
                price = StockPrice(
                    symbol=row["symbol"],
                    date=row["date"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                )
                self.db.add(price)
                count += 1
        
        self.db.commit()
        return count
    
    def _load_prices_from_db(
        self,
        symbol: str,
        days: int = 365,
    ) -> Optional[pd.DataFrame]:
        """å¾žè³‡æ–™åº«è¼‰å…¥åƒ¹æ ¼è³‡æ–™"""
        start_date = date.today() - timedelta(days=days)
        
        stmt = (
            select(StockPrice)
            .where(
                and_(
                    StockPrice.symbol == symbol.upper(),
                    StockPrice.date >= start_date,
                )
            )
            .order_by(StockPrice.date)
        )
        results = self.db.execute(stmt).scalars().all()
        
        if not results:
            return None
        
        data = []
        for r in results:
            data.append({
                "symbol": r.symbol,
                "date": r.date,
                "open": float(r.open) if r.open else None,
                "high": float(r.high) if r.high else None,
                "low": float(r.low) if r.low else None,
                "close": float(r.close) if r.close else None,
                "volume": r.volume,
            })
        
        return pd.DataFrame(data)
    
    def fetch_and_cache_stock(self, symbol: str, period: str = "1y") -> bool:
        """
        æŠ“å–è‚¡ç¥¨è³‡æ–™ä¸¦å¿«å–
        
        Returns:
            æ˜¯å¦æˆåŠŸ
        """
        df = yahoo_finance.get_stock_history(symbol, period=period)
        if df is None:
            return False
        
        self._save_prices_to_db(df)
        return True
    
    def get_stock_data(
        self,
        symbol: str,
        force_refresh: bool = False,
    ) -> Optional[pd.DataFrame]:
        """
        å–å¾—è‚¡ç¥¨è³‡æ–™ï¼ˆå„ªå…ˆä½¿ç”¨å¿«å–ï¼‰
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            force_refresh: æ˜¯å¦å¼·åˆ¶æ›´æ–°
            
        Returns:
            åŒ…å«åƒ¹æ ¼å’ŒæŠ€è¡“æŒ‡æ¨™çš„ DataFrame
        """
        symbol = symbol.upper()
        
        # æª¢æŸ¥å¿«å–
        if not force_refresh and self._is_cache_valid(symbol):
            logger.info(f"ä½¿ç”¨å¿«å–è³‡æ–™: {symbol}")
            df = self._load_prices_from_db(symbol)
        else:
            # å¾ž Yahoo Finance æŠ“å–
            logger.info(f"å¾ž Yahoo Finance æŠ“å–: {symbol}")
            if not self.fetch_and_cache_stock(symbol):
                # æŠ“å–å¤±æ•—ï¼Œå˜—è©¦ä½¿ç”¨èˆŠçš„å¿«å–
                df = self._load_prices_from_db(symbol)
                if df is None:
                    return None
            else:
                df = self._load_prices_from_db(symbol)
        
        if df is None or df.empty:
            return None
        
        # è¨ˆç®—æŠ€è¡“æŒ‡æ¨™
        df = indicator_service.calculate_all_indicators(df)
        
        return df
    
    def get_stock_analysis(
        self,
        symbol: str,
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        å–å¾—è‚¡ç¥¨å®Œæ•´åˆ†æžå ±å‘Š
        
        Returns:
            åˆ†æžå ±å‘Šå­—å…¸
        """
        symbol = symbol.upper()
        
        # å–å¾—è³‡æ–™
        df = self.get_stock_data(symbol, force_refresh)
        if df is None:
            return None
        
        # å–å¾—è‚¡ç¥¨åŸºæœ¬è³‡è¨Š
        info = yahoo_finance.get_stock_info(symbol)
        
        # æœ€æ–°åƒ¹æ ¼è³‡æ–™
        latest = df.iloc[-1]
        price = float(latest["close"])
        
        # è¨ˆç®—æ¼²è·Œå¹…
        changes = self._calculate_changes(df)
        
        # æŠ€è¡“æŒ‡æ¨™
        indicators = self._get_indicators_summary(df, latest)
        
        # è¨Šè™Ÿ
        signals = indicator_service.get_all_signals(df)
        
        # è©•åˆ†
        score = indicator_service.calculate_score(df)
        
        # æˆäº¤é‡
        volume_info = self._get_volume_info(df, latest)
        
        return {
            "symbol": symbol,
            "name": info.get("name", "N/A") if info else "N/A",
            "asset_type": "stock",
            "price": {
                "current": price,
                "high_52w": info.get("fifty_two_week_high") if info else None,
                "low_52w": info.get("fifty_two_week_low") if info else None,
                "from_high_pct": self._calc_pct_from_high(price, info),
                "from_low_pct": self._calc_pct_from_low(price, info),
            },
            "change": changes,
            "volume": volume_info,
            "indicators": indicators,
            "signals": [
                {
                    "type": s.type.value,
                    "indicator": s.indicator,
                    "description": s.description,
                }
                for s in signals
            ],
            "score": score,
            "updated_at": datetime.now().isoformat(),
        }
    
    def _calculate_changes(self, df: pd.DataFrame) -> Dict[str, float]:
        """è¨ˆç®—å„æ™‚é–“æ®µæ¼²è·Œå¹…"""
        latest_close = df["close"].iloc[-1]
        
        def calc_change(days: int) -> Optional[float]:
            if len(df) <= days:
                return None
            old_close = df["close"].iloc[-(days + 1)]
            return round((latest_close - old_close) / old_close * 100, 2)
        
        return {
            "day": calc_change(1),
            "week": calc_change(5),
            "month": calc_change(20),
            "quarter": calc_change(60),
            "year": calc_change(250) if len(df) > 250 else None,
        }
    
    def _get_indicators_summary(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
    ) -> Dict[str, Any]:
        """å–å¾—æŒ‡æ¨™æ‘˜è¦"""
        price = float(latest["close"])
        
        # MA
        ma_short = latest.get(f"ma{settings.MA_SHORT}")
        ma_mid = latest.get(f"ma{settings.MA_MID}")
        ma_long = latest.get(f"ma{settings.MA_LONG}")
        
        alignment, _ = indicator_service.get_ma_alignment(df)
        
        ma_info = {
            f"ma{settings.MA_SHORT}": round(ma_short, 2) if not pd.isna(ma_short) else None,
            f"ma{settings.MA_MID}": round(ma_mid, 2) if not pd.isna(ma_mid) else None,
            f"ma{settings.MA_LONG}": round(ma_long, 2) if not pd.isna(ma_long) else None,
            "alignment": alignment.value,
            f"price_vs_ma{settings.MA_SHORT}": "above" if price > ma_short else "below" if not pd.isna(ma_short) else None,
            f"price_vs_ma{settings.MA_MID}": "above" if price > ma_mid else "below" if not pd.isna(ma_mid) else None,
            f"price_vs_ma{settings.MA_LONG}": "above" if price > ma_long else "below" if not pd.isna(ma_long) else None,
        }
        
        # RSI
        rsi = latest.get("rsi")
        rsi_status, _ = indicator_service.get_rsi_status(rsi)
        rsi_info = {
            "value": round(rsi, 2) if not pd.isna(rsi) else None,
            "status": rsi_status,
        }
        
        # MACD
        macd_dif = latest.get("macd_dif")
        macd_dea = latest.get("macd_dea")
        macd_hist = latest.get("macd_hist")
        macd_info = {
            "dif": round(macd_dif, 4) if not pd.isna(macd_dif) else None,
            "dea": round(macd_dea, 4) if not pd.isna(macd_dea) else None,
            "histogram": round(macd_hist, 4) if not pd.isna(macd_hist) else None,
            "status": "bullish" if macd_hist and macd_hist > 0 else "bearish",
        }
        
        # KD
        kd_k = latest.get("kd_k")
        kd_d = latest.get("kd_d")
        kd_info = {
            "k": round(kd_k, 2) if not pd.isna(kd_k) else None,
            "d": round(kd_d, 2) if not pd.isna(kd_d) else None,
            "status": self._get_kd_status(kd_k),
        }
        
        # Bollinger
        bb_upper = latest.get("bb_upper")
        bb_middle = latest.get("bb_middle")
        bb_lower = latest.get("bb_lower")
        bb_info = {
            "upper": round(bb_upper, 2) if not pd.isna(bb_upper) else None,
            "middle": round(bb_middle, 2) if not pd.isna(bb_middle) else None,
            "lower": round(bb_lower, 2) if not pd.isna(bb_lower) else None,
            "position": indicator_service.get_bollinger_position(price, bb_upper, bb_middle, bb_lower),
        }
        
        # OBV
        obv_trend = indicator_service.get_obv_trend(df)
        obv_info = {
            "trend": obv_trend,
        }
        
        return {
            "ma": ma_info,
            "rsi": rsi_info,
            "macd": macd_info,
            "kd": kd_info,
            "bollinger": bb_info,
            "obv": obv_info,
        }
    
    def _get_kd_status(self, k_value: float) -> str:
        """å–å¾— KD ç‹€æ…‹"""
        if pd.isna(k_value):
            return "unknown"
        if k_value > 80:
            return "overbought"
        elif k_value < 20:
            return "oversold"
        elif k_value > 50:
            return "neutral_high"
        else:
            return "neutral_low"
    
    def _get_volume_info(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
    ) -> Dict[str, Any]:
        """å–å¾—æˆäº¤é‡è³‡è¨Š"""
        today_vol = latest.get("volume", 0)
        avg_vol = latest.get("volume_ma20")
        vol_ratio = latest.get("volume_ratio")
        
        return {
            "today": int(today_vol) if today_vol else 0,
            "avg_20d": int(avg_vol) if not pd.isna(avg_vol) else None,
            "ratio": round(vol_ratio, 2) if not pd.isna(vol_ratio) else None,
        }
    
    def _calc_pct_from_high(self, price: float, info: Optional[Dict]) -> Optional[float]:
        """è¨ˆç®—è·é›¢ 52 é€±é«˜é»žçš„è·Œå¹…"""
        if not info or not info.get("fifty_two_week_high"):
            return None
        high = info["fifty_two_week_high"]
        return round((price - high) / high * 100, 2)
    
    def _calc_pct_from_low(self, price: float, info: Optional[Dict]) -> Optional[float]:
        """è¨ˆç®—è·é›¢ 52 é€±ä½Žé»žçš„æ¼²å¹…"""
        if not info or not info.get("fifty_two_week_low"):
            return None
        low = info["fifty_two_week_low"]
        return round((price - low) / low * 100, 2)
    
    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """
        æœå°‹è‚¡ç¥¨ï¼ˆç°¡å–®å¯¦ä½œï¼Œç›´æŽ¥é©—è­‰ä»£è™Ÿï¼‰
        
        Returns:
            ç¬¦åˆçš„è‚¡ç¥¨åˆ—è¡¨
        """
        symbol = query.upper().strip()
        
        if yahoo_finance.validate_symbol(symbol):
            info = yahoo_finance.get_stock_info(symbol)
            if info:
                return [{
                    "symbol": info["symbol"],
                    "name": info.get("name", "N/A"),
                }]
        
        return []
    
    def fetch_extended_history(
        self,
        symbol: str,
        years: int = 10,
    ) -> bool:
        """
        æŠ“å–ä¸¦å¿«å–å»¶ä¼¸æ­·å²è³‡æ–™ï¼ˆæ”¯æ´å¤šå¹´ï¼‰
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            years: å¹´æ•¸ (1, 3, 5, 10)
            
        Returns:
            æ˜¯å¦æˆåŠŸ
        """
        period_map = {1: "1y", 2: "2y", 5: "5y", 10: "10y"}
        period = period_map.get(years, "10y")
        
        df = yahoo_finance.get_stock_history(symbol, period=period)
        if df is None:
            return False
        
        self._save_prices_to_db(df)
        return True
    
    def get_price_history(
        self,
        symbol: str,
        days: int = 365,
    ) -> Optional[pd.DataFrame]:
        """
        å–å¾—è‚¡ç¥¨åƒ¹æ ¼æ­·å²ï¼ˆå¾žè³‡æ–™åº«ï¼‰
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            days: å¤©æ•¸
            
        Returns:
            åƒ¹æ ¼ DataFrame
        """
        return self._load_prices_from_db(symbol, days)
    
    def ensure_historical_data(
        self,
        symbol: str,
        years: int = 10,
    ) -> bool:
        """
        ç¢ºä¿æœ‰è¶³å¤ çš„æ­·å²è³‡æ–™
        
        æª¢æŸ¥è³‡æ–™åº«æ˜¯å¦æœ‰æŒ‡å®šå¹´ä»½çš„è³‡æ–™ï¼Œ
        å¦‚æžœä¸è¶³å‰‡å¾ž API æŠ“å–è£œé½Š
        """
        symbol = symbol.upper()
        days_needed = years * 365
        
        # æª¢æŸ¥è³‡æ–™åº«ä¸­æœ€æ—©çš„è³‡æ–™æ—¥æœŸ
        stmt = (
            select(StockPrice)
            .where(StockPrice.symbol == symbol)
            .order_by(StockPrice.date)
            .limit(1)
        )
        earliest = self.db.execute(stmt).scalar_one_or_none()
        
        if earliest:
            days_available = (date.today() - earliest.date).days
            if days_available >= days_needed * 0.9:  # 90% å°±ç®—è¶³å¤ 
                return True
        
        # è³‡æ–™ä¸è¶³ï¼ŒæŠ“å–æ›´å¤š
        logger.info(f"æŠ“å– {symbol} çš„ {years} å¹´æ­·å²è³‡æ–™")
        return self.fetch_extended_history(symbol, years)