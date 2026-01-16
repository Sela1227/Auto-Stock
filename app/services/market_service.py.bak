"""
市場服務
處理三大指數、市場情緒的資料存取
"""
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc
import logging

from app.models.index_price import IndexPrice, INDEX_SYMBOLS
from app.models.market_sentiment import MarketSentiment
from app.models.dividend_history import DividendHistory
from app.models.stock_price import StockPrice
from app.data_sources.yahoo_finance import yahoo_finance
from app.data_sources.fear_greed import fear_greed

logger = logging.getLogger(__name__)


class MarketService:
    """市場服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 三大指數 ====================
    
    def get_latest_indices(self) -> Dict[str, Any]:
        """取得三大指數最新資料，回傳字典格式"""
        result = {}
        
        for symbol, info in INDEX_SYMBOLS.items():
            try:
                stmt = (
                    select(IndexPrice)
                    .where(IndexPrice.symbol == symbol)
                    .order_by(desc(IndexPrice.date))
                    .limit(1)
                )
                latest = self.db.execute(stmt).scalar_one_or_none()
                
                if latest:
                    result[symbol] = latest.to_dict()
                    continue
            except Exception as e:
                logger.warning(f"從資料庫取得 {symbol} 失敗: {e}")
            
            # Fallback: 從 Yahoo Finance API 取得
            try:
                df = yahoo_finance.get_index_data(symbol, period="5d")
                if df is not None and not df.empty:
                    row = df.iloc[-1]
                    result[symbol] = {
                        "symbol": symbol,
                        "name": info["name"],
                        "name_zh": info["name_zh"],
                        "date": str(row["date"]),
                        "close": float(row["close"]),
                        "change": float(row["change"]) if pd.notna(row.get("change")) else None,
                        "change_pct": float(row["change_pct"]) if pd.notna(row.get("change_pct")) else None,
                    }
                    logger.info(f"從 API 取得 {symbol}: {result[symbol]['close']}")
            except Exception as e:
                logger.error(f"從 API 取得 {symbol} 失敗: {e}")
        
        return result
    
    def get_index_history(
        self,
        symbol: str,
        days: int = 365,
    ) -> List[Dict[str, Any]]:
        """取得指數歷史資料"""
        start_date = date.today() - timedelta(days=days)
        
        stmt = (
            select(IndexPrice)
            .where(
                and_(
                    IndexPrice.symbol == symbol,
                    IndexPrice.date >= start_date,
                )
            )
            .order_by(IndexPrice.date)
        )
        results = self.db.execute(stmt).scalars().all()
        
        return [r.to_dict() for r in results]
    
    def save_index_data(self, df: pd.DataFrame, symbol: str) -> int:
        """
        儲存指數資料到資料庫
        
        Returns:
            儲存的筆數
        """
        import math
        
        def clean_value(val):
            """清理值，將 NaN/Inf 轉為 None"""
            if val is None:
                return None
            if pd.isna(val):
                return None
            try:
                f = float(val)
                if math.isnan(f) or math.isinf(f):
                    return None
                return f
            except (ValueError, TypeError):
                return None
        
        if df is None or df.empty:
            return 0
        
        count = 0
        index_info = INDEX_SYMBOLS.get(symbol, {})
        
        for _, row in df.iterrows():
            # 檢查是否已存在
            stmt = select(IndexPrice).where(
                and_(
                    IndexPrice.symbol == symbol,
                    IndexPrice.date == row["date"],
                )
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if existing:
                # 更新現有資料
                existing.open = clean_value(row.get("open"))
                existing.high = clean_value(row.get("high"))
                existing.low = clean_value(row.get("low"))
                existing.close = clean_value(row.get("close"))
                existing.volume = row.get("volume")
                existing.change = clean_value(row.get("change"))
                existing.change_pct = clean_value(row.get("change_pct"))
            else:
                # 新增資料
                price = IndexPrice(
                    symbol=symbol,
                    name=index_info.get("name", symbol),
                    date=row["date"],
                    open=clean_value(row.get("open")),
                    high=clean_value(row.get("high")),
                    low=clean_value(row.get("low")),
                    close=clean_value(row.get("close")),
                    volume=row.get("volume"),
                    change=clean_value(row.get("change")),
                    change_pct=clean_value(row.get("change_pct")),
                )
                self.db.add(price)
                count += 1
        
        self.db.commit()
        return count
    
    def fetch_and_save_all_indices(self, period: str = "10y") -> Dict[str, int]:
        """
        抓取並儲存所有三大指數資料
        
        Returns:
            {symbol: 儲存筆數}
        """
        result = {}
        
        for symbol in INDEX_SYMBOLS.keys():
            logger.info(f"抓取指數資料: {symbol}")
            df = yahoo_finance.get_index_data(symbol, period=period)
            
            if df is not None:
                count = self.save_index_data(df, symbol)
                result[symbol] = count
                logger.info(f"{symbol} 新增 {count} 筆資料")
            else:
                result[symbol] = 0
                logger.warning(f"{symbol} 抓取失敗")
        
        return result
    
    # ==================== 市場情緒 ====================
    
    def get_latest_sentiment(self) -> Dict[str, Any]:
        """取得最新的市場情緒"""
        result = {}
        
        for market in ["stock", "crypto"]:
            stmt = (
                select(MarketSentiment)
                .where(MarketSentiment.market == market)
                .order_by(desc(MarketSentiment.date))
                .limit(1)
            )
            latest = self.db.execute(stmt).scalar_one_or_none()
            
            if latest:
                result[market] = latest.to_dict()
            else:
                # 從 API 取得
                if market == "crypto":
                    data = fear_greed.get_crypto_fear_greed()
                else:
                    data = fear_greed.get_stock_fear_greed()
                
                if data:
                    result[market] = data
        
        return result
    
    def get_sentiment_history(
        self,
        market: str,
        days: int = 365,
    ) -> List[Dict[str, Any]]:
        """取得情緒歷史資料"""
        start_date = date.today() - timedelta(days=days)
        
        stmt = (
            select(MarketSentiment)
            .where(
                and_(
                    MarketSentiment.market == market,
                    MarketSentiment.date >= start_date,
                )
            )
            .order_by(MarketSentiment.date)
        )
        results = self.db.execute(stmt).scalars().all()
        
        return [r.to_dict() for r in results]
    
    def save_sentiment(
        self,
        market: str,
        value: int,
        target_date: Optional[date] = None,
    ) -> bool:
        """
        儲存市場情緒資料
        """
        if target_date is None:
            target_date = date.today()
        
        # 檢查是否已存在
        stmt = select(MarketSentiment).where(
            and_(
                MarketSentiment.market == market,
                MarketSentiment.date == target_date,
            )
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        
        classification = MarketSentiment.get_classification(value)
        
        if existing:
            existing.value = value
            existing.classification = classification
        else:
            sentiment = MarketSentiment(
                date=target_date,
                market=market,
                value=value,
                classification=classification,
            )
            self.db.add(sentiment)
        
        self.db.commit()
        return True
    
    def fetch_and_save_crypto_history(self, days: int = 365) -> int:
        """
        抓取並儲存幣圈情緒歷史資料
        
        Returns:
            儲存的筆數
        """
        logger.info(f"抓取幣圈情緒歷史: {days} 天")
        history = fear_greed.get_crypto_fear_greed_history(days)
        
        count = 0
        for item in history:
            try:
                target_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
                
                # 檢查是否已存在
                stmt = select(MarketSentiment).where(
                    and_(
                        MarketSentiment.market == "crypto",
                        MarketSentiment.date == target_date,
                    )
                )
                existing = self.db.execute(stmt).scalar_one_or_none()
                
                if not existing:
                    sentiment = MarketSentiment(
                        date=target_date,
                        market="crypto",
                        value=item["value"],
                        classification=item["classification"],
                    )
                    self.db.add(sentiment)
                    count += 1
            except Exception as e:
                logger.error(f"儲存情緒資料失敗: {e}")
        
        self.db.commit()
        logger.info(f"幣圈情緒歷史新增 {count} 筆")
        return count
    
    def update_today_sentiment(self) -> Dict[str, bool]:
        """
        更新今日的市場情緒
        
        Returns:
            {market: success}
        """
        result = {}
        
        # 美股情緒
        stock_data = fear_greed.get_stock_fear_greed()
        if stock_data and not stock_data.get("is_fallback"):
            result["stock"] = self.save_sentiment("stock", stock_data["value"])
        else:
            result["stock"] = False
        
        # 幣圈情緒
        crypto_data = fear_greed.get_crypto_fear_greed()
        if crypto_data and not crypto_data.get("is_fallback"):
            result["crypto"] = self.save_sentiment("crypto", crypto_data["value"])
        else:
            result["crypto"] = False
        
        return result
    
    # ==================== 配息資料 ====================
    
    def save_dividends(self, df: pd.DataFrame) -> int:
        """
        儲存配息資料
        
        Returns:
            儲存的筆數
        """
        if df is None or df.empty:
            return 0
        
        count = 0
        for _, row in df.iterrows():
            # 檢查是否已存在
            stmt = select(DividendHistory).where(
                and_(
                    DividendHistory.symbol == row["symbol"],
                    DividendHistory.date == row["date"],
                )
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if not existing:
                dividend = DividendHistory(
                    symbol=row["symbol"],
                    date=row["date"],
                    amount=row["amount"],
                )
                self.db.add(dividend)
                count += 1
        
        self.db.commit()
        return count
    
    def fetch_and_save_dividends(self, symbol: str, period: str = "10y") -> int:
        """
        抓取並儲存配息資料
        """
        logger.info(f"抓取配息資料: {symbol}")
        df = yahoo_finance.get_dividends(symbol, period=period)
        
        if df is not None:
            count = self.save_dividends(df)
            logger.info(f"{symbol} 配息新增 {count} 筆")
            return count
        
        return 0
    
    def get_dividends(
        self,
        symbol: str,
        years: int = 10,
    ) -> List[Dict[str, Any]]:
        """取得配息歷史"""
        start_date = date.today() - timedelta(days=years * 365)
        
        stmt = (
            select(DividendHistory)
            .where(
                and_(
                    DividendHistory.symbol == symbol.upper(),
                    DividendHistory.date >= start_date,
                )
            )
            .order_by(DividendHistory.date)
        )
        results = self.db.execute(stmt).scalars().all()
        
        return [r.to_dict() for r in results]
