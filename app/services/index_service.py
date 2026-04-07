"""
æŒ‡æ•¸æœå‹™
========
å››å¤§æŒ‡æ•¸è³‡æ–™æ›´æ–°æœå‹™
- S&P 500 (^GSPC)
- é“ç“Šå·¥æ¥­ (^DJI)
- ç´æ–¯é”å…‹ (^IXIC)
- å°ç£åŠ æ¬Š (^TWII)

è§£æ±º admin.py å¼•ç”¨ index_service ä¸å­˜åœ¨çš„å•é¡Œ
"""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# å››å¤§æŒ‡æ•¸å®šç¾©
INDICES = {
    "^GSPC": {"name": "S&P 500", "name_zh": "æ¨™æ™®500"},
    "^DJI": {"name": "Dow Jones", "name_zh": "é“ç“Šå·¥æ¥­"},
    "^IXIC": {"name": "NASDAQ", "name_zh": "ç´æ–¯é”å…‹"},
    "^TWII": {"name": "TWSE", "name_zh": "å°ç£åŠ æ¬Š"},
}


class IndexService:
    """æŒ‡æ•¸æœå‹™é¡ž"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_index(self, symbol: str, period: str = "5d") -> Dict[str, Any]:
        """
        æ›´æ–°å–®ä¸€æŒ‡æ•¸
        
        Args:
            symbol: æŒ‡æ•¸ä»£è™Ÿ
            period: å–å¾—é€±æœŸ (5d, 1mo, 3mo, 1y, 5y, 10y)
        
        Returns:
            æ›´æ–°çµæžœ
        """
        from app.data_sources.yahoo_finance import yahoo_finance
        from app.models.index_price import IndexPrice
        
        if symbol not in INDICES:
            return {"success": False, "error": f"ç„¡æ•ˆçš„æŒ‡æ•¸ä»£è™Ÿ: {symbol}"}
        
        try:
            logger.info(f"æ›´æ–°æŒ‡æ•¸ {symbol}...")
            
            # å–å¾—æ­·å²è³‡æ–™
            df = yahoo_finance.get_stock_history(symbol, period=period)
            
            if df is None or df.empty:
                return {"success": False, "error": f"ç„¡æ³•å–å¾— {symbol} è³‡æ–™"}
            
            # å„²å­˜åˆ°è³‡æ–™åº«
            count = 0
            for _, row in df.iterrows():
                try:
                    # æª¢æŸ¥æ˜¯å¦å·²å­˜åœ¨
                    existing = self.db.query(IndexPrice).filter(
                        IndexPrice.symbol == symbol,
                        IndexPrice.date == row['date']
                    ).first()
                    
                    if existing:
                        # æ›´æ–°
                        existing.open = float(row['open']) if row['open'] else None
                        existing.high = float(row['high']) if row['high'] else None
                        existing.low = float(row['low']) if row['low'] else None
                        existing.close = float(row['close']) if row['close'] else None
                        existing.volume = int(row['volume']) if row['volume'] else None
                    else:
                        # æ–°å¢ž
                        index_price = IndexPrice(
                            symbol=symbol,
                            date=row['date'],
                            open=float(row['open']) if row['open'] else None,
                            high=float(row['high']) if row['high'] else None,
                            low=float(row['low']) if row['low'] else None,
                            close=float(row['close']) if row['close'] else None,
                            volume=int(row['volume']) if row['volume'] else None,
                        )
                        self.db.add(index_price)
                    count += 1
                except Exception as e:
                    logger.warning(f"å„²å­˜ {symbol} {row['date']} å¤±æ•—: {e}")
                    continue
            
            self.db.commit()
            
            logger.info(f"âœ… {symbol} æ›´æ–°å®Œæˆ: {count} ç­†")
            return {
                "success": True,
                "symbol": symbol,
                "records": count,
            }
            
        except Exception as e:
            logger.error(f"æ›´æ–° {symbol} å¤±æ•—: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def update_all(self, period: str = "5d") -> Dict[str, Any]:
        """
        æ›´æ–°æ‰€æœ‰æŒ‡æ•¸
        
        Returns:
            æ›´æ–°çµæžœå½™ç¸½
        """
        results = []
        errors = []
        
        for symbol in INDICES.keys():
            result = self.update_index(symbol, period)
            if result.get("success"):
                results.append({
                    "symbol": symbol,
                    "records": result.get("records", 0),
                })
            else:
                errors.append({
                    "symbol": symbol,
                    "error": result.get("error"),
                })
        
        return {
            "success": len(errors) == 0,
            "updated": len(results),
            "results": results,
            "errors": errors,
        }


# ============================================================
# å…¨åŸŸå‡½æ•¸ï¼ˆä¾› admin.py ä½¿ç”¨ï¼‰
# ============================================================

def update_all_indices(period: str = "5d") -> Dict[str, Any]:
    """
    æ›´æ–°æ‰€æœ‰å››å¤§æŒ‡æ•¸ï¼ˆå…¨åŸŸå‡½æ•¸ï¼‰
    
    ç”¨æ–¼ admin.py:
        from app.services.index_service import update_all_indices
        result = update_all_indices()
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        service = IndexService(db)
        return service.update_all(period)
    finally:
        db.close()


def update_single_index(symbol: str, period: str = "5d") -> Dict[str, Any]:
    """
    æ›´æ–°å–®ä¸€æŒ‡æ•¸ï¼ˆå…¨åŸŸå‡½æ•¸ï¼‰
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        service = IndexService(db)
        return service.update_index(symbol, period)
    finally:
        db.close()