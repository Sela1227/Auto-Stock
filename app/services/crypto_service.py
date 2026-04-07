"""
åŠ å¯†è²¨å¹£æœå‹™
æ•´åˆ CoinGecko è³‡æ–™ã€å¿«å–å’ŒæŠ€è¡“æŒ‡æ¨™è¨ˆç®—
"""
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import logging

from app.models.crypto_price import CryptoPrice
from app.models.market_sentiment import MarketSentiment
from app.data_sources.coingecko import coingecko
from app.data_sources.fear_greed import fear_greed
from app.services.indicator_service import indicator_service, TrendDirection
from app.config import settings

logger = logging.getLogger(__name__)


class CryptoService:
    """åŠ å¯†è²¨å¹£æœå‹™"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """æª¢æŸ¥å¿«å–æ˜¯å¦æœ‰æ•ˆ"""
        today = date.today()
        
        stmt = (
            select(CryptoPrice)
            .where(CryptoPrice.symbol == symbol.upper())
            .order_by(CryptoPrice.date.desc())
            .limit(1)
        )
        result = self.db.execute(stmt).scalar_one_or_none()
        
        if not result:
            return False
        
        # åŠ å¯†è²¨å¹£å¸‚å ´ 24/7ï¼Œæª¢æŸ¥æ›´æ–°æ™‚é–“
        if result.updated_at:
            cache_minutes = settings.CRYPTO_DATA_CACHE_MINUTES
            cache_deadline = datetime.now() - timedelta(minutes=cache_minutes)
            if result.updated_at > cache_deadline:
                return True
        
        return False
    
    def _save_prices_to_db(self, df: pd.DataFrame) -> int:
        """å„²å­˜åƒ¹æ ¼è³‡æ–™åˆ°è³‡æ–™åº«"""
        if df is None or df.empty:
            return 0
        
        count = 0
        for _, row in df.iterrows():
            stmt = select(CryptoPrice).where(
                and_(
                    CryptoPrice.symbol == row["symbol"],
                    CryptoPrice.date == row["date"],
                )
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if existing:
                existing.price = row.get("price") or row.get("close")
                existing.volume_24h = row.get("volume_24h")
                existing.market_cap = row.get("market_cap")
            else:
                price = CryptoPrice(
                    symbol=row["symbol"],
                    date=row["date"],
                    price=row.get("price") or row.get("close"),
                    volume_24h=row.get("volume_24h"),
                    market_cap=row.get("market_cap"),
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
            select(CryptoPrice)
            .where(
                and_(
                    CryptoPrice.symbol == symbol.upper(),
                    CryptoPrice.date >= start_date,
                )
            )
            .order_by(CryptoPrice.date)
        )
        results = self.db.execute(stmt).scalars().all()
        
        if not results:
            return None
        
        data = []
        for r in results:
            data.append({
                "symbol": r.symbol,
                "date": r.date,
                "close": float(r.price) if r.price else None,
                "price": float(r.price) if r.price else None,
                "volume": float(r.volume_24h) if r.volume_24h else 0,
                "volume_24h": float(r.volume_24h) if r.volume_24h else None,
                "market_cap": float(r.market_cap) if r.market_cap else None,
                # åŠ å¯†è²¨å¹£æ²’æœ‰ OHLCï¼Œç”¨ close å¡«å……
                "open": float(r.price) if r.price else None,
                "high": float(r.price) if r.price else None,
                "low": float(r.price) if r.price else None,
            })
        
        return pd.DataFrame(data)
    
    def fetch_and_cache_crypto(self, symbol: str, days: int = 365) -> bool:
        """æŠ“å–åŠ å¯†è²¨å¹£è³‡æ–™ä¸¦å¿«å–"""
        df = coingecko.get_market_chart(symbol, days=days)
        if df is None:
            return False
        
        # è½‰æ›æ¬„ä½åç¨±ä»¥ç¬¦åˆè³‡æ–™åº«
        df["close"] = df["price"]
        
        self._save_prices_to_db(df)
        return True
    
    def get_crypto_data(
        self,
        symbol: str,
        force_refresh: bool = False,
    ) -> Optional[pd.DataFrame]:
        """å–å¾—åŠ å¯†è²¨å¹£è³‡æ–™ï¼ˆå„ªå…ˆä½¿ç”¨å¿«å–ï¼‰"""
        symbol = symbol.upper()
        
        if not coingecko.validate_symbol(symbol):
            logger.warning(f"ä¸æ”¯æ´çš„åŠ å¯†è²¨å¹£: {symbol}")
            return None
        
        # æª¢æŸ¥å¿«å–
        if not force_refresh and self._is_cache_valid(symbol):
            logger.info(f"ä½¿ç”¨å¿«å–è³‡æ–™: {symbol}")
            df = self._load_prices_from_db(symbol)
        else:
            logger.info(f"å¾ž CoinGecko æŠ“å–: {symbol}")
            if not self.fetch_and_cache_crypto(symbol):
                df = self._load_prices_from_db(symbol)
                if df is None:
                    return None
            else:
                df = self._load_prices_from_db(symbol)
        
        if df is None or df.empty:
            return None
        
        # è¨ˆç®—æŠ€è¡“æŒ‡æ¨™ï¼ˆä½¿ç”¨é©åˆåŠ å¯†è²¨å¹£çš„åƒæ•¸ï¼‰
        df = self._calculate_crypto_indicators(df)
        
        return df
    
    def _calculate_crypto_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """è¨ˆç®—åŠ å¯†è²¨å¹£æŠ€è¡“æŒ‡æ¨™ï¼ˆä½¿ç”¨å¹£åœˆå¸¸ç”¨åƒæ•¸ï¼‰"""
        # å»ºç«‹å¹£åœˆå°ˆç”¨çš„æŒ‡æ¨™æœå‹™ï¼ˆä½¿ç”¨ä¸åŒçš„ MA é€±æœŸï¼‰
        crypto_indicator = indicator_service.__class__(
            ma_short=7,    # å¹£åœˆçŸ­å‡ç·š
            ma_mid=25,     # å¹£åœˆä¸­å‡ç·š
            ma_long=99,    # å¹£åœˆé•·å‡ç·š
        )
        
        df = crypto_indicator.add_ma_indicators(df)
        df = indicator_service.add_rsi_indicator(df)
        df = indicator_service.add_macd_indicator(df)
        df = indicator_service.add_kd_indicator(df)
        df = indicator_service.add_bollinger_indicator(df)
        
        # åŠ å¯†è²¨å¹£é€šå¸¸æ²’æœ‰çœŸæ­£çš„æˆäº¤é‡è³‡æ–™ï¼Œè·³éŽ OBV
        if 'volume' in df.columns and df['volume'].sum() > 0:
            df = indicator_service.add_obv_indicator(df)
        
        return df
    
    def get_crypto_analysis(
        self,
        symbol: str,
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """å–å¾—åŠ å¯†è²¨å¹£å®Œæ•´åˆ†æžå ±å‘Š"""
        symbol = symbol.upper()
        
        # å–å¾—è³‡æ–™
        df = self.get_crypto_data(symbol, force_refresh)
        if df is None:
            return None
        
        # å–å¾—è©³ç´°è³‡è¨Š
        info = coingecko.get_coin_info(symbol)
        
        # æœ€æ–°åƒ¹æ ¼
        latest = df.iloc[-1]
        price = float(latest["close"])
        
        # æ¼²è·Œå¹…
        changes = self._calculate_changes(df, info)
        
        # æŠ€è¡“æŒ‡æ¨™
        indicators = self._get_indicators_summary(df, latest)
        
        # è¨Šè™Ÿ
        signals = indicator_service.get_all_signals(df)
        
        # è©•åˆ†
        score = indicator_service.calculate_score(df)
        
        return {
            "symbol": symbol,
            "name": info.get("name", symbol) if info else symbol,
            "asset_type": "crypto",
            "price": {
                "current": price,
                "ath": info.get("ath") if info else None,
                "atl": info.get("atl") if info else None,
                "from_ath_pct": info.get("ath_change_percentage") if info else None,
                "high_24h": info.get("high_24h") if info else None,
                "low_24h": info.get("low_24h") if info else None,
            },
            "change": changes,
            "market": {
                "market_cap": info.get("market_cap") if info else None,
                "market_cap_rank": info.get("market_cap_rank") if info else None,
                "volume_24h": info.get("total_volume") if info else None,
                "circulating_supply": info.get("circulating_supply") if info else None,
            },
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
    
    def _calculate_changes(
        self,
        df: pd.DataFrame,
        info: Optional[Dict],
    ) -> Dict[str, float]:
        """è¨ˆç®—æ¼²è·Œå¹…"""
        changes = {}
        
        # å¾ž CoinGecko API å–å¾—
        if info:
            changes["day"] = info.get("price_change_percentage_24h")
            changes["week"] = info.get("price_change_percentage_7d")
            changes["month"] = info.get("price_change_percentage_30d")
            changes["year"] = info.get("price_change_percentage_1y")
        
        # å¾žæœ¬åœ°è³‡æ–™è¨ˆç®—
        latest_close = df["close"].iloc[-1]
        
        def calc_change(days: int) -> Optional[float]:
            if len(df) <= days:
                return None
            old_close = df["close"].iloc[-(days + 1)]
            if old_close and old_close != 0:
                return round((latest_close - old_close) / old_close * 100, 2)
            return None
        
        # è£œå……ç¼ºå¤±çš„è³‡æ–™
        if not changes.get("day"):
            changes["day"] = calc_change(1)
        if not changes.get("week"):
            changes["week"] = calc_change(7)
        if not changes.get("month"):
            changes["month"] = calc_change(30)
        
        return changes
    
    def _get_indicators_summary(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
    ) -> Dict[str, Any]:
        """å–å¾—æŒ‡æ¨™æ‘˜è¦"""
        price = float(latest["close"])
        
        # MAï¼ˆå¹£åœˆé€±æœŸï¼‰
        ma_info = {
            "ma7": round(latest.get("ma7", 0), 2) if not pd.isna(latest.get("ma7")) else None,
            "ma25": round(latest.get("ma25", 0), 2) if not pd.isna(latest.get("ma25")) else None,
            "ma99": round(latest.get("ma99", 0), 2) if not pd.isna(latest.get("ma99")) else None,
        }
        
        # åˆ¤æ–·å‡ç·šæŽ’åˆ—
        ma7 = latest.get("ma7")
        ma25 = latest.get("ma25")
        ma99 = latest.get("ma99")
        
        if not any(pd.isna(x) for x in [ma7, ma25, ma99]):
            if price > ma7 > ma25 > ma99:
                ma_info["alignment"] = "bullish"
            elif price < ma7 < ma25 < ma99:
                ma_info["alignment"] = "bearish"
            else:
                ma_info["alignment"] = "neutral"
        else:
            ma_info["alignment"] = "unknown"
        
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
        
        return {
            "ma": ma_info,
            "rsi": rsi_info,
            "macd": macd_info,
            "bollinger": bb_info,
        }
    
    # ==================== å¸‚å ´æƒ…ç·’ ====================
    
    def get_market_sentiment(self, market: str = "all") -> Dict[str, Any]:
        """
        å–å¾—å¸‚å ´æƒ…ç·’æŒ‡æ•¸
        
        Args:
            market: "stock", "crypto", or "all"
        """
        result = {}
        
        if market in ("all", "stock"):
            stock_sentiment = fear_greed.get_stock_fear_greed()
            if stock_sentiment:
                result["stock"] = stock_sentiment
                # å„²å­˜åˆ°è³‡æ–™åº«
                self._save_sentiment(stock_sentiment)
        
        if market in ("all", "crypto"):
            crypto_sentiment = fear_greed.get_crypto_fear_greed()
            if crypto_sentiment:
                result["crypto"] = crypto_sentiment
                # å„²å­˜åˆ°è³‡æ–™åº«
                self._save_sentiment(crypto_sentiment)
        
        return result
    
    def _save_sentiment(self, sentiment_data: Dict[str, Any]):
        """å„²å­˜æƒ…ç·’æŒ‡æ•¸åˆ°è³‡æ–™åº«"""
        try:
            market = sentiment_data.get("market")
            value = sentiment_data.get("value")
            timestamp = sentiment_data.get("timestamp")
            
            if not all([market, value, timestamp]):
                return
            
            sentiment_date = datetime.strptime(timestamp, "%Y-%m-%d").date()
            
            stmt = select(MarketSentiment).where(
                and_(
                    MarketSentiment.market == market,
                    MarketSentiment.date == sentiment_date,
                )
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if existing:
                existing.value = value
                existing.classification = sentiment_data.get("classification")
            else:
                sentiment = MarketSentiment(
                    date=sentiment_date,
                    market=market,
                    value=value,
                    classification=sentiment_data.get("classification"),
                )
                self.db.add(sentiment)
            
            self.db.commit()
        except Exception as e:
            logger.error(f"å„²å­˜æƒ…ç·’æŒ‡æ•¸å¤±æ•—: {e}")
    
    def get_supported_cryptos(self) -> List[Dict[str, str]]:
        """å–å¾—æ”¯æ´çš„åŠ å¯†è²¨å¹£åˆ—è¡¨"""
        from app.data_sources.coingecko import CRYPTO_MAP
        return [
            {"symbol": symbol, "id": coin_id}
            for symbol, coin_id in CRYPTO_MAP.items()
            if symbol not in ("BITCOIN", "ETHEREUM")  # æŽ’é™¤åˆ¥å
        ]