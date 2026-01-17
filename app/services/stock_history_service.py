"""
股票歷史資料快取服務
====================
將查詢過的歷史資料存入 PostgreSQL，大幅減少 Yahoo Finance API 調用

修正版 - 2026-01-16
- 確保資料正確存入 DB
- 確保從 DB 讀取的格式與 yahoo_finance 完全一致
"""
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, delete, text
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
        
        Returns:
            (DataFrame, source) - DataFrame 格式與 yahoo_finance.get_stock_history() 完全相同
        """
        symbol = symbol.upper()
        
        # 強制刷新
        if force_refresh:
            logger.info(f"🔄 強制刷新: {symbol}")
            df = self._fetch_and_save(symbol, years)
            return df, "yahoo"
        
        # 檢查快取
        cache_info = self._get_cache_info(symbol)
        
        if cache_info is None:
            # 無快取，首次查詢
            logger.info(f"📥 首次查詢: {symbol}")
            df = self._fetch_and_save(symbol, years)
            return df, "yahoo"
        
        latest_date, record_count = cache_info
        today = date.today()
        
        # 判斷快取是否足夠新
        if self._is_cache_fresh(latest_date, today):
            logger.info(f"📦 快取命中: {symbol} ({record_count} 筆，最新 {latest_date})")
            df = self._load_from_db(symbol, years)
            return df, "cache"
        else:
            # 需要補抓
            days_missing = (today - latest_date).days
            logger.info(f"📥 補抓 {symbol}: {days_missing} 天")
            df = self._fetch_incremental(symbol, latest_date, years)
            return df, "partial" if df is not None else "cache"
    
    def _get_cache_info(self, symbol: str) -> Optional[Tuple[date, int]]:
        """取得快取資訊"""
        try:
            stmt = select(
                func.max(StockPrice.date),
                func.count(StockPrice.id)
            ).where(StockPrice.symbol == symbol)
            
            result = self.db.execute(stmt).first()
            
            if result and result[0] is not None:
                return result[0], result[1]
        except Exception as e:
            logger.warning(f"查詢快取資訊失敗: {e}")
        return None
    
    def _is_cache_fresh(self, latest_date: date, today: date) -> bool:
        """判斷快取是否足夠新"""
        if latest_date >= today:
            return True
        
        # 週末判斷
        if today.weekday() >= 5:
            days_since_friday = today.weekday() - 4
            last_friday = today - timedelta(days=days_since_friday)
            if latest_date >= last_friday:
                return True
        
        # 允許 1 天延遲（假日）
        if (today - latest_date).days <= 1:
            return True
        
        return False
    
    def _fetch_and_save(self, symbol: str, years: int) -> Optional[pd.DataFrame]:
        """從 Yahoo 抓取並存入 DB"""
        period = f"{years}y"
        df = yahoo_finance.get_stock_history(symbol, period=period)
        
        if df is not None and not df.empty:
            saved = self._save_to_db(symbol, df)
            logger.info(f"💾 已存入 DB: {symbol} ({saved} 筆)")
        
        return df
    
    def _fetch_incremental(self, symbol: str, last_date: date, years: int) -> Optional[pd.DataFrame]:
        """增量抓取"""
        today = date.today()
        days_needed = (today - last_date).days + 5
        
        if days_needed <= 30:
            period = "1mo"
        elif days_needed <= 90:
            period = "3mo"
        else:
            period = "6mo"
        
        df_new = yahoo_finance.get_stock_history(symbol, period=period)
        
        if df_new is not None and not df_new.empty:
            # 只存新資料
            df_to_save = df_new[df_new['date'] > last_date]
            if not df_to_save.empty:
                saved = self._save_to_db(symbol, df_to_save)
                logger.info(f"💾 增量存入: {symbol} ({saved} 筆)")
        
        # 返回完整資料
        return self._load_from_db(symbol, years)
    
    def _save_to_db(self, symbol: str, df: pd.DataFrame) -> int:
        """存入資料庫"""
        if df is None or df.empty:
            return 0
        
        count = 0
        symbol = symbol.upper()
        
        for _, row in df.iterrows():
            try:
                # 處理日期
                row_date = row['date']
                if hasattr(row_date, 'date') and callable(row_date.date):
                    row_date = row_date.date()
                elif not isinstance(row_date, date):
                    row_date = pd.to_datetime(row_date).date()
                
                # 檢查是否已存在
                existing = self.db.query(StockPrice).filter(
                    StockPrice.symbol == symbol,
                    StockPrice.date == row_date
                ).first()
                
                if existing:
                    # 更新
                    existing.open = float(row['open']) if pd.notna(row.get('open')) else None
                    existing.high = float(row['high']) if pd.notna(row.get('high')) else None
                    existing.low = float(row['low']) if pd.notna(row.get('low')) else None
                    existing.close = float(row['close']) if pd.notna(row.get('close')) else None
                    existing.volume = int(row['volume']) if pd.notna(row.get('volume')) else 0
                else:
                    # 新增
                    price = StockPrice(
                        symbol=symbol,
                        date=row_date,
                        open=float(row['open']) if pd.notna(row.get('open')) else None,
                        high=float(row['high']) if pd.notna(row.get('high')) else None,
                        low=float(row['low']) if pd.notna(row.get('low')) else None,
                        close=float(row['close']) if pd.notna(row.get('close')) else None,
                        volume=int(row['volume']) if pd.notna(row.get('volume')) else 0,
                    )
                    self.db.add(price)
                    count += 1
                    
            except Exception as e:
                logger.warning(f"存入失敗 {symbol} {row.get('date')}: {e}")
                continue
        
        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Commit 失敗: {e}")
            self.db.rollback()
            return 0
        
        return count
    
    def _load_from_db(self, symbol: str, years: int) -> Optional[pd.DataFrame]:
        """
        從資料庫載入，返回格式與 yahoo_finance.get_stock_history() 完全相同
        """
        start_date = date.today() - timedelta(days=years * 365)
        
        try:
            results = self.db.query(StockPrice).filter(
                StockPrice.symbol == symbol.upper(),
                StockPrice.date >= start_date
            ).order_by(StockPrice.date).all()
            
            if not results:
                return None
            
            # 建立與 yahoo_finance 相同格式的 DataFrame
            data = []
            for r in results:
                data.append({
                    "date": r.date,
                    "open": float(r.open) if r.open else None,
                    "high": float(r.high) if r.high else None,
                    "low": float(r.low) if r.low else None,
                    "close": float(r.close) if r.close else None,
                    "volume": int(r.volume) if r.volume else 0,
                    "symbol": symbol.upper(),
                })
            
            df = pd.DataFrame(data)
            
            # 調用 yahoo_finance 的分割調整邏輯，產生 adj_close
            df = yahoo_finance._detect_and_adjust_splits(df, symbol)
            
            return df
            
        except Exception as e:
            logger.error(f"從 DB 載入失敗: {e}")
            return None
    
    def get_cache_stats(self, symbol: str = None) -> dict:
        """取得快取統計"""
        if symbol:
            info = self._get_cache_info(symbol.upper())
            if info:
                return {
                    "symbol": symbol.upper(),
                    "latest_date": info[0].isoformat(),
                    "record_count": info[1],
                }
            return {"symbol": symbol.upper(), "cached": False}
        
        try:
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
                    {"symbol": r[0], "records": r[1], "latest": r[2].isoformat() if r[2] else None}
                    for r in results
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def clear_cache(self, symbol: str = None) -> int:
        """清除快取"""
        try:
            if symbol:
                count = self.db.query(StockPrice).filter(
                    StockPrice.symbol == symbol.upper()
                ).delete()
            else:
                count = self.db.query(StockPrice).delete()
            
            self.db.commit()
            logger.info(f"🗑️ 已清除快取: {symbol or '全部'} ({count} 筆)")
            return count
        except Exception as e:
            logger.error(f"清除快取失敗: {e}")
            self.db.rollback()
            return 0
