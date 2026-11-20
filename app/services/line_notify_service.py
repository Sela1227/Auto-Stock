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
    
    
    
    


# 單例
line_notify_service = LineNotifyService()
