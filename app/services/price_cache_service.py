"""
價格快取服務 - 優化版

🔧 優化版本 - 2026-04-06
- 支援按市場分別更新 (market='tw'/'us'/'crypto')
- 智能快取判斷
- 減少不必要的 API 調用
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
import yfinance as yf

from app.models.price_cache import StockPriceCache
from app.models.watchlist import Watchlist

logger = logging.getLogger(__name__)

# 台北時區
TW_TZ = timezone(timedelta(hours=8))

# 台股名稱對照表（常用）
TAIWAN_STOCK_NAMES = {
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2308": "台達電",
    "2881": "富邦金",
    "2882": "國泰金",
    "2884": "玉山金",
    "2891": "中信金",
    "2303": "聯電",
    "3711": "日月光投控",
    "2412": "中華電",
    "1301": "台塑",
    "1303": "南亞",
    "1326": "台化",
    "2886": "兆豐金",
    "2892": "第一金",
    "5880": "合庫金",
    "2357": "華碩",
    "2382": "廣達",
    "3034": "聯詠",
    # 更多可以從 taiwan_stocks.py 導入
}


def is_tw_market_open() -> bool:
    """判斷台股是否開盤"""
    now = datetime.now(TW_TZ)
    if now.weekday() >= 5:
        return False
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=13, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def is_us_market_open() -> bool:
    """判斷美股是否開盤（21:30-05:00 台北時間）"""
    now = datetime.now(TW_TZ)
    if now.weekday() == 6:
        return False
    if now.weekday() == 5 and now.hour >= 5:
        return False
    hour = now.hour
    minute = now.minute
    if hour >= 21 and minute >= 30:
        return True
    if hour >= 22:
        return True
    if hour < 5:
        return True
    return False


def is_market_open_for_symbol(symbol: str) -> bool:
    """判斷特定股票的市場是否開盤"""
    symbol = symbol.upper()
    if symbol in ("BTC", "ETH"):
        return True  # 加密貨幣 24 小時
    if symbol.endswith((".TW", ".TWO")):
        return is_tw_market_open()
    return is_us_market_open()


class PriceCacheService:
    """價格快取服務 - 優化版"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tracked_symbols(self) -> Dict[str, List[str]]:
        """取得所有被追蹤的 symbol（去重，按市場分類）"""
        stmt = select(distinct(Watchlist.symbol))
        result = self.db.execute(stmt)
        symbols = [row[0] for row in result.all()]
        
        tw_stocks = []
        us_stocks = []
        crypto = []
        
        for symbol in symbols:
            if symbol.upper() in ("BTC", "ETH"):
                crypto.append(symbol)
            elif symbol.endswith((".TW", ".TWO")):
                tw_stocks.append(symbol)
            else:
                us_stocks.append(symbol)
        
        logger.info(f"追蹤: 台股 {len(tw_stocks)}, 美股 {len(us_stocks)}, 加密貨幣 {len(crypto)}")
        return {"tw_stocks": tw_stocks, "us_stocks": us_stocks, "crypto": crypto}
    
    def batch_update_stock_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """批次更新股票價格（含 MA20）"""
        if not symbols:
            return {"updated": 0, "failed": []}
        
        result = {"updated": 0, "failed": []}
        logger.info(f"開始更新 {len(symbols)} 支股票...")
        
        try:
            # 使用 yfinance 批次取得
            tickers = yf.Tickers(" ".join(symbols))
            
            for symbol in symbols:
                try:
                    ticker = tickers.tickers.get(symbol)
                    if not ticker:
                        result["failed"].append(symbol)
                        continue
                    
                    # 取得歷史數據（用於計算 MA20）
                    hist = ticker.history(period="1mo")
                    
                    if hist.empty:
                        # 嘗試用 info
                        info = ticker.info
                        if not info:
                            result["failed"].append(symbol)
                            continue
                        
                        price = info.get("regularMarketPrice") or info.get("currentPrice")
                        prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
                        volume = info.get("regularMarketVolume") or info.get("volume")
                        name = info.get("shortName") or info.get("longName") or ""
                        ma20 = None
                    else:
                        # 從歷史數據取得
                        price = float(hist['Close'].iloc[-1])
                        prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else None
                        volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else None
                        
                        # 計算 MA20
                        ma20 = None
                        if len(hist) >= 20:
                            ma20 = float(hist['Close'].tail(20).mean())
                        
                        # 取得名稱
                        info = ticker.info
                        name = ""
                        if info:
                            name = info.get("shortName") or info.get("longName") or ""
                    
                    if price is None:
                        result["failed"].append(symbol)
                        continue
                    
                    # 台股名稱
                    if not name and symbol.endswith((".TW", ".TWO")):
                        stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                        name = TAIWAN_STOCK_NAMES.get(stock_code, "")
                    
                    # 計算漲跌
                    change = None
                    change_pct = None
                    if prev_close and prev_close > 0:
                        change = price - prev_close
                        change_pct = (change / prev_close) * 100
                    
                    # 更新快取（含 MA20）
                    self._upsert_cache(
                        symbol=symbol,
                        name=name,
                        price=price,
                        prev_close=prev_close,
                        change=change,
                        change_pct=change_pct,
                        volume=volume,
                        asset_type="stock",
                        ma20=ma20,
                    )
                    result["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"更新 {symbol} 失敗: {e}")
                    result["failed"].append(symbol)
            
            self.db.commit()
            logger.info(f"股票更新完成: 成功 {result['updated']}, 失敗 {len(result['failed'])}")
            
        except Exception as e:
            logger.error(f"批次更新失敗: {e}")
        
        return result
    
    def batch_update_crypto_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """批次更新加密貨幣價格"""
        if not symbols:
            return {"updated": 0, "failed": []}
        
        result = {"updated": 0, "failed": []}
        
        try:
            from app.data_sources.coingecko import coingecko
            
            for symbol in symbols:
                try:
                    data = coingecko.get_price(symbol)
                    if not data or data.get("price") is None:
                        result["failed"].append(symbol)
                        continue
                    
                    self._upsert_cache(
                        symbol=symbol,
                        name=data.get("name", symbol),
                        price=data["price"],
                        prev_close=None,
                        change=None,
                        change_pct=data.get("change_24h"),
                        volume=data.get("volume_24h"),
                        asset_type="crypto",
                        ma20=None,
                    )
                    result["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"更新 {symbol} 失敗: {e}")
                    result["failed"].append(symbol)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"加密貨幣更新失敗: {e}")
        
        return result
    
    def _upsert_cache(self, symbol, name, price, prev_close, change, change_pct, volume, asset_type, ma20=None):
        """更新或新增快取（含 MA20）"""
        cache = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol
        ).first()
        
        if cache:
            cache.name = name or cache.name
            cache.price = price
            cache.prev_close = prev_close
            cache.change = change
            cache.change_pct = change_pct
            cache.volume = volume
            if ma20 is not None:
                cache.ma20 = ma20
            cache.updated_at = datetime.now()
        else:
            cache = StockPriceCache(
                symbol=symbol,
                name=name,
                price=price,
                prev_close=prev_close,
                change=change,
                change_pct=change_pct,
                ma20=ma20,
                volume=volume,
                asset_type=asset_type,
            )
            self.db.add(cache)
    
    # ============================================================
    # 🆕 智慧快取查詢（效能優化核心）
    # ============================================================
    
    def get_cached_price(self, symbol: str, max_age_minutes: int = 5) -> Optional[dict]:
        """從快取取得股票價格"""
        cache = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol.upper()
        ).first()
        
        if not cache:
            logger.debug(f"快取未命中: {symbol}")
            return None
        
        if cache.updated_at:
            age = datetime.now() - cache.updated_at
            if age > timedelta(minutes=max_age_minutes):
                logger.info(f"快取過期: {symbol} (已 {age.total_seconds()/60:.1f} 分鐘)")
                return None
        
        logger.info(f"📦 快取命中: {symbol}")
        return self._cache_to_dict(cache)
    
    def get_cached_price_smart(self, symbol: str) -> Tuple[Optional[dict], bool]:
        """
        🆕 智慧取得快取價格（效能優化版）
        
        Returns:
            (快取資料 dict 或 None, 是否需要更新)
        """
        symbol = symbol.upper()
        
        cache = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol
        ).first()
        
        # 無資料
        if not cache:
            logger.debug(f"⚡ 快取未命中: {symbol}")
            return None, True
        
        cache_data = self._cache_to_dict(cache)
        
        # 判斷市場是否開盤
        market_open = is_market_open_for_symbol(symbol)
        
        # 非開盤時間 → 直接使用快取
        if not market_open:
            logger.info(f"⚡ 非開盤時間，直接使用快取: {symbol}")
            return cache_data, False
        
        # 開盤時間，檢查快取年齡
        if cache.updated_at:
            age = datetime.now() - cache.updated_at
            age_minutes = age.total_seconds() / 60
            
            if age_minutes < 5:
                logger.info(f"⚡ 快取有效 ({age_minutes:.1f}分鐘): {symbol}")
                return cache_data, False
            
            logger.info(f"⚡ 快取過期但先返回 ({age_minutes:.1f}分鐘): {symbol}")
            return cache_data, True
        
        return cache_data, True
    
    def get_cached_prices_batch(self, symbols: List[str]) -> Dict[str, dict]:
        """🆕 批量取得快取價格"""
        if not symbols:
            return {}
        
        caches = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol.in_([s.upper() for s in symbols])
        ).all()
        
        return {
            cache.symbol: self._cache_to_dict(cache)
            for cache in caches
        }
    
    def _cache_to_dict(self, cache: StockPriceCache) -> dict:
        """將快取物件轉換為 dict"""
        return {
            "symbol": cache.symbol,
            "name": cache.name,
            "price": float(cache.price) if cache.price else None,
            "prev_close": float(cache.prev_close) if cache.prev_close else None,
            "change": float(cache.change) if cache.change else None,
            "change_pct": float(cache.change_pct) if cache.change_pct else None,
            "volume": int(cache.volume) if cache.volume else None,
            "ma20": float(cache.ma20) if cache.ma20 else None,
            "updated_at": cache.updated_at.isoformat() if cache.updated_at else None,
            "asset_type": cache.asset_type,
        }
    
    # ============================================================
    # 🆕 優化版更新方法（支援按市場更新）
    # ============================================================
    
    def update_all(self, force: bool = False, market: str = None) -> Dict[str, Any]:
        """
        更新所有追蹤的價格
        
        🆕 新增參數:
        - market: 'tw' / 'us' / 'crypto' / None (全部)
        - force=True: 強制更新所有
        - force=False: 只更新開盤中的市場
        """
        logger.info("=" * 40)
        logger.info(f"開始更新價格快取 (force={force}, market={market})")
        logger.info(f"時間: {datetime.now()}")
        
        tw_open = is_tw_market_open()
        us_open = is_us_market_open()
        logger.info(f"台股: {'開盤' if tw_open else '收盤'}, 美股: {'開盤' if us_open else '收盤'}")
        logger.info("=" * 40)
        
        tracked = self.get_all_tracked_symbols()
        
        result = {
            "tw_stocks": {"updated": 0, "failed": [], "skipped": False},
            "us_stocks": {"updated": 0, "failed": [], "skipped": False},
            "crypto": {"updated": 0, "failed": []},
            "timestamp": datetime.now().isoformat(),
            "market_filter": market,
        }
        
        # 🆕 根據 market 參數過濾
        should_update_tw = (market is None or market == 'tw') and (force or tw_open)
        should_update_us = (market is None or market == 'us') and (force or us_open)
        should_update_crypto = (market is None or market == 'crypto')
        
        # 台股
        if should_update_tw:
            if tracked["tw_stocks"]:
                result["tw_stocks"] = self.batch_update_stock_prices(tracked["tw_stocks"])
        else:
            result["tw_stocks"]["skipped"] = True
            logger.info("台股: 跳過更新")
        
        # 美股
        if should_update_us:
            if tracked["us_stocks"]:
                result["us_stocks"] = self.batch_update_stock_prices(tracked["us_stocks"])
        else:
            result["us_stocks"]["skipped"] = True
            logger.info("美股: 跳過更新")
        
        # 加密貨幣（24小時）
        if should_update_crypto:
            if tracked["crypto"]:
                result["crypto"] = self.batch_update_crypto_prices(tracked["crypto"])
        else:
            logger.info("加密貨幣: 跳過更新")
        
        result["total_updated"] = (
            result["tw_stocks"].get("updated", 0) +
            result["us_stocks"].get("updated", 0) +
            result["crypto"].get("updated", 0)
        )
        
        logger.info(f"更新完成: 共 {result['total_updated']} 筆")
        return result
    
    # ============================================================
    # 🆕 成本監控輔助方法
    # ============================================================
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """取得快取統計資訊"""
        from sqlalchemy import func
        
        total = self.db.query(func.count(StockPriceCache.id)).scalar()
        
        # 最近更新時間
        latest = self.db.query(func.max(StockPriceCache.updated_at)).scalar()
        
        # 按類型統計
        by_type = self.db.query(
            StockPriceCache.asset_type,
            func.count(StockPriceCache.id)
        ).group_by(StockPriceCache.asset_type).all()
        
        return {
            "total_cached": total,
            "latest_update": latest.isoformat() if latest else None,
            "by_type": {t: c for t, c in by_type},
        }
