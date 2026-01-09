"""
價格快取服務
負責批次更新追蹤股票的即時價格

排程邏輯：
- 台股開盤 (09:00-13:30)：每 10 分鐘更新台股
- 美股開盤 (21:30-04:00 夏令 / 22:30-05:00 冬令)：每 10 分鐘更新美股
- 收盤後：不更新（使用收盤價）
- 加密貨幣：24 小時每 10 分鐘更新
"""
import logging
from datetime import datetime, time
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
import yfinance as yf

from app.models.price_cache import StockPriceCache
from app.models.watchlist import Watchlist
from app.data_sources.yahoo_finance import yahoo_finance, TAIWAN_STOCK_NAMES

logger = logging.getLogger(__name__)


# ============================================================
# 開盤時間設定（台灣時間）
# ============================================================

# 台股：09:00 - 13:30
TW_MARKET_OPEN = time(9, 0)
TW_MARKET_CLOSE = time(13, 30)

# 美股：夏令 21:30-04:00，冬令 22:30-05:00
# 簡化處理：用 21:30-05:00 涵蓋兩種情況
US_MARKET_OPEN_EVENING = time(21, 30)   # 晚上開盤
US_MARKET_CLOSE_MORNING = time(5, 0)    # 凌晨收盤


def is_tw_market_open() -> bool:
    """判斷台股是否開盤（台灣時間）"""
    now = datetime.now().time()
    # 週一到週五
    weekday = datetime.now().weekday()
    if weekday >= 5:  # 週六日
        return False
    return TW_MARKET_OPEN <= now <= TW_MARKET_CLOSE


def is_us_market_open() -> bool:
    """判斷美股是否開盤（台灣時間）"""
    now = datetime.now().time()
    # 週一到週五（注意：台灣週六凌晨對應美股週五）
    weekday = datetime.now().weekday()
    
    # 晚上 21:30 後（週一到週五）
    if weekday < 5 and now >= US_MARKET_OPEN_EVENING:
        return True
    
    # 凌晨 05:00 前（週二到週六，對應美股週一到週五）
    if weekday > 0 and now <= US_MARKET_CLOSE_MORNING:
        return True
    
    # 週六凌晨（對應美股週五）
    if weekday == 5 and now <= US_MARKET_CLOSE_MORNING:
        return True
    
    return False


def get_market_status() -> Dict[str, bool]:
    """取得各市場開盤狀態"""
    return {
        "tw_open": is_tw_market_open(),
        "us_open": is_us_market_open(),
        "crypto_open": True,  # 加密貨幣 24 小時
    }


class PriceCacheService:
    """價格快取服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tracked_symbols(self) -> Dict[str, List[str]]:
        """
        取得所有被追蹤的 symbol（去重，按市場分類）
        
        Returns:
            {
                "tw_stocks": ["0050.TW", "2330.TW", ...],   # 台股
                "us_stocks": ["AAPL", "TSLA", ...],         # 美股
                "crypto": ["BTC", "ETH", ...]              # 加密貨幣
            }
        """
        stmt = select(
            distinct(Watchlist.symbol), 
            Watchlist.asset_type
        )
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
        
        logger.info(f"追蹤的標的: 台股 {len(tw_stocks)} 支, 美股 {len(us_stocks)} 支, 加密貨幣 {len(crypto)} 種")
        return {
            "tw_stocks": tw_stocks,
            "us_stocks": us_stocks,
            "crypto": crypto,
        }
    
    def batch_update_stock_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """
        批次更新股票價格（使用 yfinance 批次功能）
        
        Args:
            symbols: 股票代號列表
            
        Returns:
            {"updated": 10, "failed": ["XXX"], "errors": [...]}
        """
        if not symbols:
            return {"updated": 0, "failed": [], "errors": []}
        
        result = {
            "updated": 0,
            "failed": [],
            "errors": [],
        }
        
        logger.info(f"開始批次更新 {len(symbols)} 支股票價格...")
        
        try:
            # 使用 yfinance 的 Tickers 批次取得資料
            tickers = yf.Tickers(" ".join(symbols))
            
            for symbol in symbols:
                try:
                    ticker = tickers.tickers.get(symbol)
                    if not ticker:
                        result["failed"].append(symbol)
                        continue
                    
                    # 取得即時報價
                    info = ticker.info
                    
                    if not info:
                        result["failed"].append(symbol)
                        continue
                    
                    # 取得價格資訊
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
                    
                    # 台股名稱補充
                    if not name and symbol.endswith((".TW", ".TWO")):
                        stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                        name = TAIWAN_STOCK_NAMES.get(stock_code, "")
                    
                    # 取得成交量
                    volume = info.get("regularMarketVolume") or info.get("volume")
                    
                    # 更新或新增快取
                    self._upsert_cache(
                        symbol=symbol,
                        name=name,
                        price=price,
                        prev_close=prev_close,
                        change=change,
                        change_pct=change_pct,
                        volume=volume,
                        asset_type="stock",
                    )
                    
                    result["updated"] += 1
                    logger.debug(f"{symbol}: ${price:.2f} ({change_pct:+.2f}%)" if change_pct else f"{symbol}: ${price:.2f}")
                    
                except Exception as e:
                    logger.error(f"更新 {symbol} 失敗: {e}")
                    result["failed"].append(symbol)
                    result["errors"].append(f"{symbol}: {str(e)}")
            
            self.db.commit()
            logger.info(f"批次更新完成: 成功 {result['updated']}, 失敗 {len(result['failed'])}")
            
        except Exception as e:
            logger.error(f"批次更新失敗: {e}")
            result["errors"].append(str(e))
        
        return result
    
    def batch_update_crypto_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """
        批次更新加密貨幣價格
        
        Args:
            symbols: 加密貨幣代號列表 (BTC, ETH)
            
        Returns:
            {"updated": 2, "failed": [], "errors": []}
        """
        if not symbols:
            return {"updated": 0, "failed": [], "errors": []}
        
        result = {
            "updated": 0,
            "failed": [],
            "errors": [],
        }
        
        logger.info(f"開始更新 {len(symbols)} 種加密貨幣價格...")
        
        try:
            from app.data_sources.coingecko import coingecko
            
            for symbol in symbols:
                try:
                    data = coingecko.get_price(symbol)
                    
                    if not data:
                        result["failed"].append(symbol)
                        continue
                    
                    price = data.get("price")
                    change_24h = data.get("change_24h")
                    name = data.get("name", symbol)
                    
                    if price is None:
                        result["failed"].append(symbol)
                        continue
                    
                    self._upsert_cache(
                        symbol=symbol,
                        name=name,
                        price=price,
                        prev_close=None,
                        change=None,
                        change_pct=change_24h,
                        volume=data.get("volume_24h"),
                        asset_type="crypto",
                    )
                    
                    result["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"更新 {symbol} 失敗: {e}")
                    result["failed"].append(symbol)
                    result["errors"].append(f"{symbol}: {str(e)}")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"加密貨幣批次更新失敗: {e}")
            result["errors"].append(str(e))
        
        return result
    
    def _upsert_cache(
        self,
        symbol: str,
        name: str,
        price: float,
        prev_close: Optional[float],
        change: Optional[float],
        change_pct: Optional[float],
        volume: Optional[int],
        asset_type: str,
    ):
        """更新或新增快取記錄"""
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
            cache.asset_type = asset_type
            cache.updated_at = datetime.now()
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
            )
            self.db.add(cache)
    
    def get_cached_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        從快取取得價格（給 API 用）
        
        Args:
            symbols: 要查詢的代號列表
            
        Returns:
            {
                "0050.TW": {"price": 150.5, "change_pct": 1.2, ...},
                "AAPL": {"price": 180.0, "change_pct": -0.5, ...},
            }
        """
        if not symbols:
            return {}
        
        stmt = select(StockPriceCache).where(
            StockPriceCache.symbol.in_(symbols)
        )
        results = self.db.execute(stmt).scalars().all()
        
        return {r.symbol: r.to_dict() for r in results}
    
    def get_all_cached_prices(self) -> List[Dict]:
        """取得所有快取的價格"""
        stmt = select(StockPriceCache).order_by(StockPriceCache.symbol)
        results = self.db.execute(stmt).scalars().all()
        return [r.to_dict() for r in results]
    
    def update_all_tracked_prices(self, force: bool = False) -> Dict[str, Any]:
        """
        更新所有被追蹤的股票和加密貨幣價格
        這是排程任務會呼叫的主函數
        
        根據開盤時間決定更新哪些市場：
        - 台股開盤 (09:00-13:30)：更新台股
        - 美股開盤 (21:30-05:00)：更新美股
        - 加密貨幣：24 小時更新
        - force=True：強制更新所有
        
        Returns:
            {
                "tw_stocks": {"updated": 5, "failed": [...]},
                "us_stocks": {"updated": 10, "failed": [...]},
                "crypto": {"updated": 2, "failed": [...]},
                "total_updated": 17,
                "market_status": {"tw_open": True, "us_open": False, ...},
                "timestamp": "2024-01-01T12:00:00"
            }
        """
        logger.info("=" * 50)
        logger.info("開始更新價格快取")
        logger.info(f"時間: {datetime.now()}")
        
        # 檢查各市場開盤狀態
        market_status = get_market_status()
        logger.info(f"市場狀態: 台股={'開盤' if market_status['tw_open'] else '收盤'}, "
                   f"美股={'開盤' if market_status['us_open'] else '收盤'}")
        logger.info("=" * 50)
        
        # 取得所有追蹤的 symbol（按市場分類）
        tracked = self.get_all_tracked_symbols()
        
        result = {
            "tw_stocks": {"updated": 0, "failed": [], "errors": [], "skipped": False},
            "us_stocks": {"updated": 0, "failed": [], "errors": [], "skipped": False},
            "crypto": {"updated": 0, "failed": [], "errors": []},
            "market_status": market_status,
            "timestamp": datetime.now().isoformat(),
        }
        
        # 更新台股（只在開盤時間或強制更新）
        if force or market_status["tw_open"]:
            if tracked["tw_stocks"]:
                logger.info(f"更新台股: {len(tracked['tw_stocks'])} 支")
                tw_result = self.batch_update_stock_prices(tracked["tw_stocks"])
                result["tw_stocks"] = tw_result
        else:
            logger.info("台股收盤，跳過更新")
            result["tw_stocks"]["skipped"] = True
        
        # 更新美股（只在開盤時間或強制更新）
        if force or market_status["us_open"]:
            if tracked["us_stocks"]:
                logger.info(f"更新美股: {len(tracked['us_stocks'])} 支")
                us_result = self.batch_update_stock_prices(tracked["us_stocks"])
                result["us_stocks"] = us_result
        else:
            logger.info("美股收盤，跳過更新")
            result["us_stocks"]["skipped"] = True
        
        # 更新加密貨幣（24 小時）
        if tracked["crypto"]:
            logger.info(f"更新加密貨幣: {len(tracked['crypto'])} 種")
            crypto_result = self.batch_update_crypto_prices(tracked["crypto"])
            result["crypto"] = crypto_result
        
        # 統計總數
        result["total_updated"] = (
            result["tw_stocks"].get("updated", 0) + 
            result["us_stocks"].get("updated", 0) + 
            result["crypto"].get("updated", 0)
        )
        
        logger.info("=" * 50)
        logger.info(f"價格快取更新完成: 共 {result['total_updated']} 筆")
        logger.info(f"  台股: {result['tw_stocks'].get('updated', 0)} {'(跳過)' if result['tw_stocks'].get('skipped') else ''}")
        logger.info(f"  美股: {result['us_stocks'].get('updated', 0)} {'(跳過)' if result['us_stocks'].get('skipped') else ''}")
        logger.info(f"  加密貨幣: {result['crypto'].get('updated', 0)}")
        logger.info("=" * 50)
        
        return result


# 建立全域實例的工廠函數
def get_price_cache_service(db: Session) -> PriceCacheService:
    return PriceCacheService(db)
