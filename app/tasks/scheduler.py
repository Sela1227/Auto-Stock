"""
排程任務服務
每日自動更新股價、指數、情緒資料
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
import logging

from app.database import SyncSessionLocal
from app.models.watchlist import Watchlist
from app.models.stock_price import StockPrice
from app.models.index_price import IndexPrice, INDEX_SYMBOLS
from app.models.market_sentiment import MarketSentiment
from app.services.market_service import MarketService
from app.data_sources.yahoo_finance import yahoo_finance

logger = logging.getLogger(__name__)


class SchedulerService:
    """排程任務服務"""
    
    def __init__(self):
        self.last_run: Optional[datetime] = None
        self.last_result: Dict[str, Any] = {}
    
    def _get_db(self) -> Session:
        """取得資料庫 session"""
        return SyncSessionLocal()
    
    def run_daily_update(self) -> Dict[str, Any]:
        """
        執行每日更新任務
        
        包含：
        1. 更新所有追蹤股票的價格
        2. 更新三大指數
        3. 更新市場情緒
        
        Returns:
            執行結果摘要
        """
        logger.info("=" * 50)
        logger.info("開始執行每日更新任務")
        logger.info(f"執行時間: {datetime.now()}")
        logger.info("=" * 50)
        
        result = {
            "start_time": datetime.now().isoformat(),
            "stocks_updated": 0,
            "indices_updated": {},
            "sentiment_updated": {},
            "errors": [],
        }
        
        db = self._get_db()
        
        try:
            # 1. 更新追蹤股票
            stocks_result = self._update_watchlist_stocks(db)
            result["stocks_updated"] = stocks_result["count"]
            if stocks_result.get("errors"):
                result["errors"].extend(stocks_result["errors"])
            
            # 2. 更新三大指數
            market_service = MarketService(db)
            indices_result = self._update_indices(market_service)
            result["indices_updated"] = indices_result
            
            # 3. 更新市場情緒
            sentiment_result = market_service.update_today_sentiment()
            result["sentiment_updated"] = sentiment_result
            
            result["end_time"] = datetime.now().isoformat()
            result["success"] = True
            
            logger.info("=" * 50)
            logger.info("每日更新任務完成")
            logger.info(f"股票更新: {result['stocks_updated']} 檔")
            logger.info(f"指數更新: {result['indices_updated']}")
            logger.info(f"情緒更新: {result['sentiment_updated']}")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"每日更新任務失敗: {e}")
            result["errors"].append(str(e))
            result["success"] = False
        finally:
            db.close()
        
        self.last_run = datetime.now()
        self.last_result = result
        
        return result
    
    def _update_watchlist_stocks(self, db: Session) -> Dict[str, Any]:
        """
        更新所有追蹤清單中的股票
        """
        result = {"count": 0, "errors": []}
        
        # 取得所有不重複的追蹤股票
        stmt = select(distinct(Watchlist.symbol)).where(Watchlist.asset_type == "stock")
        symbols = db.execute(stmt).scalars().all()
        
        logger.info(f"需要更新的股票: {len(symbols)} 檔")
        
        for symbol in symbols:
            try:
                # 從 Yahoo Finance 抓取最新資料
                df = yahoo_finance.get_stock_history(symbol, period="5d")
                
                if df is None or df.empty:
                    logger.warning(f"無法取得 {symbol} 的資料")
                    result["errors"].append(f"{symbol}: 無資料")
                    continue
                
                # 儲存到資料庫
                count = self._save_stock_prices(db, df)
                result["count"] += 1
                logger.debug(f"{symbol} 更新完成，新增 {count} 筆")
                
            except Exception as e:
                logger.error(f"更新 {symbol} 失敗: {e}")
                result["errors"].append(f"{symbol}: {str(e)}")
        
        return result
    
    def _save_stock_prices(self, db: Session, df) -> int:
        """儲存股票價格"""
        if df is None or df.empty:
            return 0
        
        from sqlalchemy import and_
        
        count = 0
        for _, row in df.iterrows():
            stmt = select(StockPrice).where(
                and_(
                    StockPrice.symbol == row["symbol"],
                    StockPrice.date == row["date"],
                )
            )
            existing = db.execute(stmt).scalar_one_or_none()
            
            if existing:
                existing.open = row["open"]
                existing.high = row["high"]
                existing.low = row["low"]
                existing.close = row["close"]
                existing.volume = row["volume"]
            else:
                price = StockPrice(
                    symbol=row["symbol"],
                    date=row["date"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                )
                db.add(price)
                count += 1
        
        db.commit()
        return count
    
    def _update_indices(self, market_service: MarketService) -> Dict[str, int]:
        """
        更新三大指數（只更新最近 5 天）
        """
        result = {}
        
        for symbol in INDEX_SYMBOLS.keys():
            try:
                df = yahoo_finance.get_index_data(symbol, period="5d")
                if df is not None:
                    count = market_service.save_index_data(df, symbol)
                    result[symbol] = count
                else:
                    result[symbol] = 0
            except Exception as e:
                logger.error(f"更新指數 {symbol} 失敗: {e}")
                result[symbol] = -1
        
        return result
    
    def initialize_historical_data(self, years: int = 10) -> Dict[str, Any]:
        """
        初始化歷史資料（首次執行時使用）
        
        包含：
        1. 三大指數 10 年歷史
        2. 幣圈情緒 365 天歷史
        
        Args:
            years: 指數歷史年數
            
        Returns:
            執行結果
        """
        logger.info("=" * 50)
        logger.info("開始初始化歷史資料")
        logger.info("=" * 50)
        
        result = {
            "start_time": datetime.now().isoformat(),
            "indices": {},
            "crypto_sentiment": 0,
            "errors": [],
        }
        
        db = self._get_db()
        
        try:
            market_service = MarketService(db)
            
            # 1. 初始化三大指數
            logger.info(f"初始化三大指數 ({years} 年資料)...")
            indices_result = market_service.fetch_and_save_all_indices(period=f"{years}y")
            result["indices"] = indices_result
            
            # 2. 初始化幣圈情緒歷史
            logger.info("初始化幣圈情緒歷史 (365 天)...")
            crypto_count = market_service.fetch_and_save_crypto_history(days=365)
            result["crypto_sentiment"] = crypto_count
            
            result["success"] = True
            result["end_time"] = datetime.now().isoformat()
            
            logger.info("=" * 50)
            logger.info("歷史資料初始化完成")
            logger.info(f"指數: {result['indices']}")
            logger.info(f"幣圈情緒: {result['crypto_sentiment']} 筆")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"初始化失敗: {e}")
            result["errors"].append(str(e))
            result["success"] = False
        finally:
            db.close()
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """取得排程狀態"""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_result": self.last_result,
        }


# 建立全域排程服務實例
scheduler_service = SchedulerService()
