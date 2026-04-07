"""
LINE Messaging API æŽ¨æ’­æœå‹™
ç™¼é€æŠ€è¡“è¨Šè™Ÿé€šçŸ¥çµ¦ç”¨æˆ¶
"""
import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class LineNotifyService:
    """LINE Messaging API æŽ¨æ’­æœå‹™"""
    
    PUSH_URL = "https://api.line.me/v2/bot/message/push"
    MULTICAST_URL = "https://api.line.me/v2/bot/message/multicast"
    BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"
    
    def __init__(self):
        self.channel_access_token = settings.LINE_MESSAGING_CHANNEL_ACCESS_TOKEN
        self.enabled = bool(self.channel_access_token)
        
        if not self.enabled:
            logger.warning("LINE Messaging API æœªè¨­å®š Channel Access Tokenï¼ŒæŽ¨æ’­åŠŸèƒ½åœç”¨")
    
    def _get_headers(self) -> Dict[str, str]:
        """å–å¾— API è«‹æ±‚æ¨™é ­"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}",
        }
    
    async def push_text_message(
        self, 
        user_id: str, 
        message: str
    ) -> bool:
        """
        æŽ¨é€æ–‡å­—è¨Šæ¯çµ¦å–®ä¸€ç”¨æˆ¶
        
        Args:
            user_id: LINE User ID
            message: è¨Šæ¯å…§å®¹
            
        Returns:
            æ˜¯å¦æˆåŠŸ
        """
        if not self.enabled:
            logger.warning("LINE æŽ¨æ’­æœªå•Ÿç”¨")
            return False
        
        if not user_id or not message:
            logger.warning("user_id æˆ– message ç‚ºç©º")
            return False
        
        payload = {
            "to": user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.PUSH_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"LINE æŽ¨æ’­æˆåŠŸ: user={user_id[:10]}...")
                    return True
                else:
                    logger.error(f"LINE æŽ¨æ’­å¤±æ•—: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"LINE æŽ¨æ’­ä¾‹å¤–: {e}")
            return False
    
    async def push_flex_message(
        self,
        user_id: str,
        alt_text: str,
        flex_content: Dict[str, Any]
    ) -> bool:
        """
        æŽ¨é€ Flex Message çµ¦å–®ä¸€ç”¨æˆ¶
        
        Args:
            user_id: LINE User ID
            alt_text: æ›¿ä»£æ–‡å­—ï¼ˆæ‰‹æ©Ÿé€šçŸ¥é¡¯ç¤ºï¼‰
            flex_content: Flex Message å…§å®¹
            
        Returns:
            æ˜¯å¦æˆåŠŸ
        """
        if not self.enabled:
            logger.warning("LINE æŽ¨æ’­æœªå•Ÿç”¨")
            return False
        
        payload = {
            "to": user_id,
            "messages": [
                {
                    "type": "flex",
                    "altText": alt_text,
                    "contents": flex_content
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.PUSH_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"LINE Flex æŽ¨æ’­æˆåŠŸ: user={user_id[:10]}...")
                    return True
                else:
                    logger.error(f"LINE Flex æŽ¨æ’­å¤±æ•—: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"LINE Flex æŽ¨æ’­ä¾‹å¤–: {e}")
            return False
    
    async def multicast_text_message(
        self,
        user_ids: List[str],
        message: str
    ) -> bool:
        """
        æŽ¨é€æ–‡å­—è¨Šæ¯çµ¦å¤šå€‹ç”¨æˆ¶ï¼ˆæœ€å¤š 500 äººï¼‰
        
        Args:
            user_ids: LINE User ID åˆ—è¡¨
            message: è¨Šæ¯å…§å®¹
            
        Returns:
            æ˜¯å¦æˆåŠŸ
        """
        if not self.enabled:
            logger.warning("LINE æŽ¨æ’­æœªå•Ÿç”¨")
            return False
        
        if not user_ids or not message:
            return False
        
        # LINE API é™åˆ¶æœ€å¤š 500 äºº
        if len(user_ids) > 500:
            logger.warning(f"ç”¨æˆ¶æ•¸è¶…éŽ 500ï¼ŒåªæŽ¨é€å‰ 500 äºº")
            user_ids = user_ids[:500]
        
        payload = {
            "to": user_ids,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.MULTICAST_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"LINE ç¾¤ç™¼æˆåŠŸ: {len(user_ids)} äºº")
                    return True
                else:
                    logger.error(f"LINE ç¾¤ç™¼å¤±æ•—: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"LINE ç¾¤ç™¼ä¾‹å¤–: {e}")
            return False
    
    async def broadcast_text_message(self, message: str) -> bool:
        """
        å»£æ’­è¨Šæ¯çµ¦æ‰€æœ‰å¥½å‹
        
        Args:
            message: è¨Šæ¯å…§å®¹
            
        Returns:
            æ˜¯å¦æˆåŠŸ
        """
        if not self.enabled:
            logger.warning("LINE æŽ¨æ’­æœªå•Ÿç”¨")
            return False
        
        payload = {
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BROADCAST_URL,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("LINE å»£æ’­æˆåŠŸ")
                    return True
                else:
                    logger.error(f"LINE å»£æ’­å¤±æ•—: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"LINE å»£æ’­ä¾‹å¤–: {e}")
            return False
    
    def create_signal_flex_message(
        self,
        symbol: str,
        signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        å»ºç«‹è¨Šè™Ÿé€šçŸ¥çš„ Flex Message
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            signals: è¨Šè™Ÿåˆ—è¡¨
            
        Returns:
            Flex Message å…§å®¹
        """
        # è¨Šè™Ÿé¡è‰²å°ç…§
        signal_colors = {
            "golden": "#00C853",  # ç¶ è‰²
            "death": "#FF1744",   # ç´…è‰²
            "overbought": "#FF9800",  # æ©™è‰²
            "oversold": "#00C853",
            "breakout": "#00C853",
            "breakdown": "#FF1744",
            "surge": "#2196F3",   # è—è‰²
            "fear": "#FF9800",
            "greed": "#FF1744",
        }
        
        def get_color(signal_type: str) -> str:
            for key, color in signal_colors.items():
                if key in signal_type.lower():
                    return color
            return "#666666"
        
        # å»ºç«‹è¨Šè™Ÿåˆ—è¡¨
        signal_boxes = []
        for s in signals:
            signal_type = s.get("signal_type", "")
            message = s.get("message", "")
            color = get_color(signal_type)
            
            signal_boxes.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": "â—",
                        "size": "sm",
                        "color": color,
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": message,
                        "size": "sm",
                        "color": "#333333",
                        "flex": 1,
                        "wrap": True
                    }
                ],
                "margin": "sm"
            })
        
        # Flex Message çµæ§‹
        flex_content = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"ðŸ“Š {symbol}",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#FFFFFF"
                    }
                ],
                "backgroundColor": "#FA7A35",
                "paddingAll": "15px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": signal_boxes,
                "paddingAll": "15px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "size": "xs",
                        "color": "#999999",
                        "align": "end"
                    }
                ],
                "paddingAll": "10px"
            }
        }
        
        return flex_content


# å–®ä¾‹
line_notify_service = LineNotifyService()