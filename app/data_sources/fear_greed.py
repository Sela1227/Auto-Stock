"""
å¸‚å ´æƒ…ç·’æŒ‡æ•¸è³‡æ–™ä¾†æº
- CNN Fear & Greed Index (ç¾Žè‚¡)
- Alternative.me (åŠ å¯†è²¨å¹£)
"""
import requests
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)


class FearGreedClient:
    """å¸‚å ´æƒ…ç·’æŒ‡æ•¸å®¢æˆ¶ç«¯"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
    
    # ==================== åŠ å¯†è²¨å¹£æƒ…ç·’ (Alternative.me) ====================
    
    def get_crypto_fear_greed(self, limit: int = 1) -> Optional[Dict[str, Any]]:
        """
        å–å¾—åŠ å¯†è²¨å¹£ Fear & Greed æŒ‡æ•¸
        ä¾†æº: Alternative.me
        
        Args:
            limit: å–å¾—å¤©æ•¸ (1 = åªå–ä»Šå¤©)
            
        Returns:
            {
                "value": 45,
                "classification": "fear",
                "classification_zh": "ææ‡¼",
                "timestamp": "2025-01-05",
                "history": [...]  # å¦‚æžœ limit > 1
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
            
            # å¦‚æžœéœ€è¦æ­·å²è³‡æ–™
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
            logger.error(f"å–å¾—åŠ å¯†è²¨å¹£æƒ…ç·’æŒ‡æ•¸å¤±æ•—: {e}")
            return self._get_fallback_crypto()
    
    def _get_fallback_crypto(self) -> Dict[str, Any]:
        """åŠ å¯†è²¨å¹£æƒ…ç·’çš„å‚™ç”¨å€¼"""
        return {
            "value": 50,
            "classification": "neutral",
            "classification_zh": "ä¸­æ€§",
            "timestamp": date.today().strftime("%Y-%m-%d"),
            "market": "crypto",
            "is_fallback": True,
        }
    
    # ==================== ç¾Žè‚¡æƒ…ç·’ (CNN Fear & Greed) ====================
    
    def get_stock_fear_greed(self) -> Optional[Dict[str, Any]]:
        """
        å–å¾—ç¾Žè‚¡ Fear & Greed æŒ‡æ•¸
        ä¾†æº: CNN Business (é€éŽç¬¬ä¸‰æ–¹ API æˆ–çˆ¬èŸ²)
        
        Returns:
            {
                "value": 55,
                "classification": "neutral",
                "classification_zh": "ä¸­æ€§",
                "timestamp": "2025-01-05",
            }
        """
        # æ–¹æ³• 1: ä½¿ç”¨ CNN çš„éžå®˜æ–¹ API
        result = self._get_cnn_fear_greed_api()
        if result:
            return result
        
        # æ–¹æ³• 2: ä½¿ç”¨å‚™ç”¨è³‡æ–™ä¾†æº
        result = self._get_fear_greed_alternative()
        if result:
            return result
        
        logger.warning("ç„¡æ³•å–å¾—ç¾Žè‚¡æƒ…ç·’æŒ‡æ•¸ï¼Œä½¿ç”¨å‚™ç”¨å€¼")
        # è¿”å›žå‚™ç”¨å€¼è€Œéž None
        return {
            "value": 50,
            "classification": "neutral",
            "classification_zh": "ä¸­æ€§",
            "timestamp": date.today().strftime("%Y-%m-%d"),
            "market": "stock",
            "is_fallback": True,
        }
    
    def _get_cnn_fear_greed_api(self) -> Optional[Dict[str, Any]]:
        """å¾ž CNN API å–å¾— Fear & Greed"""
        try:
            # CNN çš„éžå®˜æ–¹ API ç«¯é»ž
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
            logger.debug(f"CNN API å–å¾—å¤±æ•—: {e}")
            return None
    
    def _get_fear_greed_alternative(self) -> Optional[Dict[str, Any]]:
        """å‚™ç”¨æ–¹æ³•ï¼šä½¿ç”¨å…¶ä»–è³‡æ–™ä¾†æº"""
        try:
            # å¯ä»¥ä½¿ç”¨å…¶ä»–å…¬é–‹ API æˆ–çˆ¬èŸ²
            # é€™è£¡æä¾›ä¸€å€‹æ¨¡æ“¬çš„å‚™ç”¨æ–¹æ¡ˆ
            
            # ä¾‹å¦‚å¾ž rapidapi æˆ–å…¶ä»–ä¾†æºå–å¾—
            # ç›®å‰è¿”å›ž Noneï¼Œè¡¨ç¤ºç„¡æ³•å–å¾—
            return None
            
        except Exception as e:
            logger.debug(f"å‚™ç”¨ä¾†æºå–å¾—å¤±æ•—: {e}")
            return None
    
    # ==================== é€šç”¨æ–¹æ³• ====================
    
    def get_all_sentiment(self) -> Dict[str, Any]:
        """
        å–å¾—æ‰€æœ‰å¸‚å ´æƒ…ç·’
        
        Returns:
            {
                "stock": {...},
                "crypto": {...}
            }
        """
        result = {}
        
        # ç¾Žè‚¡æƒ…ç·’
        stock_sentiment = self.get_stock_fear_greed()
        if stock_sentiment:
            result["stock"] = stock_sentiment
        
        # åŠ å¯†è²¨å¹£æƒ…ç·’
        crypto_sentiment = self.get_crypto_fear_greed()
        if crypto_sentiment:
            result["crypto"] = crypto_sentiment
        
        return result
    
    def _get_classification(self, value: int) -> str:
        """å–å¾—è‹±æ–‡åˆ†é¡ž"""
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
        """å–å¾—ä¸­æ–‡åˆ†é¡ž"""
        if value <= 25:
            return "æ¥µåº¦ææ‡¼"
        elif value <= 45:
            return "ææ‡¼"
        elif value <= 55:
            return "ä¸­æ€§"
        elif value <= 75:
            return "è²ªå©ª"
        else:
            return "æ¥µåº¦è²ªå©ª"
    
    def get_sentiment_advice(self, value: int) -> str:
        """æ ¹æ“šæƒ…ç·’å€¼å–å¾—å»ºè­°"""
        if value <= 25:
            return "å¸‚å ´æ¥µåº¦ææ‡¼ï¼Œå¯èƒ½æ˜¯è²·å…¥æ©Ÿæœƒï¼Œä½†éœ€è¬¹æ…Ž"
        elif value <= 45:
            return "å¸‚å ´åææ‡¼ï¼Œç•™æ„æ½›åœ¨æ©Ÿæœƒ"
        elif value <= 55:
            return "å¸‚å ´ä¸­æ€§ï¼Œè§€æœ›ç‚ºä¸»"
        elif value <= 75:
            return "å¸‚å ´åæ¨‚è§€ï¼Œç•™æ„é¢¨éšª"
        else:
            return "å¸‚å ´æ¥µåº¦è²ªå©ªï¼Œå¯èƒ½æ˜¯ç²åˆ©äº†çµæ™‚æ©Ÿ"
    
    def get_crypto_fear_greed_history(self, days: int = 365) -> List[Dict[str, Any]]:
        """
        å–å¾—åŠ å¯†è²¨å¹£ Fear & Greed æ­·å²è³‡æ–™
        
        Args:
            days: å–å¾—å¤©æ•¸ï¼ˆæœ€å¤š 365 å¤©ï¼‰
            
        Returns:
            æ­·å²è³‡æ–™åˆ—è¡¨
        """
        try:
            url = "https://api.alternative.me/fng/"
            params = {"limit": min(days, 365)}
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("data"):
                return []
            
            history = []
            for item in data["data"]:
                value = int(item["value"])
                history.append({
                    "date": datetime.fromtimestamp(int(item["timestamp"])).strftime("%Y-%m-%d"),
                    "value": value,
                    "classification": item.get("value_classification", "").lower().replace(" ", "_"),
                    "classification_zh": self._get_classification_zh(value),
                })
            
            # åè½‰é †åºï¼Œè®“æœ€èˆŠçš„åœ¨å‰é¢
            history.reverse()
            
            return history
            
        except Exception as e:
            logger.error(f"å–å¾—åŠ å¯†è²¨å¹£æƒ…ç·’æ­·å²å¤±æ•—: {e}")
            return []


# å»ºç«‹å…¨åŸŸå®¢æˆ¶ç«¯å¯¦ä¾‹
fear_greed = FearGreedClient()