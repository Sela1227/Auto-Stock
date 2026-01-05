"""
Yahoo Finance 資料來源
使用 yfinance 套件抓取美股資料
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Yahoo Finance 資料擷取客戶端"""
    
    def __init__(self):
        pass
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        取得股票基本資訊
        
        Args:
            symbol: 股票代號 (如 AAPL, TSLA)
            
        Returns:
            股票資訊字典，包含名稱、市值等
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or "symbol" not in info:
                logger.warning(f"無法取得股票資訊: {symbol}")
                return None
            
            return {
                "symbol": info.get("symbol", symbol),
                "name": info.get("longName") or info.get("shortName", "N/A"),
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            }
        except Exception as e:
            logger.error(f"取得股票資訊失敗 {symbol}: {e}")
            return None
    
    def get_stock_history(
        self,
        symbol: str,
        period: str = "1y",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Optional[pd.DataFrame]:
        """
        取得股票歷史價格資料
        
        Args:
            symbol: 股票代號
            period: 資料期間 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: 開始日期（與 end 搭配使用時，period 會被忽略）
            end: 結束日期
            
        Returns:
            包含 OHLCV 的 DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            
            if start and end:
                df = ticker.history(start=start, end=end)
            else:
                df = ticker.history(period=period)
            
            if df.empty:
                logger.warning(f"無歷史資料: {symbol}")
                return None
            
            # 重設索引，將日期變成欄位
            df = df.reset_index()
            
            # 標準化欄位名稱
            df = df.rename(columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            })
            
            # 只保留需要的欄位
            df = df[["date", "open", "high", "low", "close", "volume"]]
            
            # 確保日期是 date 類型
            df["date"] = pd.to_datetime(df["date"]).dt.date
            
            # 加入股票代號
            df["symbol"] = symbol.upper()
            
            return df
            
        except Exception as e:
            logger.error(f"取得歷史資料失敗 {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        取得股票即時（延遲）報價
        
        Args:
            symbol: 股票代號
            
        Returns:
            包含當前價格和漲跌資訊的字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            # 嘗試取得即時價格
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
            
            if not current_price:
                # 從歷史資料取得最新收盤價
                hist = ticker.history(period="5d")
                if not hist.empty:
                    current_price = hist["Close"].iloc[-1]
                    if len(hist) >= 2:
                        previous_close = hist["Close"].iloc[-2]
            
            if not current_price:
                return None
            
            change = current_price - previous_close if previous_close else 0
            change_pct = (change / previous_close * 100) if previous_close else 0
            
            return {
                "symbol": symbol.upper(),
                "price": round(current_price, 2),
                "previous_close": round(previous_close, 2) if previous_close else None,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
            }
            
        except Exception as e:
            logger.error(f"取得即時報價失敗 {symbol}: {e}")
            return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        驗證股票代號是否有效
        
        Args:
            symbol: 股票代號
            
        Returns:
            是否為有效代號
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info is not None and "symbol" in info
        except Exception:
            return False


# 建立全域客戶端實例
yahoo_finance = YahooFinanceClient()
