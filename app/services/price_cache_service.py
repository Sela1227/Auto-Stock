"""
價格快取服務

🚀 V1.03 精簡版 - 2026-04-07
- 移除冗長的台股名稱對照（移至 taiwan_stock_names.py）
- 簡化程式碼結構
"""
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
import yfinance as yf

from app.models.price_cache import StockPriceCache
from app.models.watchlist import Watchlist
from app.data_sources.taiwan_stock_names import TAIWAN_STOCK_NAMES, get_stock_name

logger = logging.getLogger(__name__)


def is_tw_market_open() -> bool:
    """台股是否開盤（週一至週五 09:00-13:30）"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return time(9, 0) <= now.time() <= time(13, 30)


def is_us_market_open() -> bool:
    """美股是否開盤（台灣時間 21:30-05:00，夏令時 22:30-06:00）"""
    now = datetime.now()
    t = now.time()
    # 簡化判斷：晚上 21:00 後或凌晨 06:00 前
    return t >= time(21, 0) or t <= time(6, 0)


def get_market_status() -> Dict[str, bool]:
    """取得市場狀態"""
    return {
        "tw": is_tw_market_open(),
        "us": is_us_market_open(),
        "crypto": True,  # 24 小時
    }


def get_symbol_market(symbol: str) -> str:
    """判斷股票所屬市場"""
    s = symbol.upper()
    if s.endswith(".TW") or s.endswith(".TWO"):
        return "tw"
    if s in ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "DOT", "AVAX", "MATIC"]:
        return "crypto"
    return "us"


def is_market_open_for_symbol(symbol: str) -> bool:
    """判斷該股票的市場是否開盤"""
    market = get_symbol_market(symbol)
    if market == "tw":
        return is_tw_market_open()
    elif market == "us":
        return is_us_market_open()
    return True  # crypto


class PriceCacheService:
    """價格快取服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tracked_symbols(self) -> Dict[str, List[str]]:
        """取得所有被追蹤的股票代號（按市場分類）"""
        stmt = select(distinct(Watchlist.symbol))
        results = self.db.execute(stmt).scalars().all()
        
        categorized = {"tw": [], "us": [], "crypto": []}
        for symbol in results:
            market = get_symbol_market(symbol)
            categorized[market].append(symbol)
        
        return categorized

    def batch_update_stock_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """批次更新股票價格"""
        if not symbols:
            return {"updated": 0, "failed": 0, "skipped": 0}
        
        updated, failed, skipped = 0, 0, 0
        
        for symbol in symbols:
            if not is_market_open_for_symbol(symbol):
                skipped += 1
                continue
            
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                price = info.get("regularMarketPrice") or info.get("currentPrice")
                prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
                
                if price:
                    change = price - prev_close if prev_close else None
                    change_pct = (change / prev_close * 100) if prev_close and change else None
                    
                    name = info.get("shortName") or info.get("longName") or ""
                    if not name and symbol.endswith((".TW", ".TWO")):
                        name = get_stock_name(symbol)
                    
                    volume = info.get("regularMarketVolume") or info.get("volume")
                    
                    self._upsert_cache(
                        symbol=symbol,
                        name=name,
                        price=price,
                        prev_close=prev_close,
                        change=change,
                        change_pct=change_pct,
                        volume=volume,
                        asset_type="tw_stock" if ".TW" in symbol else "us_stock",
                    )
                    updated += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"更新 {symbol} 失敗: {e}")
                failed += 1
        
        self.db.commit()
        return {"updated": updated, "failed": failed, "skipped": skipped}

    def batch_update_crypto_prices(self, symbols: List[str], force: bool = False) -> Dict[str, Any]:
        """批次更新加密貨幣價格"""
        from app.data_sources.coingecko import coingecko
        
        if not symbols:
            return {"updated": 0, "failed": 0}
        
        updated, failed = 0, 0
        
        for symbol in symbols:
            try:
                data = coingecko.get_coin_price(symbol.lower())
                if data and "price" in data:
                    self._upsert_cache(
                        symbol=symbol.upper(),
                        name=data.get("name", symbol),
                        price=data["price"],
                        prev_close=None,
                        change=data.get("change_24h"),
                        change_pct=data.get("change_pct_24h"),
                        volume=data.get("volume_24h"),
                        asset_type="crypto",
                    )
                    updated += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"更新 {symbol} 失敗: {e}")
                failed += 1
        
        self.db.commit()
        return {"updated": updated, "failed": failed}

    def _upsert_cache(self, symbol, name, price, prev_close, change, change_pct, volume, asset_type, ma20=None):
        """新增或更新快取"""
        existing = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol
        ).first()
        
        if existing:
            existing.name = name or existing.name
            existing.price = price
            existing.prev_close = prev_close
            existing.change = change
            existing.change_pct = change_pct
            existing.volume = volume
            existing.asset_type = asset_type
            if ma20 is not None:
                existing.ma20 = ma20
            existing.updated_at = datetime.now()
        else:
            cache = StockPriceCache(
                symbol=symbol,
                name=name,
                price=price,
                prev_close=prev_close,
                change=change,
                change_pct=change_pct,
                volume=volume,
                asset_type=asset_type,
                ma20=ma20,
            )
            self.db.add(cache)

    def get_cached_price(self, symbol: str, max_age_minutes: int = 5) -> Optional[dict]:
        """取得快取價格（有時效性檢查）"""
        cache = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol
        ).first()
        
        if not cache:
            return None
        
        # 檢查時效
        age = datetime.now() - cache.updated_at
        if age > timedelta(minutes=max_age_minutes):
            return None
        
        return self._cache_to_dict(cache)

    def get_cached_price_smart(self, symbol: str) -> Tuple[Optional[dict], bool]:
        """
        智慧取得快取價格
        Returns: (cache_data, needs_update)
        - 非開盤時間：直接返回快取，不需更新
        - 開盤時間：返回快取 + 標記是否需更新
        """
        cache = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol
        ).first()
        
        if not cache:
            return None, True
        
        # 非開盤時間：直接返回，不需更新
        if not is_market_open_for_symbol(symbol):
            return self._cache_to_dict(cache), False
        
        # 開盤時間：檢查時效
        age = (datetime.now() - cache.updated_at).total_seconds() / 60
        needs_update = age > 5  # 5 分鐘過期
        
        return self._cache_to_dict(cache), needs_update

    def get_cached_prices_batch(self, symbols: List[str]) -> Dict[str, dict]:
        """批次取得快取價格"""
        result = {}
        caches = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol.in_(symbols)
        ).all()
        
        for cache in caches:
            result[cache.symbol] = self._cache_to_dict(cache)
        
        return result

    def _cache_to_dict(self, cache: StockPriceCache) -> dict:
        """快取轉字典"""
        return {
            "symbol": cache.symbol,
            "name": cache.name,
            "price": cache.price,
            "prev_close": cache.prev_close,
            "change": cache.change,
            "change_pct": cache.change_pct,
            "volume": cache.volume,
            "ma20": cache.ma20,
            "updated_at": cache.updated_at.isoformat() if cache.updated_at else None,
        }

    def update_all(self, force: bool = False) -> Dict[str, Any]:
        """更新所有被追蹤的股票"""
        symbols = self.get_all_tracked_symbols()
        
        result = {
            "tw": self.batch_update_stock_prices(symbols["tw"]),
            "us": self.batch_update_stock_prices(symbols["us"]),
            "crypto": self.batch_update_crypto_prices(symbols["crypto"], force),
        }
        
        total = sum(r.get("updated", 0) for r in result.values())
        result["total_updated"] = total
        
        return result
