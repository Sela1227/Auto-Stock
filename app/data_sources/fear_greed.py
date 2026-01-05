"""
市場情緒指數資料來源
- CNN Fear & Greed Index (美股)
- Alternative.me (加密貨幣)
"""
import requests
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)


class FearGreedClient:
    """市場情緒指數客戶端"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
    
    # ==================== 加密貨幣情緒 (Alternative.me) ====================
    
    def get_crypto_fear_greed(self, limit: int = 1) -> Optional[Dict[str, Any]]:
        """
        取得加密貨幣 Fear & Greed 指數
        來源: Alternative.me
        
        Args:
            limit: 取得天數 (1 = 只取今天)
            
        Returns:
            {
                "value": 45,
                "classification": "fear",
                "classification_zh": "恐懼",
                "timestamp": "2025-01-05",
                "history": [...]  # 如果 limit > 1
            }
        """
        try:
            url = "https://api.alternative.me/fng/"
            params = {"limit": limit}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("data"):
                return self._get_fallback_crypto()
            
            latest = data["data"][0]
            value = int(latest["value"])
            
            result = {
                "value": value,
                "classification": latest.get("value_classification", "").lower().replace(" ", "_"),
                "classification_zh": self._get_classification_zh(value),
                "timestamp": datetime.fromtimestamp(int(latest["timestamp"])).strftime("%Y-%m-%d"),
                "market": "crypto",
            }
            
            # 如果需要歷史資料
            if limit > 1:
                result["history"] = [
                    {
                        "value": int(item["value"]),
                        "classification": item.get("value_classification", "").lower().replace(" ", "_"),
                        "timestamp": datetime.fromtimestamp(int(item["timestamp"])).strftime("%Y-%m-%d"),
                    }
                    for item in data["data"]
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"取得加密貨幣情緒指數失敗: {e}")
            return self._get_fallback_crypto()
    
    def _get_fallback_crypto(self) -> Dict[str, Any]:
        """加密貨幣情緒的備用值"""
        return {
            "value": 50,
            "classification": "neutral",
            "classification_zh": "中性",
            "timestamp": date.today().strftime("%Y-%m-%d"),
            "market": "crypto",
            "is_fallback": True,
        }
    
    # ==================== 美股情緒 (CNN Fear & Greed) ====================
    
    def get_stock_fear_greed(self) -> Optional[Dict[str, Any]]:
        """
        取得美股 Fear & Greed 指數
        來源: CNN Business (透過第三方 API 或爬蟲)
        
        Returns:
            {
                "value": 55,
                "classification": "neutral",
                "classification_zh": "中性",
                "timestamp": "2025-01-05",
            }
        """
        # 方法 1: 使用 CNN 的非官方 API
        result = self._get_cnn_fear_greed_api()
        if result:
            return result
        
        # 方法 2: 使用備用資料來源
        result = self._get_fear_greed_alternative()
        if result:
            return result
        
        logger.warning("無法取得美股情緒指數，使用備用值")
        # 返回備用值而非 None
        return {
            "value": 50,
            "classification": "neutral",
            "classification_zh": "中性",
            "timestamp": date.today().strftime("%Y-%m-%d"),
            "market": "stock",
            "is_fallback": True,
        }
    
    def _get_cnn_fear_greed_api(self) -> Optional[Dict[str, Any]]:
        """從 CNN API 取得 Fear & Greed"""
        try:
            # CNN 的非官方 API 端點
            url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("fear_and_greed"):
                return None
            
            fg_data = data["fear_and_greed"]
            value = int(round(fg_data.get("score", 0)))
            
            return {
                "value": value,
                "classification": self._get_classification(value),
                "classification_zh": self._get_classification_zh(value),
                "timestamp": date.today().strftime("%Y-%m-%d"),
                "market": "stock",
                "rating": fg_data.get("rating", ""),
            }
            
        except Exception as e:
            logger.debug(f"CNN API 取得失敗: {e}")
            return None
    
    def _get_fear_greed_alternative(self) -> Optional[Dict[str, Any]]:
        """備用方法：使用其他資料來源"""
        try:
            # 可以使用其他公開 API 或爬蟲
            # 這裡提供一個模擬的備用方案
            
            # 例如從 rapidapi 或其他來源取得
            # 目前返回 None，表示無法取得
            return None
            
        except Exception as e:
            logger.debug(f"備用來源取得失敗: {e}")
            return None
    
    # ==================== 通用方法 ====================
    
    def get_all_sentiment(self) -> Dict[str, Any]:
        """
        取得所有市場情緒
        
        Returns:
            {
                "stock": {...},
                "crypto": {...}
            }
        """
        result = {}
        
        # 美股情緒
        stock_sentiment = self.get_stock_fear_greed()
        if stock_sentiment:
            result["stock"] = stock_sentiment
        
        # 加密貨幣情緒
        crypto_sentiment = self.get_crypto_fear_greed()
        if crypto_sentiment:
            result["crypto"] = crypto_sentiment
        
        return result
    
    def _get_classification(self, value: int) -> str:
        """取得英文分類"""
        if value <= 25:
            return "extreme_fear"
        elif value <= 45:
            return "fear"
        elif value <= 55:
            return "neutral"
        elif value <= 75:
            return "greed"
        else:
            return "extreme_greed"
    
    def _get_classification_zh(self, value: int) -> str:
        """取得中文分類"""
        if value <= 25:
            return "極度恐懼"
        elif value <= 45:
            return "恐懼"
        elif value <= 55:
            return "中性"
        elif value <= 75:
            return "貪婪"
        else:
            return "極度貪婪"
    
    def get_sentiment_advice(self, value: int) -> str:
        """根據情緒值取得建議"""
        if value <= 25:
            return "市場極度恐懼，可能是買入機會，但需謹慎"
        elif value <= 45:
            return "市場偏恐懼，留意潛在機會"
        elif value <= 55:
            return "市場中性，觀望為主"
        elif value <= 75:
            return "市場偏樂觀，留意風險"
        else:
            return "市場極度貪婪，可能是獲利了結時機"


# 建立全域客戶端實例
fear_greed = FearGreedClient()
