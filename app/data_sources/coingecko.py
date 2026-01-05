"""
CoinGecko API 資料來源
抓取加密貨幣價格資料
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import time

logger = logging.getLogger(__name__)

# CoinGecko API 基礎 URL
BASE_URL = "https://api.coingecko.com/api/v3"

# 支援的加密貨幣對應
CRYPTO_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BITCOIN": "bitcoin",
    "ETHEREUM": "ethereum",
}


class CoinGeckoClient:
    """CoinGecko API 客戶端"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
        })
        self._last_request_time = 0
        self._min_request_interval = 1.5  # 免費 API 限制：~30 次/分鐘
    
    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _get(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """發送 GET 請求"""
        self._rate_limit()
        
        try:
            url = f"{BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API 請求失敗: {e}")
            return None
    
    def get_coin_id(self, symbol: str) -> Optional[str]:
        """將代號轉換為 CoinGecko ID"""
        symbol = symbol.upper()
        return CRYPTO_MAP.get(symbol)
    
    def get_current_price(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """
        取得即時價格
        
        Args:
            symbols: 代號列表 (如 ["BTC", "ETH"])
            
        Returns:
            {
                "BTC": {"price": 67850, "change_24h": 2.35, ...},
                "ETH": {"price": 3450, "change_24h": 1.82, ...}
            }
        """
        # 轉換代號
        coin_ids = []
        symbol_map = {}
        for symbol in symbols:
            coin_id = self.get_coin_id(symbol)
            if coin_id:
                coin_ids.append(coin_id)
                symbol_map[coin_id] = symbol.upper()
        
        if not coin_ids:
            return None
        
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
        }
        
        data = self._get("simple/price", params)
        if not data:
            return None
        
        result = {}
        for coin_id, values in data.items():
            symbol = symbol_map.get(coin_id, coin_id.upper())
            result[symbol] = {
                "price": values.get("usd"),
                "change_24h": values.get("usd_24h_change"),
                "volume_24h": values.get("usd_24h_vol"),
                "market_cap": values.get("usd_market_cap"),
            }
        
        return result
    
    def get_coin_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        取得加密貨幣詳細資訊
        
        Args:
            symbol: 代號 (如 BTC, ETH)
            
        Returns:
            包含價格、市值、歷史高點等資訊
        """
        coin_id = self.get_coin_id(symbol)
        if not coin_id:
            logger.warning(f"不支援的加密貨幣: {symbol}")
            return None
        
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false",
        }
        
        data = self._get(f"coins/{coin_id}", params)
        if not data:
            return None
        
        market_data = data.get("market_data", {})
        
        return {
            "symbol": symbol.upper(),
            "name": data.get("name"),
            "current_price": market_data.get("current_price", {}).get("usd"),
            "market_cap": market_data.get("market_cap", {}).get("usd"),
            "market_cap_rank": market_data.get("market_cap_rank"),
            "total_volume": market_data.get("total_volume", {}).get("usd"),
            "high_24h": market_data.get("high_24h", {}).get("usd"),
            "low_24h": market_data.get("low_24h", {}).get("usd"),
            "price_change_24h": market_data.get("price_change_24h"),
            "price_change_percentage_24h": market_data.get("price_change_percentage_24h"),
            "price_change_percentage_7d": market_data.get("price_change_percentage_7d"),
            "price_change_percentage_30d": market_data.get("price_change_percentage_30d"),
            "price_change_percentage_1y": market_data.get("price_change_percentage_1y"),
            "ath": market_data.get("ath", {}).get("usd"),
            "ath_date": market_data.get("ath_date", {}).get("usd"),
            "ath_change_percentage": market_data.get("ath_change_percentage", {}).get("usd"),
            "atl": market_data.get("atl", {}).get("usd"),
            "atl_date": market_data.get("atl_date", {}).get("usd"),
            "circulating_supply": market_data.get("circulating_supply"),
            "total_supply": market_data.get("total_supply"),
            "last_updated": data.get("last_updated"),
        }
    
    def get_market_chart(
        self,
        symbol: str,
        days: int = 365,
    ) -> Optional[pd.DataFrame]:
        """
        取得歷史價格資料
        
        Args:
            symbol: 代號 (如 BTC, ETH)
            days: 天數 (最多 365 天，免費 API 限制)
            
        Returns:
            DataFrame with columns: date, price, volume, market_cap
        """
        coin_id = self.get_coin_id(symbol)
        if not coin_id:
            return None
        
        params = {
            "vs_currency": "usd",
            "days": min(days, 365),  # 免費 API 限制
            "interval": "daily",
        }
        
        data = self._get(f"coins/{coin_id}/market_chart", params)
        if not data:
            return None
        
        # 解析資料
        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        market_caps = data.get("market_caps", [])
        
        if not prices:
            return None
        
        records = []
        for i, (timestamp, price) in enumerate(prices):
            record = {
                "date": datetime.fromtimestamp(timestamp / 1000).date(),
                "price": price,
                "volume_24h": volumes[i][1] if i < len(volumes) else None,
                "market_cap": market_caps[i][1] if i < len(market_caps) else None,
            }
            records.append(record)
        
        df = pd.DataFrame(records)
        df["symbol"] = symbol.upper()
        
        # 移除重複日期（保留最後一筆）
        df = df.drop_duplicates(subset=["date"], keep="last")
        df = df.sort_values("date").reset_index(drop=True)
        
        return df
    
    def get_ohlc(
        self,
        symbol: str,
        days: int = 365,
    ) -> Optional[pd.DataFrame]:
        """
        取得 OHLC 資料（K線資料）
        
        Args:
            symbol: 代號
            days: 天數 (1/7/14/30/90/180/365/max)
            
        Returns:
            DataFrame with columns: date, open, high, low, close
        """
        coin_id = self.get_coin_id(symbol)
        if not coin_id:
            return None
        
        # CoinGecko OHLC 只支援特定天數
        valid_days = [1, 7, 14, 30, 90, 180, 365]
        days = min(valid_days, key=lambda x: abs(x - days))
        
        params = {
            "vs_currency": "usd",
            "days": days,
        }
        
        data = self._get(f"coins/{coin_id}/ohlc", params)
        if not data:
            return None
        
        records = []
        for item in data:
            timestamp, open_p, high, low, close = item
            records.append({
                "date": datetime.fromtimestamp(timestamp / 1000).date(),
                "open": open_p,
                "high": high,
                "low": low,
                "close": close,
            })
        
        df = pd.DataFrame(records)
        df["symbol"] = symbol.upper()
        
        # 移除重複日期
        df = df.drop_duplicates(subset=["date"], keep="last")
        df = df.sort_values("date").reset_index(drop=True)
        
        return df
    
    def validate_symbol(self, symbol: str) -> bool:
        """驗證代號是否支援"""
        return self.get_coin_id(symbol) is not None


# 建立全域客戶端實例
coingecko = CoinGeckoClient()
