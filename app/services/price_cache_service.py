"""
價格快取服務 - 簡化版
負責批次更新追蹤股票的即時價格
"""
import logging
from datetime import datetime, time
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
import yfinance as yf

from app.models.price_cache import StockPriceCache
from app.models.watchlist import Watchlist

logger = logging.getLogger(__name__)


# 台股名稱對照（常見的）
TAIWAN_STOCK_NAMES = {
    "0050": "元大台灣50",
    "0056": "元大高股息",
    "00878": "國泰永續高股息",
    "00713": "元大台灣高息低波",
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2412": "中華電",
    "2882": "國泰金",
    "2881": "富邦金",
}


# ============================================================
# 開盤時間判斷
# ============================================================

def is_tw_market_open() -> bool:
    """判斷台股是否開盤（週一到週五 09:00-13:30）"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return time(9, 0) <= now.time() <= time(13, 30)


def is_us_market_open() -> bool:
    """判斷美股是否開盤（台灣時間 21:30-05:00）"""
    now = datetime.now()
    weekday = now.weekday()
    current_time = now.time()
    
    # 晚上 21:30 後（週一到週五）
    if weekday < 5 and current_time >= time(21, 30):
        return True
    # 凌晨 05:00 前（週二到週六）
    if weekday > 0 and current_time <= time(5, 0):
        return True
    # 週六凌晨
    if weekday == 5 and current_time <= time(5, 0):
        return True
    return False


# ============================================================
# 價格快取服務
# ============================================================

class PriceCacheService:
    """價格快取服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tracked_symbols(self) -> Dict[str, List[str]]:
        """取得所有被追蹤的 symbol（去重，按市場分類）"""
        stmt = select(distinct(Watchlist.symbol), Watchlist.asset_type)
        results = self.db.execute(stmt).all()
        
        tw_stocks = []
        us_stocks = []
        crypto = []
        
        for symbol, asset_type in results:
            if asset_type == "crypto":
                crypto.append(symbol)
            elif symbol.endswith((".TW", ".TWO")):
                tw_stocks.append(symbol)
            else:
                us_stocks.append(symbol)
        
        logger.info(f"追蹤: 台股 {len(tw_stocks)}, 美股 {len(us_stocks)}, 加密貨幣 {len(crypto)}")
        return {"tw_stocks": tw_stocks, "us_stocks": us_stocks, "crypto": crypto}
    
    def batch_update_stock_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """批次更新股票價格"""
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
                    
                    info = ticker.info
                    if not info:
                        result["failed"].append(symbol)
                        continue
                    
                    # 取得價格
                    price = info.get("regularMarketPrice") or info.get("currentPrice")
                    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
                    
                    if price is None:
                        # 嘗試從歷史資料取得
                        hist = ticker.history(period="2d")
                        if not hist.empty:
                            price = float(hist['Close'].iloc[-1])
                            if len(hist) > 1:
                                prev_close = float(hist['Close'].iloc[-2])
                    
                    if price is None:
                        result["failed"].append(symbol)
                        continue
                    
                    # 計算漲跌
                    change = None
                    change_pct = None
                    if prev_close and prev_close > 0:
                        change = price - prev_close
                        change_pct = (change / prev_close) * 100
                    
                    # 取得名稱
                    name = info.get("shortName") or info.get("longName") or ""
                    if not name and symbol.endswith((".TW", ".TWO")):
                        stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                        name = TAIWAN_STOCK_NAMES.get(stock_code, "")
                    
                    # 更新快取
                    self._upsert_cache(
                        symbol=symbol,
                        name=name,
                        price=price,
                        prev_close=prev_close,
                        change=change,
                        change_pct=change_pct,
                        asset_type="stock",
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
                        asset_type="crypto",
                    )
                    result["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"更新 {symbol} 失敗: {e}")
                    result["failed"].append(symbol)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"加密貨幣更新失敗: {e}")
        
        return result
    
    def _upsert_cache(self, symbol, name, price, prev_close, change, change_pct, asset_type):
        """更新或新增快取"""
        cache = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol
        ).first()
        
        if cache:
            cache.name = name or cache.name
            cache.price = price
            cache.prev_close = prev_close
            cache.change = change
            cache.change_pct = change_pct
            cache.updated_at = datetime.now()
        else:
            cache = StockPriceCache(
                symbol=symbol,
                name=name,
                price=price,
                prev_close=prev_close,
                change=change,
                change_pct=change_pct,
                asset_type=asset_type,
            )
            self.db.add(cache)
    
    def update_all(self, force: bool = False) -> Dict[str, Any]:
        """
        更新所有追蹤的價格
        
        - force=True: 強制更新所有
        - force=False: 只更新開盤中的市場
        """
        logger.info("=" * 40)
        logger.info(f"開始更新價格快取 (force={force})")
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
        }
        
        # 台股
        if force or tw_open:
            if tracked["tw_stocks"]:
                result["tw_stocks"] = self.batch_update_stock_prices(tracked["tw_stocks"])
        else:
            result["tw_stocks"]["skipped"] = True
        
        # 美股
        if force or us_open:
            if tracked["us_stocks"]:
                result["us_stocks"] = self.batch_update_stock_prices(tracked["us_stocks"])
        else:
            result["us_stocks"]["skipped"] = True
        
        # 加密貨幣（24小時）
        if tracked["crypto"]:
            result["crypto"] = self.batch_update_crypto_prices(tracked["crypto"])
        
        result["total_updated"] = (
            result["tw_stocks"].get("updated", 0) +
            result["us_stocks"].get("updated", 0) +
            result["crypto"].get("updated", 0)
        )
        
        logger.info(f"更新完成: 共 {result['total_updated']} 筆")
        return result
