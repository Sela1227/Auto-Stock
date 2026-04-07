"""
分析快取服務
V1.05 新增 - 減少 Railway 資源消耗

功能：
1. 股票詳情快取（減少 Yahoo API 調用）
2. 技術指標快取（預計算）
3. 圖表快取（減少 matplotlib CPU）
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.analysis_cache import StockDetailCache, IndicatorCache, ChartCache
from app.services.price_cache_service import is_market_open_for_symbol

logger = logging.getLogger(__name__)


class AnalysisCacheService:
    """分析快取服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 股票詳情快取 ====================
    
    def get_stock_detail_cache(self, symbol: str) -> Optional[Dict]:
        """
        取得股票詳情快取
        - 交易時段：5 分鐘有效
        - 非交易時段：1 小時有效
        """
        cache = self.db.query(StockDetailCache).filter(
            StockDetailCache.symbol == symbol
        ).first()
        
        if not cache:
            return None
        
        # 檢查有效期
        max_age = 5 if is_market_open_for_symbol(symbol) else 60  # 分鐘
        age = (datetime.now() - cache.updated_at).total_seconds() / 60
        
        if age > max_age:
            logger.debug(f"📦 股票詳情快取過期: {symbol} ({age:.1f} 分鐘)")
            return None
        
        logger.debug(f"📦 股票詳情快取命中: {symbol}")
        return cache.to_dict()
    
    def save_stock_detail_cache(self, symbol: str, data: Dict) -> None:
        """儲存股票詳情快取"""
        cache = self.db.query(StockDetailCache).filter(
            StockDetailCache.symbol == symbol
        ).first()
        
        if cache:
            cache.name = data.get("name") or cache.name
            cache.price = data.get("price")
            cache.prev_close = data.get("prev_close")
            cache.open_price = data.get("open")
            cache.high = data.get("high")
            cache.low = data.get("low")
            cache.volume = str(data.get("volume", ""))
            cache.market_cap = data.get("market_cap")
            cache.pe_ratio = data.get("pe_ratio")
            cache.dividend_yield = data.get("dividend_yield")
            cache.fifty_two_week_high = data.get("52_week_high")
            cache.fifty_two_week_low = data.get("52_week_low")
            cache.raw_data = data
            cache.updated_at = datetime.now()
        else:
            cache = StockDetailCache(
                symbol=symbol,
                name=data.get("name"),
                price=data.get("price"),
                prev_close=data.get("prev_close"),
                open_price=data.get("open"),
                high=data.get("high"),
                low=data.get("low"),
                volume=str(data.get("volume", "")),
                market_cap=data.get("market_cap"),
                pe_ratio=data.get("pe_ratio"),
                dividend_yield=data.get("dividend_yield"),
                fifty_two_week_high=data.get("52_week_high"),
                fifty_two_week_low=data.get("52_week_low"),
                raw_data=data,
            )
            self.db.add(cache)
        
        self.db.commit()
        logger.debug(f"💾 股票詳情已快取: {symbol}")
    
    # ==================== 技術指標快取 ====================
    
    def get_indicator_cache(self, symbol: str) -> Optional[Dict]:
        """
        取得技術指標快取
        - 交易時段：10 分鐘有效
        - 非交易時段：24 小時有效（使用收盤資料）
        """
        cache = self.db.query(IndicatorCache).filter(
            IndicatorCache.symbol == symbol
        ).first()
        
        if not cache:
            return None
        
        # 檢查有效期
        max_age = 10 if is_market_open_for_symbol(symbol) else 1440  # 分鐘
        age = (datetime.now() - cache.updated_at).total_seconds() / 60
        
        if age > max_age:
            logger.debug(f"📦 指標快取過期: {symbol} ({age:.1f} 分鐘)")
            return None
        
        logger.debug(f"📦 指標快取命中: {symbol}")
        return cache.to_dict()
    
    def save_indicator_cache(self, symbol: str, data: Dict) -> None:
        """儲存技術指標快取"""
        cache = self.db.query(IndicatorCache).filter(
            IndicatorCache.symbol == symbol
        ).first()
        
        if cache:
            for key, value in data.items():
                if hasattr(cache, key):
                    setattr(cache, key, value)
            cache.updated_at = datetime.now()
        else:
            cache = IndicatorCache(symbol=symbol, **data)
            self.db.add(cache)
        
        self.db.commit()
        logger.debug(f"💾 指標已快取: {symbol}")
    
    def precompute_indicators_for_watchlist(self) -> Dict[str, int]:
        """
        預計算所有追蹤清單股票的技術指標
        由排程調用
        """
        from app.models.watchlist import Watchlist
        from app.data_sources.yahoo_finance import yahoo_finance
        from app.services.indicator_service import IndicatorService
        
        # 取得所有被追蹤的股票
        symbols = self.db.query(Watchlist.symbol).distinct().all()
        symbols = [s[0] for s in symbols]
        
        logger.info(f"⏰ [排程] 預計算 {len(symbols)} 檔股票指標...")
        
        success, failed = 0, 0
        indicator_service = IndicatorService()
        
        for symbol in symbols:
            try:
                # 取得歷史資料
                df = yahoo_finance.get_stock_history(symbol, period="1y")
                if df is None or df.empty:
                    failed += 1
                    continue
                
                # 計算指標
                df = indicator_service.calculate_all_indicators(df)
                latest = df.iloc[-1]
                
                # 計算評分和訊號
                score, signals = indicator_service.generate_score_and_signals(df)
                trend = indicator_service.get_trend(df)
                
                # 儲存快取
                self.save_indicator_cache(symbol, {
                    "price": float(latest.get("close", 0)),
                    "change_pct": float(latest.get("change_pct", 0)) if "change_pct" in latest else None,
                    "ma5": float(latest.get("ma5")) if "ma5" in latest and latest.get("ma5") else None,
                    "ma10": float(latest.get("ma10")) if "ma10" in latest and latest.get("ma10") else None,
                    "ma20": float(latest.get("ma20")) if "ma20" in latest and latest.get("ma20") else None,
                    "ma60": float(latest.get("ma60")) if "ma60" in latest and latest.get("ma60") else None,
                    "ma120": float(latest.get("ma120")) if "ma120" in latest and latest.get("ma120") else None,
                    "ma240": float(latest.get("ma240")) if "ma240" in latest and latest.get("ma240") else None,
                    "rsi": float(latest.get("rsi")) if "rsi" in latest and latest.get("rsi") else None,
                    "macd_dif": float(latest.get("macd_dif")) if "macd_dif" in latest and latest.get("macd_dif") else None,
                    "macd_dem": float(latest.get("macd_dem")) if "macd_dem" in latest and latest.get("macd_dem") else None,
                    "macd_histogram": float(latest.get("macd_histogram")) if "macd_histogram" in latest and latest.get("macd_histogram") else None,
                    "k_value": float(latest.get("k")) if "k" in latest and latest.get("k") else None,
                    "d_value": float(latest.get("d")) if "d" in latest and latest.get("d") else None,
                    "bb_upper": float(latest.get("bb_upper")) if "bb_upper" in latest and latest.get("bb_upper") else None,
                    "bb_middle": float(latest.get("bb_middle")) if "bb_middle" in latest and latest.get("bb_middle") else None,
                    "bb_lower": float(latest.get("bb_lower")) if "bb_lower" in latest and latest.get("bb_lower") else None,
                    "obv": int(latest.get("obv")) if "obv" in latest and latest.get("obv") else None,
                    "score": score,
                    "trend": trend,
                    "signals": [{"type": s.type.value, "indicator": s.indicator, "description": s.description} for s in signals] if signals else [],
                })
                success += 1
                
            except Exception as e:
                logger.error(f"預計算 {symbol} 失敗: {e}")
                failed += 1
        
        logger.info(f"✅ 指標預計算完成: 成功 {success}, 失敗 {failed}")
        return {"success": success, "failed": failed}
    
    # ==================== 圖表快取 ====================
    
    def get_chart_cache(self, symbol: str, days: int) -> Optional[bytes]:
        """
        取得圖表快取
        - 有效期：1 小時
        """
        cache_key = f"{symbol}_{days}"
        cache = self.db.query(ChartCache).filter(
            ChartCache.cache_key == cache_key
        ).first()
        
        if not cache:
            return None
        
        # 檢查有效期（1 小時）
        age = (datetime.now() - cache.updated_at).total_seconds() / 3600
        if age > 1:
            logger.debug(f"📦 圖表快取過期: {cache_key} ({age:.1f} 小時)")
            return None
        
        logger.debug(f"📦 圖表快取命中: {cache_key}")
        return cache.chart_data
    
    def save_chart_cache(self, symbol: str, days: int, chart_data: bytes) -> None:
        """儲存圖表快取"""
        cache_key = f"{symbol}_{days}"
        
        cache = self.db.query(ChartCache).filter(
            ChartCache.cache_key == cache_key
        ).first()
        
        if cache:
            cache.chart_data = chart_data
            cache.updated_at = datetime.now()
        else:
            cache = ChartCache(
                cache_key=cache_key,
                symbol=symbol,
                days=days,
                chart_data=chart_data,
            )
            self.db.add(cache)
        
        self.db.commit()
        logger.debug(f"💾 圖表已快取: {cache_key}")
    
    def clear_expired_caches(self) -> Dict[str, int]:
        """清除過期的快取"""
        now = datetime.now()
        
        # 清除超過 24 小時的股票詳情
        detail_deleted = self.db.query(StockDetailCache).filter(
            StockDetailCache.updated_at < now - timedelta(hours=24)
        ).delete()
        
        # 清除超過 48 小時的指標快取
        indicator_deleted = self.db.query(IndicatorCache).filter(
            IndicatorCache.updated_at < now - timedelta(hours=48)
        ).delete()
        
        # 清除超過 2 小時的圖表快取
        chart_deleted = self.db.query(ChartCache).filter(
            ChartCache.updated_at < now - timedelta(hours=2)
        ).delete()
        
        self.db.commit()
        
        return {
            "detail_deleted": detail_deleted,
            "indicator_deleted": indicator_deleted,
            "chart_deleted": chart_deleted,
        }
