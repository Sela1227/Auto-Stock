"""
åƒ¹æ ¼å¿«å–è¼”åŠ©æ¨¡çµ„

æŸ¥è©¢è‚¡ç¥¨æ™‚è‡ªå‹•å°‡çµæžœå¯«å…¥å¿«å–
- æŸ¥è©¢éŽçš„è‚¡ç¥¨æœƒè¢«å¿«å–
- ä½†ä¸æœƒè‡ªå‹•æ›´æ–°ï¼ˆåªæœ‰è¿½è¹¤æ¸…å–®æ‰æœƒï¼‰
- æ”¯æ´ MA20 æ¬„ä½ç”¨æ–¼æŽ’åº
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
    å°‡æŸ¥è©¢çµæžœå¯«å…¥å¿«å–ï¼ˆèƒŒæ™¯åŸ·è¡Œï¼Œä¸å½±éŸ¿ä¸»æµç¨‹ï¼‰
    
    Args:
        symbol: è‚¡ç¥¨ä»£ç¢¼ (å¦‚ 0050.TW, AAPL)
        name: è‚¡ç¥¨åç¨±
        price: æœ€æ–°åƒ¹æ ¼
        prev_close: å‰æ”¶ç›¤åƒ¹
        change: æ¼²è·Œé‡‘é¡
        change_pct: æ¼²è·Œå¹… %
        ma20: 20æ—¥å‡ç·šï¼ˆç”¨æ–¼æŽ’åºï¼‰
        volume: æˆäº¤é‡
        asset_type: è³‡ç”¢é¡žåž‹ (stock/crypto)
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
                # æ›´æ–°ç¾æœ‰å¿«å–
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
                logger.debug(f"æ›´æ–°å¿«å–: {symbol} = {price}, MA20={ma20}")
            else:
                # æ–°å¢žå¿«å–
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
                logger.info(f"æ–°å¢žå¿«å–: {symbol} = {price}, MA20={ma20}")
            
            db.commit()
        finally:
            db.close()
    except Exception as e:
        # å¿«å–å¤±æ•—ä¸å½±éŸ¿ä¸»æµç¨‹
        logger.warning(f"å¿«å– {symbol} å¤±æ•—ï¼ˆä¸å½±éŸ¿æŸ¥è©¢ï¼‰: {e}")


def cache_crypto_price(
    symbol: str,
    name: str,
    price: float,
    change_pct: Optional[float] = None,
    volume: Optional[int] = None
):
    """
    å¿«å–åŠ å¯†è²¨å¹£åƒ¹æ ¼ï¼ˆåŠ å¯†è²¨å¹£ä¸éœ€è¦ MA20ï¼‰
    """
    cache_stock_price(
        symbol=symbol,
        name=name,
        price=price,
        change_pct=change_pct,
        volume=volume,
        asset_type="crypto"
    )