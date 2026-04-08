"""
市場服務
處理三大指數、市場情緒的資料存取

🚀 優化版 - 2026-04-07
- 加入內存快取（60秒過期），避免重複 DB 查詢
- 一次查詢取得所有市場資料
- 只在快取過期時才查詢 DB
"""
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc
import logging
import threading

from app.models.index_price import IndexPrice, INDEX_SYMBOLS
from app.models.market_sentiment import MarketSentiment
from app.models.dividend_history import DividendHistory
from app.models.stock_price import StockPrice
from app.data_sources.yahoo_finance import yahoo_finance
from app.data_sources.fear_greed import fear_greed

logger = logging.getLogger(__name__)


# ============================================================
# 🆕 內存快取（全域，所有 request 共用）
# ============================================================

class MemoryCache:
    """簡單的內存快取，線程安全"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str, max_age_seconds: int = 60) -> Optional[Any]:
        """取得快取值，過期返回 None"""
        with self._lock:
            if key not in self._cache:
                return None
            
            timestamp = self._timestamps.get(key)
            if timestamp is None:
                return None
            
            age = (datetime.now() - timestamp).total_seconds()
            if age > max_age_seconds:
                # 過期，清除
                del self._cache[key]
                del self._timestamps[key]
                return None
            
            return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """設定快取值"""
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = datetime.now()
    
    def clear(self, key: str = None) -> None:
        """清除快取"""
        with self._lock:
            if key:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
            else:
                self._cache.clear()
                self._timestamps.clear()


# 全域快取實例
_memory_cache = MemoryCache()

# 快取有效期（秒）
SENTIMENT_CACHE_SECONDS = 60  # 情緒指數 60 秒
INDICES_CACHE_SECONDS = 60    # 指數 60 秒


class MarketService:
    """市場服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 三大指數 ====================
    
    def get_latest_indices(self) -> Dict[str, Any]:
        """
        取得四大指數最新資料
        🆕 優先從內存快取讀取
        """
        # 嘗試從快取取得
        cached = _memory_cache.get("indices", INDICES_CACHE_SECONDS)
        if cached is not None:
            logger.debug("📦 指數快取命中 (memory)")
            return cached
        
        # 快取未命中，查詢 DB
        result = {}
        
        for symbol, info in INDEX_SYMBOLS.items():
            try:
                stmt = (
                    select(IndexPrice)
                    .where(IndexPrice.symbol == symbol)
                    .order_by(desc(IndexPrice.date))
                    .limit(1)
                )
                latest = self.db.execute(stmt).scalar_one_or_none()
                
                if latest:
                    result[symbol] = latest.to_dict()
                    logger.debug(f"📦 指數 DB: {symbol} = {latest.close}")
                else:
                    logger.warning(f"⚠️ 指數 {symbol} 無快取資料，請執行更新")
                    result[symbol] = {
                        "symbol": symbol,
                        "name": info["name"],
                        "name_zh": info["name_zh"],
                        "date": None,
                        "close": None,
                        "change": None,
                        "change_pct": None,
                    }
            except Exception as e:
                logger.error(f"讀取指數 {symbol} 失敗: {e}")
                result[symbol] = {
                    "symbol": symbol,
                    "name": info["name"],
                    "name_zh": info["name_zh"],
                    "date": None,
                    "close": None,
                    "change": None,
                    "change_pct": None,
                }
        
        # 寫入快取
        _memory_cache.set("indices", result)
        
        return result
    
    def get_index_history(
        self,
        symbol: str,
        days: int = 365,
    ) -> List[Dict[str, Any]]:
        """取得指數歷史資料"""
        start_date = date.today() - timedelta(days=days)
        
        stmt = (
            select(IndexPrice)
            .where(
                and_(
                    IndexPrice.symbol == symbol,
                    IndexPrice.date >= start_date,
                )
            )
            .order_by(IndexPrice.date)
        )
        results = self.db.execute(stmt).scalars().all()
        
        return [r.to_dict() for r in results]
    
    def save_index_data(self, df: pd.DataFrame, symbol: str) -> int:
        """儲存指數資料到資料庫"""
        import math
        
        def clean_value(val):
            if val is None:
                return None
            if pd.isna(val):
                return None
            try:
                f = float(val)
                if math.isnan(f) or math.isinf(f):
                    return None
                return f
            except (ValueError, TypeError):
                return None
        
        if df is None or df.empty:
            return 0
        
        count = 0
        index_info = INDEX_SYMBOLS.get(symbol, {})
        
        for _, row in df.iterrows():
            stmt = select(IndexPrice).where(
                and_(
                    IndexPrice.symbol == symbol,
                    IndexPrice.date == row["date"],
                )
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if existing:
                existing.open = clean_value(row.get("open"))
                existing.high = clean_value(row.get("high"))
                existing.low = clean_value(row.get("low"))
                existing.close = clean_value(row.get("close"))
                existing.volume = row.get("volume")
                existing.change = clean_value(row.get("change"))
                existing.change_pct = clean_value(row.get("change_pct"))
            else:
                price = IndexPrice(
                    symbol=symbol,
                    name=index_info.get("name", symbol),
                    date=row["date"],
                    open=clean_value(row.get("open")),
                    high=clean_value(row.get("high")),
                    low=clean_value(row.get("low")),
                    close=clean_value(row.get("close")),
                    volume=row.get("volume"),
                    change=clean_value(row.get("change")),
                    change_pct=clean_value(row.get("change_pct")),
                )
                self.db.add(price)
                count += 1
        
        self.db.commit()
        _memory_cache.clear("indices")
        return count
    
    def fetch_and_save_all_indices(self, period: str = "10y") -> Dict[str, int]:
        """抓取並儲存所有三大指數資料"""
        result = {}
        
        for symbol in INDEX_SYMBOLS.keys():
            logger.info(f"抓取指數資料: {symbol}")
            df = yahoo_finance.get_index_data(symbol, period=period)
            
            if df is not None:
                count = self.save_index_data(df, symbol)
                result[symbol] = count
                logger.info(f"{symbol} 新增 {count} 筆資料")
            else:
                result[symbol] = 0
                logger.warning(f"{symbol} 抓取失敗")
        
        return result
    
    # ==================== 市場情緒 ====================
    
    def get_latest_sentiment(self) -> Dict[str, Any]:
        """
        取得最新的市場情緒
        
        🆕 優化版：
        1. 優先從內存快取讀取（60 秒有效）
        2. 只在快取過期時才查詢 DB
        """
        # 嘗試從快取取得
        cached = _memory_cache.get("sentiment", SENTIMENT_CACHE_SECONDS)
        if cached is not None:
            logger.debug("📦 情緒快取命中 (memory)")
            return cached
        
        # 快取未命中，查詢 DB
        logger.debug("📦 情緒快取未命中，查詢 DB")
        result = {}
        
        for market in ["stock", "crypto"]:
            try:
                stmt = (
                    select(MarketSentiment)
                    .where(MarketSentiment.market == market)
                    .order_by(desc(MarketSentiment.date))
                    .limit(1)
                )
                latest = self.db.execute(stmt).scalar_one_or_none()
                
                if latest:
                    result[market] = latest.to_dict()
                    logger.debug(f"📦 情緒 DB: {market} = {latest.value}")
                else:
                    logger.warning(f"⚠️ 情緒 {market} 無快取資料")
                    result[market] = {
                        "market": market,
                        "value": None,
                        "label": "無資料",
                        "date": None,
                    }
            except Exception as e:
                logger.error(f"讀取情緒 {market} 失敗: {e}")
                result[market] = {
                    "market": market,
                    "value": None,
                    "label": "錯誤",
                    "date": None,
                }
        
        # 寫入內存快取
        _memory_cache.set("sentiment", result)
        return result

    def get_sentiment_history(
        self,
        market: str,
        days: int = 365,
    ) -> List[Dict[str, Any]]:
        """取得情緒歷史資料（快取 5 分鐘）"""
        cache_key = f"sentiment_history_{market}_{days}"
        cached = _memory_cache.get(cache_key, 300)
        if cached is not None:
            logger.debug(f"📦 情緒歷史快取命中: {market} {days}天")
            return cached
        
        start_date = date.today() - timedelta(days=days)
        
        stmt = (
            select(MarketSentiment)
            .where(
                and_(
                    MarketSentiment.market == market,
                    MarketSentiment.date >= start_date,
                )
            )
            .order_by(MarketSentiment.date)
        )
        results = self.db.execute(stmt).scalars().all()
        history = [r.to_dict() for r in results]
        
        _memory_cache.set(cache_key, history)
        return history
    
    def save_sentiment(
        self,
        market: str,
        value: int,
        target_date: Optional[date] = None,
    ) -> bool:
        """儲存市場情緒資料"""
        if target_date is None:
            target_date = date.today()
        
        stmt = select(MarketSentiment).where(
            and_(
                MarketSentiment.market == market,
                MarketSentiment.date == target_date,
            )
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        
        classification = MarketSentiment.get_classification(value)
        
        if existing:
            existing.value = value
            existing.classification = classification
        else:
            sentiment = MarketSentiment(
                date=target_date,
                market=market,
                value=value,
                classification=classification,
            )
            self.db.add(sentiment)
        
        self.db.commit()
        _memory_cache.clear("sentiment")
        return True
    
    def fetch_and_save_crypto_history(self, days: int = 365) -> int:
        """抓取並儲存幣圈情緒歷史資料"""
        logger.info(f"抓取幣圈情緒歷史: {days} 天")
        history = fear_greed.get_crypto_fear_greed_history(days)
        
        count = 0
        for item in history:
            try:
                target_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
                
                stmt = select(MarketSentiment).where(
                    and_(
                        MarketSentiment.market == "crypto",
                        MarketSentiment.date == target_date,
                    )
                )
                existing = self.db.execute(stmt).scalar_one_or_none()
                
                if not existing:
                    sentiment = MarketSentiment(
                        date=target_date,
                        market="crypto",
                        value=item["value"],
                        classification=item["classification"],
                    )
                    self.db.add(sentiment)
                    count += 1
            except Exception as e:
                logger.error(f"儲存情緒資料失敗: {e}")
        
        self.db.commit()
        _memory_cache.clear("sentiment")
        logger.info(f"幣圈情緒歷史新增 {count} 筆")
        return count
    
    def update_today_sentiment(self) -> Dict[str, bool]:
        """更新今日的市場情緒"""
        result = {}
        
        stock_data = fear_greed.get_stock_fear_greed()
        if stock_data and not stock_data.get("is_fallback"):
            result["stock"] = self.save_sentiment("stock", stock_data["value"])
        else:
            result["stock"] = False
        
        crypto_data = fear_greed.get_crypto_fear_greed()
        if crypto_data and not crypto_data.get("is_fallback"):
            result["crypto"] = self.save_sentiment("crypto", crypto_data["value"])
        else:
            result["crypto"] = False
        
        return result
    
    # ==================== 配息資料 ====================
    
    def save_dividends(self, df: pd.DataFrame) -> int:
        """儲存配息資料"""
        if df is None or df.empty:
            return 0
        
        count = 0
        for _, row in df.iterrows():
            stmt = select(DividendHistory).where(
                and_(
                    DividendHistory.symbol == row["symbol"],
                    DividendHistory.date == row["date"],
                )
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if not existing:
                dividend = DividendHistory(
                    symbol=row["symbol"],
                    date=row["date"],
                    amount=row["amount"],
                )
                self.db.add(dividend)
                count += 1
        
        self.db.commit()
        return count
    
    def fetch_and_save_dividends(self, symbol: str, period: str = "10y") -> int:
        """抓取並儲存配息資料"""
        logger.info(f"抓取配息資料: {symbol}")
        df = yahoo_finance.get_dividends(symbol, period=period)
        
        if df is not None:
            count = self.save_dividends(df)
            logger.info(f"{symbol} 配息新增 {count} 筆")
            return count
        
        return 0
    
    def get_dividends(
        self,
        symbol: str,
        years: int = 10,
    ) -> List[Dict[str, Any]]:
        """取得配息歷史"""
        start_date = date.today() - timedelta(days=years * 365)
        
        stmt = (
            select(DividendHistory)
            .where(
                and_(
                    DividendHistory.symbol == symbol.upper(),
                    DividendHistory.date >= start_date,
                )
            )
            .order_by(DividendHistory.date)
        )
        results = self.db.execute(stmt).scalars().all()
        
        return [r.to_dict() for r in results]
