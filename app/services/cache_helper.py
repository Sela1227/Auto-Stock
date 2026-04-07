"""
價格快取輔助模組

查詢股票時自動將結果寫入快取
- 查詢過的股票會被快取
- 但不會自動更新（只有追蹤清單才會）
- 支援 MA20 欄位用於排序
"""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def cache_stock_price(
    symbol: str,
    name: str,
    price: float,
    prev_close: Optional[float] = None,
    change: Optional[float] = None,
    change_pct: Optional[float] = None,
    ma20: Optional[float] = None,
    volume: Optional[int] = None,
    asset_type: str = "stock"
):
    """
    將查詢結果寫入快取（背景執行，不影響主流程）
    
    Args:
        symbol: 股票代碼 (如 0050.TW, AAPL)
        name: 股票名稱
        price: 最新價格
        prev_close: 前收盤價
        change: 漲跌金額
        change_pct: 漲跌幅 %
        ma20: 20日均線（用於排序）
        volume: 成交量
        asset_type: 資產類型 (stock/crypto)
    """
    try:
        from app.database import SessionLocal
        from app.models.price_cache import StockPriceCache
        
        db = SessionLocal()
        try:
            cache = db.query(StockPriceCache).filter(
                StockPriceCache.symbol == symbol
            ).first()
            
            if cache:
                # 更新現有快取
                cache.name = name or cache.name
                cache.price = price
                if prev_close is not None:
                    cache.prev_close = prev_close
                if change is not None:
                    cache.change = change
                if change_pct is not None:
                    cache.change_pct = change_pct
                if ma20 is not None:
                    cache.ma20 = ma20
                if volume is not None:
                    cache.volume = volume
                cache.updated_at = datetime.now()
                logger.debug(f"更新快取: {symbol} = {price}, MA20={ma20}")
            else:
                # 新增快取
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
                db.add(cache)
                logger.info(f"新增快取: {symbol} = {price}, MA20={ma20}")
            
            db.commit()
        finally:
            db.close()
    except Exception as e:
        # 快取失敗不影響主流程
        logger.warning(f"快取 {symbol} 失敗（不影響查詢）: {e}")


def cache_crypto_price(
    symbol: str,
    name: str,
    price: float,
    change_pct: Optional[float] = None,
    volume: Optional[int] = None
):
    """
    快取加密貨幣價格（加密貨幣不需要 MA20）
    """
    cache_stock_price(
        symbol=symbol,
        name=name,
        price=price,
        change_pct=change_pct,
        volume=volume,
        asset_type="crypto"
    )
