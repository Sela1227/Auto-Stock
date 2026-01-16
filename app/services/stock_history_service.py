"""
股票歷史資料快取服務
====================
將查詢過的歷史資料存入 PostgreSQL，大幅減少 Yahoo Finance API 調用

策略：
1. 首次查詢：從 Yahoo 抓取完整資料並存入 DB
2. 同日查詢：直接從 DB 讀取（毫秒級）
3. 隔日查詢：只補抓缺失的日期（1-3 秒）

效能預估：
- 首次查詢：10-30 秒（與原來相同）
- 同日重查：< 500ms（提升 99%）
- 隔日查詢：1-3 秒（提升 90%）
"""
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, delete
from sqlalchemy.dialects.postgresql import insert
import logging

from app.models.stock_price import StockPrice
from app.data_sources.yahoo_finance import yahoo_finance

logger = logging.getLogger(__name__)


class StockHistoryService:
    """股票歷史資料快取服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_stock_history(
        self,
        symbol: str,
        years: int = 10,
        force_refresh: bool = False,
    ) -> Tuple[Optional[pd.DataFrame], str]:
        """
        取得股票歷史資料（優先使用本地快取）
        
        Args:
            symbol: 股票代號
            years: 需要的年數（預設 10 年）
            force_refresh: 是否強制刷新
            
        Returns:
            (DataFrame, source) - source 為 'cache', 'partial', 'yahoo'
            DataFrame 格式與 yahoo_finance.get_stock_history() 相同
        """
        symbol = symbol.upper()
        
        # 強制刷新時，直接從 Yahoo 抓取
        if force_refresh:
            logger.info(f"🔄 強制刷新: {symbol}")
            df = self._fetch_from_yahoo(symbol, years)
            if df is not None and not df.empty:
                self._save_to_db(symbol, df)
            return df, "yahoo"
        
        # 檢查本地快取
        cache_info = self._get_cache_info(symbol)
        
        if cache_info is None:
            # 無快取，首次查詢
            logger.info(f"📥 首次查詢: {symbol}")
            df = self._fetch_from_yahoo(symbol, years)
            if df is not None and not df.empty:
                self._save_to_db(symbol, df)
            return df, "yahoo"
        
        latest_date, record_count = cache_info
        today = date.today()
        
        # 判斷是否需要補抓
        if self._is_cache_fresh(latest_date, today):
            # 快取是最新的，直接返回
            logger.info(f"📦 快取命中: {symbol} ({record_count} 筆，最新 {latest_date})")
            df = self._load_from_db(symbol, years)
            return df, "cache"
        else:
            # 需要補抓缺失的日期
            days_missing = (today - latest_date).days
            logger.info(f"📥 補抓 {symbol}: {days_missing} 天 ({latest_date} → {today})")
            
            # 補抓並合併
            df = self._fetch_incremental(symbol, latest_date, years)
            if df is not None and not df.empty:
                return df, "partial"
            else:
                # 補抓失敗，返回現有資料
                df = self._load_from_db(symbol, years)
                return df, "cache"
    
    def _get_cache_info(self, symbol: str) -> Optional[Tuple[date, int]]:
        """
        取得快取資訊
        
        Returns:
            (最新日期, 記錄數) 或 None
        """
        stmt = select(
            func.max(StockPrice.date),
            func.count(StockPrice.id)
        ).where(StockPrice.symbol == symbol)
        
        result = self.db.execute(stmt).first()
        
        if result and result[0] is not None:
            return result[0], result[1]
        return None
    
    def _is_cache_fresh(self, latest_date: date, today: date) -> bool:
        """
        判斷快取是否足夠新
        
        規則：
        - 有今日資料 → 新鮮
        - 週末時有週五資料 → 新鮮
        - 假日時有最近交易日資料 → 新鮮
        """
        if latest_date >= today:
            return True
        
        # 週末判斷
        if today.weekday() >= 5:  # 週六=5, 週日=6
            # 找到最近的週五
            days_since_friday = today.weekday() - 4
            last_friday = today - timedelta(days=days_since_friday)
            if latest_date >= last_friday:
                return True
        
        # 如果只差一天，可能是假日
        if (today - latest_date).days <= 1:
            return True
        
        return False
    
    def _fetch_from_yahoo(self, symbol: str, years: int) -> Optional[pd.DataFrame]:
        """
        從 Yahoo Finance 抓取完整資料
        返回格式與 yahoo_finance.get_stock_history() 相同
        """
        period = f"{years}y"
        df = yahoo_finance.get_stock_history(symbol, period=period)
        return df
    
    def _fetch_incremental(
        self,
        symbol: str,
        last_date: date,
        years: int
    ) -> Optional[pd.DataFrame]:
        """
        增量抓取：只抓取缺失的日期，然後合併現有資料
        """
        # 計算需要抓取的天數
        today = date.today()
        days_needed = (today - last_date).days + 5  # 多抓幾天確保完整
        
        # 抓取最近的資料
        if days_needed <= 30:
            period = "1mo"
        elif days_needed <= 90:
            period = "3mo"
        elif days_needed <= 180:
            period = "6mo"
        else:
            period = "1y"
        
        logger.info(f"📥 增量抓取 {symbol}: period={period}")
        df_new = yahoo_finance.get_stock_history(symbol, period=period)
        
        if df_new is None or df_new.empty:
            logger.warning(f"⚠️ 增量抓取失敗: {symbol}")
            return None
        
        # 只保留新的資料來存入 DB
        df_to_save = df_new[df_new['date'] > last_date]
        
        if not df_to_save.empty:
            # 存入資料庫
            saved = self._save_to_db(symbol, df_to_save)
            logger.info(f"💾 增量存入: {symbol} ({saved} 筆新資料)")
        
        # 返回完整資料（從 DB 讀取以確保格式一致）
        return self._load_from_db(symbol, years)
    
    def _save_to_db(self, symbol: str, df: pd.DataFrame) -> int:
        """
        存入資料庫（使用 upsert）
        
        Args:
            symbol: 股票代號
            df: yahoo_finance 格式的 DataFrame（有 date 欄位）
        """
        if df is None or df.empty:
            return 0
        
        count = 0
        
        for _, row in df.iterrows():
            # 處理日期
            row_date = row['date']
            if hasattr(row_date, 'date'):
                row_date = row_date.date() if callable(row_date.date) else row_date.date
            elif not isinstance(row_date, date):
                row_date = pd.to_datetime(row_date).date()
            
            row_data = {
                "symbol": symbol,
                "date": row_date,
                "open": float(row['open']) if pd.notna(row.get('open')) else None,
                "high": float(row['high']) if pd.notna(row.get('high')) else None,
                "low": float(row['low']) if pd.notna(row.get('low')) else None,
                "close": float(row['close']) if pd.notna(row.get('close')) else None,
                "volume": int(row['volume']) if pd.notna(row.get('volume')) else 0,
            }
            
            stmt = insert(StockPrice).values(**row_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['symbol', 'date'],
                set_={
                    'open': stmt.excluded.open,
                    'high': stmt.excluded.high,
                    'low': stmt.excluded.low,
                    'close': stmt.excluded.close,
                    'volume': stmt.excluded.volume,
                    'updated_at': func.now(),
                }
            )
            try:
                self.db.execute(stmt)
                count += 1
            except Exception as e:
                logger.warning(f"存入失敗 {symbol} {row_date}: {e}")
        
        self.db.commit()
        logger.info(f"💾 已存入 DB: {symbol} ({count} 筆)")
        return count
    
    def _load_from_db(self, symbol: str, years: int) -> Optional[pd.DataFrame]:
        """
        從資料庫載入歷史資料
        返回格式與 yahoo_finance.get_stock_history() 相同
        """
        start_date = date.today() - timedelta(days=years * 365)
        
        stmt = (
            select(StockPrice)
            .where(
                and_(
                    StockPrice.symbol == symbol,
                    StockPrice.date >= start_date,
                )
            )
            .order_by(StockPrice.date)
        )
        
        results = self.db.execute(stmt).scalars().all()
        
        if not results:
            return None
        
        # 建立與 yahoo_finance 相同格式的 DataFrame
        data = []
        for r in results:
            data.append({
                "date": r.date,  # date 是欄位，不是 index
                "open": float(r.open) if r.open else None,
                "high": float(r.high) if r.high else None,
                "low": float(r.low) if r.low else None,
                "close": float(r.close) if r.close else None,
                "volume": int(r.volume) if r.volume else 0,
                "symbol": symbol,
            })
        
        df = pd.DataFrame(data)
        
        # 計算 adj_close（使用 yahoo_finance 的分割檢測邏輯）
        df = yahoo_finance._detect_and_adjust_splits(df, symbol)
        
        return df
    
    def get_cache_stats(self, symbol: str = None) -> dict:
        """
        取得快取統計資訊
        """
        if symbol:
            info = self._get_cache_info(symbol.upper())
            if info:
                return {
                    "symbol": symbol.upper(),
                    "latest_date": info[0].isoformat(),
                    "record_count": info[1],
                    "is_fresh": self._is_cache_fresh(info[0], date.today()),
                }
            return {"symbol": symbol.upper(), "cached": False}
        
        # 全域統計
        stmt = select(
            StockPrice.symbol,
            func.count(StockPrice.id),
            func.max(StockPrice.date)
        ).group_by(StockPrice.symbol)
        
        results = self.db.execute(stmt).all()
        
        return {
            "total_symbols": len(results),
            "total_records": sum(r[1] for r in results),
            "symbols": [
                {
                    "symbol": r[0],
                    "records": r[1],
                    "latest": r[2].isoformat() if r[2] else None,
                }
                for r in results
            ]
        }
    
    def clear_cache(self, symbol: str = None) -> int:
        """
        清除快取
        
        Args:
            symbol: 指定股票代號，None 表示清除全部
            
        Returns:
            清除的記錄數
        """
        if symbol:
            stmt = delete(StockPrice).where(StockPrice.symbol == symbol.upper())
        else:
            stmt = delete(StockPrice)
        
        result = self.db.execute(stmt)
        self.db.commit()
        
        count = result.rowcount
        logger.info(f"🗑️ 已清除快取: {symbol or '全部'} ({count} 筆)")
        return count


# 便捷函數
def get_stock_history_cached(
    db: Session,
    symbol: str,
    years: int = 10,
    force_refresh: bool = False
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    便捷函數：取得股票歷史資料（帶快取）
    """
    service = StockHistoryService(db)
    return service.get_stock_history(symbol, years, force_refresh)
