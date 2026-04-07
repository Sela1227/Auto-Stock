"""
CoinGecko API è³‡æ–™ä¾†æº
æŠ“å–åŠ å¯†è²¨å¹£åƒ¹æ ¼è³‡æ–™
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import time

logger = logging.getLogger(__name__)

# CoinGecko API åŸºç¤Ž URL
BASE_URL = "https://api.coingecko.com/api/v3"

# æ”¯æ´çš„åŠ å¯†è²¨å¹£å°æ‡‰
CRYPTO_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BITCOIN": "bitcoin",
    "ETHEREUM": "ethereum",
}


class CoinGeckoClient:
    """CoinGecko API å®¢æˆ¶ç«¯"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
        })
        self._last_request_time = 0
        self._min_request_interval = 1.5  # å…è²» API é™åˆ¶ï¼š~30 æ¬¡/åˆ†é˜
    
    def _rate_limit(self):
        """é€ŸçŽ‡é™åˆ¶"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _get(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """ç™¼é€ GET è«‹æ±‚"""
        self._rate_limit()
        
        try:
            url = f"{BASE_URL}/{endpoint}"
            logger.info(f"CoinGecko API è«‹æ±‚: {url}")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            logger.error(f"CoinGecko API è«‹æ±‚è¶…æ™‚: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"CoinGecko API é€£ç·šå¤±æ•— (å¯èƒ½è¢«ç¶²è·¯é™åˆ¶): {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API è«‹æ±‚å¤±æ•—: {e}")
            return None
    
    def get_coin_id(self, symbol: str) -> Optional[str]:
        """å°‡ä»£è™Ÿè½‰æ›ç‚º CoinGecko ID"""
        symbol = symbol.upper()
        return CRYPTO_MAP.get(symbol)
    
    def get_current_price(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """
        å–å¾—å³æ™‚åƒ¹æ ¼
        
        Args:
            symbols: ä»£è™Ÿåˆ—è¡¨ (å¦‚ ["BTC", "ETH"])
            
        Returns:
            {
                "BTC": {"price": 67850, "change_24h": 2.35, ...},
                "ETH": {"price": 3450, "change_24h": 1.82, ...}
            }
        """
        # è½‰æ›ä»£è™Ÿ
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
        å–å¾—åŠ å¯†è²¨å¹£è©³ç´°è³‡è¨Š
        
        Args:
            symbol: ä»£è™Ÿ (å¦‚ BTC, ETH)
            
        Returns:
            åŒ…å«åƒ¹æ ¼ã€å¸‚å€¼ã€æ­·å²é«˜é»žç­‰è³‡è¨Š
        """
        coin_id = self.get_coin_id(symbol)
        if not coin_id:
            logger.warning(f"ä¸æ”¯æ´çš„åŠ å¯†è²¨å¹£: {symbol}")
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
        å–å¾—æ­·å²åƒ¹æ ¼è³‡æ–™
        
        Args:
            symbol: ä»£è™Ÿ (å¦‚ BTC, ETH)
            days: å¤©æ•¸ (æœ€å¤š 365 å¤©ï¼Œå…è²» API é™åˆ¶)
            
        Returns:
            DataFrame with columns: date, price, volume, market_cap
        """
        coin_id = self.get_coin_id(symbol)
        if not coin_id:
            return None
        
        params = {
            "vs_currency": "usd",
            "days": min(days, 365),  # å…è²» API é™åˆ¶
            "interval": "daily",
        }
        
        data = self._get(f"coins/{coin_id}/market_chart", params)
        if not data:
            return None
        
        # è§£æžè³‡æ–™
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
        
        # ç§»é™¤é‡è¤‡æ—¥æœŸï¼ˆä¿ç•™æœ€å¾Œä¸€ç­†ï¼‰
        df = df.drop_duplicates(subset=["date"], keep="last")
        df = df.sort_values("date").reset_index(drop=True)
        
        return df
    
    def get_ohlc(
        self,
        symbol: str,
        days: int = 365,
    ) -> Optional[pd.DataFrame]:
        """
        å–å¾— OHLC è³‡æ–™ï¼ˆKç·šè³‡æ–™ï¼‰
        
        Args:
            symbol: ä»£è™Ÿ
            days: å¤©æ•¸ (1/7/14/30/90/180/365/max)
            
        Returns:
            DataFrame with columns: date, open, high, low, close
        """
        coin_id = self.get_coin_id(symbol)
        if not coin_id:
            return None
        
        # CoinGecko OHLC åªæ”¯æ´ç‰¹å®šå¤©æ•¸
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
        
        # ç§»é™¤é‡è¤‡æ—¥æœŸ
        df = df.drop_duplicates(subset=["date"], keep="last")
        df = df.sort_values("date").reset_index(drop=True)
        
        return df
    
    def validate_symbol(self, symbol: str) -> bool:
        """é©—è­‰ä»£è™Ÿæ˜¯å¦æ”¯æ´"""
        return self.get_coin_id(symbol) is not None


# å»ºç«‹å…¨åŸŸå®¢æˆ¶ç«¯å¯¦ä¾‹
coingecko = CoinGeckoClient()