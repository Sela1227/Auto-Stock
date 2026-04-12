"""
LINE Messaging API 推播服務
發送技術訊號通知給用戶
"""
import httpx
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class LineNotifyService:
    """LINE Messaging API 推播服務"""
    
    PUSH_URL = "https://api.line.me/v2/bot/message/push"
    MULTICAST_URL = "https://api.line.me/v2/bot/message/multicast"
    BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"
    
    def __init__(self):
        self.channel_access_token = settings.LINE_MESSAGING_CHANNEL_ACCESS_TOKEN
        self.enabled = bool(self.channel_access_token)
        
        if not self.enabled:
            logger.warning("LINE Messaging API 未設定 Channel Access Token，推播功能停用")
    
    def _get_headers(self) -> Dict[str, str]:
        """取得 API 請求標頭"""
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
        推送文字訊息給單一用戶
        
        Args:
            user_id: LINE User ID
            message: 訊息內容
            
        Returns:
            是否成功
        """
        if not self.enabled:
            logger.warning("LINE 推播未啟用")
            return False
        
        if not user_id or not message:
            logger.warning("user_id 或 message 為空")
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
                    logger.info(f"LINE 推播成功: user={user_id[:10]}...")
                    return True
                else:
                    logger.error(f"LINE 推播失敗: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"LINE 推播例外: {e}")
            return False
    
    async def push_flex_message(
        self,
        user_id: str,
        alt_text: str,
        flex_content: Dict[str, Any]
    ) -> bool:
        """
        推送 Flex Message 給單一用戶
        
        Args:
            user_id: LINE User ID
            alt_text: 替代文字（手機通知顯示）
            flex_content: Flex Message 內容
            
        Returns:
            是否成功
        """
        if not self.enabled:
            logger.warning("LINE 推播未啟用")
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
                    logger.info(f"LINE Flex 推播成功: user={user_id[:10]}...")
                    return True
                else:
                    logger.error(f"LINE Flex 推播失敗: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"LINE Flex 推播例外: {e}")
            return False
    
    async def multicast_text_message(
        self,
        user_ids: List[str],
        message: str
    ) -> bool:
        """
        推送文字訊息給多個用戶（最多 500 人）
        
        Args:
            user_ids: LINE User ID 列表
            message: 訊息內容
            
        Returns:
            是否成功
        """
        if not self.enabled:
            logger.warning("LINE 推播未啟用")
            return False
        
        if not user_ids or not message:
            return False
        
        # LINE API 限制最多 500 人
        if len(user_ids) > 500:
            logger.warning(f"用戶數超過 500，只推送前 500 人")
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
                    logger.info(f"LINE 群發成功: {len(user_ids)} 人")
                    return True
                else:
                    logger.error(f"LINE 群發失敗: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"LINE 群發例外: {e}")
            return False
    
    async def broadcast_text_message(self, message: str) -> bool:
        """
        廣播訊息給所有好友
        
        Args:
            message: 訊息內容
            
        Returns:
            是否成功
        """
        if not self.enabled:
            logger.warning("LINE 推播未啟用")
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
                    logger.info("LINE 廣播成功")
                    return True
                else:
                    logger.error(f"LINE 廣播失敗: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"LINE 廣播例外: {e}")
            return False
    
    def create_signal_flex_message(
        self,
        symbol: str,
        signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        建立訊號通知的 Flex Message
        
        Args:
            symbol: 股票代號
            signals: 訊號列表
            
        Returns:
            Flex Message 內容
        """
        # 訊號顏色對照
        signal_colors = {
            "golden": "#00C853",  # 綠色
            "death": "#FF1744",   # 紅色
            "overbought": "#FF9800",  # 橙色
            "oversold": "#00C853",
            "breakout": "#00C853",
            "breakdown": "#FF1744",
            "surge": "#2196F3",   # 藍色
            "fear": "#FF9800",
            "greed": "#FF1744",
        }
        
        def get_color(signal_type: str) -> str:
            for key, color in signal_colors.items():
                if key in signal_type.lower():
                    return color
            return "#666666"
        
        # 建立訊號列表
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
                        "text": "●",
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
        
        # Flex Message 結構
        flex_content = {
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"📊 {symbol}",
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


# 單例
line_notify_service = LineNotifyService()
