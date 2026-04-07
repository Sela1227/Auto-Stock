"""
指數服務
========
四大指數資料更新服務
- S&P 500 (^GSPC)
- 道瓊工業 (^DJI)
- 納斯達克 (^IXIC)
- 台灣加權 (^TWII)

解決 admin.py 引用 index_service 不存在的問題
"""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 四大指數定義
INDICES = {
    "^GSPC": {"name": "S&P 500", "name_zh": "標普500"},
    "^DJI": {"name": "Dow Jones", "name_zh": "道瓊工業"},
    "^IXIC": {"name": "NASDAQ", "name_zh": "納斯達克"},
    "^TWII": {"name": "TWSE", "name_zh": "台灣加權"},
}


class IndexService:
    """指數服務類"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def update_index(self, symbol: str, period: str = "5d") -> Dict[str, Any]:
        """
        更新單一指數
        
        Args:
            symbol: 指數代號
            period: 取得週期 (5d, 1mo, 3mo, 1y, 5y, 10y)
        
        Returns:
            更新結果
        """
        from app.data_sources.yahoo_finance import yahoo_finance
        from app.models.index_price import IndexPrice
        
        if symbol not in INDICES:
            return {"success": False, "error": f"無效的指數代號: {symbol}"}
        
        try:
            logger.info(f"更新指數 {symbol}...")
            
            # 取得歷史資料
            df = yahoo_finance.get_stock_history(symbol, period=period)
            
            if df is None or df.empty:
                return {"success": False, "error": f"無法取得 {symbol} 資料"}
            
            # 儲存到資料庫
            count = 0
            for _, row in df.iterrows():
                try:
                    # 檢查是否已存在
                    existing = self.db.query(IndexPrice).filter(
                        IndexPrice.symbol == symbol,
                        IndexPrice.date == row['date']
                    ).first()
                    
                    if existing:
                        # 更新
                        existing.open = float(row['open']) if row['open'] else None
                        existing.high = float(row['high']) if row['high'] else None
                        existing.low = float(row['low']) if row['low'] else None
                        existing.close = float(row['close']) if row['close'] else None
                        existing.volume = int(row['volume']) if row['volume'] else None
                    else:
                        # 新增
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
                    logger.warning(f"儲存 {symbol} {row['date']} 失敗: {e}")
                    continue
            
            self.db.commit()
            
            logger.info(f"✅ {symbol} 更新完成: {count} 筆")
            return {
                "success": True,
                "symbol": symbol,
                "records": count,
            }
            
        except Exception as e:
            logger.error(f"更新 {symbol} 失敗: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    def update_all(self, period: str = "5d") -> Dict[str, Any]:
        """
        更新所有指數
        
        Returns:
            更新結果彙總
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
# 全域函數（供 admin.py 使用）
# ============================================================

def update_all_indices(period: str = "5d") -> Dict[str, Any]:
    """
    更新所有四大指數（全域函數）
    
    用於 admin.py:
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
    更新單一指數（全域函數）
    """
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        service = IndexService(db)
        return service.update_index(symbol, period)
    finally:
        db.close()
