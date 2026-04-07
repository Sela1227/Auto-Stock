"""
通知管理服務
整合訊號偵測、通知記錄、LINE 推播
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.notification import Notification
from app.models.user_settings import UserAlertSettings
from app.services.signal_service import Signal, SignalType, signal_service
from app.services.line_notify_service import line_notify_service
from app.services.indicator_service import indicator_service
from app.data_sources.yahoo_finance import yahoo_finance

logger = logging.getLogger(__name__)


class NotificationService:
    """通知管理服務"""
    
    # 訊號類型與通知設定的對應
    SIGNAL_TO_SETTING = {
        SignalType.MA_GOLDEN_CROSS: "alert_ma_cross",
        SignalType.MA_DEATH_CROSS: "alert_ma_cross",
        SignalType.APPROACHING_BREAKOUT: "alert_ma_breakout",
        SignalType.APPROACHING_BREAKDOWN: "alert_ma_breakout",
        SignalType.BREAKOUT: "alert_ma_breakout",
        SignalType.BREAKDOWN: "alert_ma_breakout",
        SignalType.RSI_OVERBOUGHT: "alert_rsi",
        SignalType.RSI_OVERSOLD: "alert_rsi",
        SignalType.MACD_GOLDEN_CROSS: "alert_macd",
        SignalType.MACD_DEATH_CROSS: "alert_macd",
        SignalType.KD_GOLDEN_CROSS: "alert_kd",
        SignalType.KD_DEATH_CROSS: "alert_kd",
        SignalType.BOLLINGER_BREAKOUT: "alert_bollinger",
        SignalType.BOLLINGER_BREAKDOWN: "alert_bollinger",
        SignalType.VOLUME_SURGE: "alert_volume",
        SignalType.SENTIMENT_EXTREME_FEAR: "alert_sentiment",
        SignalType.SENTIMENT_EXTREME_GREED: "alert_sentiment",
    }
    
    async def get_all_tracked_symbols(self, db: AsyncSession) -> Dict[str, Set[int]]:
        """
        取得所有用戶追蹤的股票（聯集）
        
        Returns:
            {symbol: set(user_ids)} 對應表
        """
        result = await db.execute(
            select(Watchlist.symbol, Watchlist.user_id, Watchlist.asset_type)
            .join(User, Watchlist.user_id == User.id)
            .where(User.is_active == True)
            .where(User.is_blocked == False)
        )
        rows = result.all()
        
        symbol_users = {}
        for symbol, user_id, asset_type in rows:
            key = f"{symbol}|{asset_type}"
            if key not in symbol_users:
                symbol_users[key] = {"symbol": symbol, "asset_type": asset_type, "users": set()}
            symbol_users[key]["users"].add(user_id)
        
        logger.info(f"共 {len(symbol_users)} 個追蹤標的")
        return symbol_users
    
    async def get_user_alert_settings(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Dict[str, bool]:
        """取得用戶的通知設定"""
        result = await db.execute(
            select(UserAlertSettings).where(UserAlertSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # 使用預設值（全部開啟）
            return {
                "alert_ma_cross": True,
                "alert_ma_breakout": True,
                "alert_rsi": True,
                "alert_macd": True,
                "alert_kd": False,
                "alert_bollinger": False,
                "alert_volume": False,
                "alert_sentiment": True,
            }
        
        return {
            "alert_ma_cross": settings.alert_ma_cross,
            "alert_ma_breakout": settings.alert_ma_breakout,
            "alert_rsi": settings.alert_rsi,
            "alert_macd": settings.alert_macd,
            "alert_kd": settings.alert_kd,
            "alert_bollinger": settings.alert_bollinger,
            "alert_volume": settings.alert_volume,
            "alert_sentiment": settings.alert_sentiment,
        }
    
    async def is_recently_notified(
        self,
        db: AsyncSession,
        user_id: int,
        symbol: str,
        signal_type: str,
        hours: int = 24
    ) -> bool:
        """
        檢查是否最近已通知過（防止重複）
        
        Args:
            user_id: 用戶 ID
            symbol: 股票代號
            signal_type: 訊號類型
            hours: 多少小時內不重複
            
        Returns:
            是否已通知過
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await db.execute(
            select(func.count(Notification.id))
            .where(and_(
                Notification.user_id == user_id,
                Notification.symbol == symbol,
                Notification.alert_type == signal_type,
                Notification.triggered_at >= since
            ))
        )
        count = result.scalar()
        return count > 0
    
    async def save_notification(
        self,
        db: AsyncSession,
        user_id: int,
        signal: Signal,
        sent: bool = False
    ) -> Notification:
        """儲存通知記錄"""
        notification = Notification(
            user_id=user_id,
            symbol=signal.symbol,
            asset_type=signal.asset_type,
            alert_type=signal.signal_type.value,
            indicator=signal.indicator,
            message=signal.message,
            price_at_trigger=signal.price if signal.price > 0 else None,
            triggered_at=signal.timestamp,
            sent=sent,
            sent_at=datetime.utcnow() if sent else None,
        )
        db.add(notification)
        await db.commit()
        return notification
    
    async def process_signals_for_user(
        self,
        db: AsyncSession,
        user_id: int,
        line_user_id: str,
        signals: List[Signal]
    ) -> Dict[str, Any]:
        """
        處理用戶的訊號通知
        
        Args:
            db: 資料庫 session
            user_id: 用戶 ID
            line_user_id: LINE User ID
            signals: 訊號列表
            
        Returns:
            處理結果
        """
        if not signals:
            return {"sent": 0, "skipped": 0, "filtered": 0}
        
        # 取得用戶通知設定
        alert_settings = await self.get_user_alert_settings(db, user_id)
        
        sent_count = 0
        skipped_count = 0
        filtered_count = 0
        signals_to_send = []
        
        for signal in signals:
            # 1. 檢查用戶是否開啟此類通知
            setting_key = self.SIGNAL_TO_SETTING.get(signal.signal_type)
            if setting_key and not alert_settings.get(setting_key, True):
                filtered_count += 1
                continue
            
            # 2. 檢查是否最近已通知過
            if await self.is_recently_notified(
                db, user_id, signal.symbol, signal.signal_type.value
            ):
                skipped_count += 1
                continue
            
            signals_to_send.append(signal)
        
        # 3. 發送 LINE 通知
        if signals_to_send and line_user_id:
            # 合併訊息發送
            message = signal_service.format_signals_summary(signals_to_send)
            
            success = await line_notify_service.push_text_message(
                line_user_id, message
            )
            
            # 4. 儲存通知記錄
            for signal in signals_to_send:
                await self.save_notification(db, user_id, signal, sent=success)
                if success:
                    sent_count += 1
        
        return {
            "sent": sent_count,
            "skipped": skipped_count,
            "filtered": filtered_count,
        }
    
    async def run_signal_check(self, db: AsyncSession) -> Dict[str, Any]:
        """
        執行訊號檢查（主要入口）
        
        流程：
        1. 取得所有追蹤的股票
        2. 計算技術指標
        3. 偵測訊號
        4. 根據用戶設定過濾並發送通知
        
        Returns:
            執行結果摘要
        """
        logger.info("=" * 50)
        logger.info("開始執行訊號檢查")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        result = {
            "symbols_checked": 0,
            "signals_detected": 0,
            "notifications_sent": 0,
            "errors": [],
        }
        
        try:
            # 1. 取得所有追蹤的股票
            symbol_users = await self.get_all_tracked_symbols(db)
            
            if not symbol_users:
                logger.info("無追蹤標的，結束檢查")
                return result
            
            all_signals_by_symbol = {}  # {symbol: [signals]}
            
            # 2. 逐一計算指標並偵測訊號
            for key, info in symbol_users.items():
                symbol = info["symbol"]
                asset_type = info["asset_type"]
                
                try:
                    # 取得股價資料
                    if asset_type == "stock":
                        df = yahoo_finance.get_stock_history(symbol, period="6mo")
                    else:
                        # 加密貨幣處理
                        from app.services.crypto_service import crypto_service
                        df = await crypto_service.get_crypto_history(symbol, period="6mo")
                    
                    if df is None or df.empty:
                        logger.warning(f"{symbol} 無法取得資料")
                        continue
                    
                    # 計算技術指標
                    indicators = indicator_service.calculate_all_indicators(df)
                    
                    if not indicators:
                        continue
                    
                    # 偵測訊號
                    signals = signal_service.detect_signals(
                        symbol, indicators, asset_type
                    )
                    
                    if signals:
                        all_signals_by_symbol[key] = {
                            "signals": signals,
                            "users": info["users"],
                        }
                        result["signals_detected"] += len(signals)
                    
                    result["symbols_checked"] += 1
                    
                except Exception as e:
                    logger.error(f"處理 {symbol} 時發生錯誤: {e}")
                    result["errors"].append(f"{symbol}: {str(e)}")
            
            # 3. 發送通知給用戶
            for key, data in all_signals_by_symbol.items():
                signals = data["signals"]
                user_ids = data["users"]
                
                for user_id in user_ids:
                    try:
                        # 取得用戶 LINE ID
                        user_result = await db.execute(
                            select(User).where(User.id == user_id)
                        )
                        user = user_result.scalar_one_or_none()
                        
                        if not user or not user.line_user_id:
                            continue
                        
                        # 處理並發送通知
                        send_result = await self.process_signals_for_user(
                            db, user_id, user.line_user_id, signals
                        )
                        
                        result["notifications_sent"] += send_result["sent"]
                        
                    except Exception as e:
                        logger.error(f"發送通知給用戶 {user_id} 時發生錯誤: {e}")
                        result["errors"].append(f"user_{user_id}: {str(e)}")
            
            # 4. 檢查市場情緒
            try:
                from app.services.market_service import MarketService
                market_service = MarketService()
                sentiment = await market_service.get_current_sentiment()
                
                sentiment_signals = signal_service.detect_sentiment_signals(sentiment)
                
                if sentiment_signals:
                    result["signals_detected"] += len(sentiment_signals)
                    # 情緒訊號發送給所有開啟此通知的用戶
                    # （這裡簡化處理，實際可以更精細控制）
                    logger.info(f"偵測到 {len(sentiment_signals)} 個情緒訊號")
                    
            except Exception as e:
                logger.error(f"檢查市場情緒時發生錯誤: {e}")
            
        except Exception as e:
            logger.error(f"訊號檢查發生嚴重錯誤: {e}", exc_info=True)
            result["errors"].append(f"critical: {str(e)}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        result["elapsed_seconds"] = round(elapsed, 2)
        
        logger.info(f"訊號檢查完成: {result}")
        return result
    
    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict]:
        """取得用戶的通知歷史"""
        query = select(Notification).where(
            Notification.user_id == user_id
        ).order_by(Notification.triggered_at.desc()).limit(limit)
        
        if unread_only:
            query = query.where(Notification.sent == False)
        
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        return [n.to_dict() for n in notifications]


# 單例
notification_service = NotificationService()
