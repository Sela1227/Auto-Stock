"""
é€šçŸ¥ç®¡ç†æœå‹™
æ•´åˆè¨Šè™Ÿåµæ¸¬ã€é€šçŸ¥è¨˜éŒ„ã€LINE æŽ¨æ’­
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
    """é€šçŸ¥ç®¡ç†æœå‹™"""
    
    # è¨Šè™Ÿé¡žåž‹èˆ‡é€šçŸ¥è¨­å®šçš„å°æ‡‰
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
        å–å¾—æ‰€æœ‰ç”¨æˆ¶è¿½è¹¤çš„è‚¡ç¥¨ï¼ˆè¯é›†ï¼‰
        
        Returns:
            {symbol: set(user_ids)} å°æ‡‰è¡¨
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
        
        logger.info(f"å…± {len(symbol_users)} å€‹è¿½è¹¤æ¨™çš„")
        return symbol_users
    
    async def get_user_alert_settings(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Dict[str, bool]:
        """å–å¾—ç”¨æˆ¶çš„é€šçŸ¥è¨­å®š"""
        result = await db.execute(
            select(UserAlertSettings).where(UserAlertSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # ä½¿ç”¨é è¨­å€¼ï¼ˆå…¨éƒ¨é–‹å•Ÿï¼‰
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
        æª¢æŸ¥æ˜¯å¦æœ€è¿‘å·²é€šçŸ¥éŽï¼ˆé˜²æ­¢é‡è¤‡ï¼‰
        
        Args:
            user_id: ç”¨æˆ¶ ID
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            signal_type: è¨Šè™Ÿé¡žåž‹
            hours: å¤šå°‘å°æ™‚å…§ä¸é‡è¤‡
            
        Returns:
            æ˜¯å¦å·²é€šçŸ¥éŽ
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
        """å„²å­˜é€šçŸ¥è¨˜éŒ„"""
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
        è™•ç†ç”¨æˆ¶çš„è¨Šè™Ÿé€šçŸ¥
        
        Args:
            db: è³‡æ–™åº« session
            user_id: ç”¨æˆ¶ ID
            line_user_id: LINE User ID
            signals: è¨Šè™Ÿåˆ—è¡¨
            
        Returns:
            è™•ç†çµæžœ
        """
        if not signals:
            return {"sent": 0, "skipped": 0, "filtered": 0}
        
        # å–å¾—ç”¨æˆ¶é€šçŸ¥è¨­å®š
        alert_settings = await self.get_user_alert_settings(db, user_id)
        
        sent_count = 0
        skipped_count = 0
        filtered_count = 0
        signals_to_send = []
        
        for signal in signals:
            # 1. æª¢æŸ¥ç”¨æˆ¶æ˜¯å¦é–‹å•Ÿæ­¤é¡žé€šçŸ¥
            setting_key = self.SIGNAL_TO_SETTING.get(signal.signal_type)
            if setting_key and not alert_settings.get(setting_key, True):
                filtered_count += 1
                continue
            
            # 2. æª¢æŸ¥æ˜¯å¦æœ€è¿‘å·²é€šçŸ¥éŽ
            if await self.is_recently_notified(
                db, user_id, signal.symbol, signal.signal_type.value
            ):
                skipped_count += 1
                continue
            
            signals_to_send.append(signal)
        
        # 3. ç™¼é€ LINE é€šçŸ¥
        if signals_to_send and line_user_id:
            # åˆä½µè¨Šæ¯ç™¼é€
            message = signal_service.format_signals_summary(signals_to_send)
            
            success = await line_notify_service.push_text_message(
                line_user_id, message
            )
            
            # 4. å„²å­˜é€šçŸ¥è¨˜éŒ„
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
        åŸ·è¡Œè¨Šè™Ÿæª¢æŸ¥ï¼ˆä¸»è¦å…¥å£ï¼‰
        
        æµç¨‹ï¼š
        1. å–å¾—æ‰€æœ‰è¿½è¹¤çš„è‚¡ç¥¨
        2. è¨ˆç®—æŠ€è¡“æŒ‡æ¨™
        3. åµæ¸¬è¨Šè™Ÿ
        4. æ ¹æ“šç”¨æˆ¶è¨­å®šéŽæ¿¾ä¸¦ç™¼é€é€šçŸ¥
        
        Returns:
            åŸ·è¡Œçµæžœæ‘˜è¦
        """
        logger.info("=" * 50)
        logger.info("é–‹å§‹åŸ·è¡Œè¨Šè™Ÿæª¢æŸ¥")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        result = {
            "symbols_checked": 0,
            "signals_detected": 0,
            "notifications_sent": 0,
            "errors": [],
        }
        
        try:
            # 1. å–å¾—æ‰€æœ‰è¿½è¹¤çš„è‚¡ç¥¨
            symbol_users = await self.get_all_tracked_symbols(db)
            
            if not symbol_users:
                logger.info("ç„¡è¿½è¹¤æ¨™çš„ï¼ŒçµæŸæª¢æŸ¥")
                return result
            
            all_signals_by_symbol = {}  # {symbol: [signals]}
            
            # 2. é€ä¸€è¨ˆç®—æŒ‡æ¨™ä¸¦åµæ¸¬è¨Šè™Ÿ
            for key, info in symbol_users.items():
                symbol = info["symbol"]
                asset_type = info["asset_type"]
                
                try:
                    # å–å¾—è‚¡åƒ¹è³‡æ–™
                    if asset_type == "stock":
                        df = yahoo_finance.get_stock_history(symbol, period="6mo")
                    else:
                        # åŠ å¯†è²¨å¹£è™•ç†
                        from app.services.crypto_service import crypto_service
                        df = await crypto_service.get_crypto_history(symbol, period="6mo")
                    
                    if df is None or df.empty:
                        logger.warning(f"{symbol} ç„¡æ³•å–å¾—è³‡æ–™")
                        continue
                    
                    # è¨ˆç®—æŠ€è¡“æŒ‡æ¨™
                    indicators = indicator_service.calculate_all_indicators(df)
                    
                    if not indicators:
                        continue
                    
                    # åµæ¸¬è¨Šè™Ÿ
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
                    logger.error(f"è™•ç† {symbol} æ™‚ç™¼ç”ŸéŒ¯èª¤: {e}")
                    result["errors"].append(f"{symbol}: {str(e)}")
            
            # 3. ç™¼é€é€šçŸ¥çµ¦ç”¨æˆ¶
            for key, data in all_signals_by_symbol.items():
                signals = data["signals"]
                user_ids = data["users"]
                
                for user_id in user_ids:
                    try:
                        # å–å¾—ç”¨æˆ¶ LINE ID
                        user_result = await db.execute(
                            select(User).where(User.id == user_id)
                        )
                        user = user_result.scalar_one_or_none()
                        
                        if not user or not user.line_user_id:
                            continue
                        
                        # è™•ç†ä¸¦ç™¼é€é€šçŸ¥
                        send_result = await self.process_signals_for_user(
                            db, user_id, user.line_user_id, signals
                        )
                        
                        result["notifications_sent"] += send_result["sent"]
                        
                    except Exception as e:
                        logger.error(f"ç™¼é€é€šçŸ¥çµ¦ç”¨æˆ¶ {user_id} æ™‚ç™¼ç”ŸéŒ¯èª¤: {e}")
                        result["errors"].append(f"user_{user_id}: {str(e)}")
            
            # 4. æª¢æŸ¥å¸‚å ´æƒ…ç·’
            try:
                from app.services.market_service import MarketService
                market_service = MarketService()
                sentiment = await market_service.get_current_sentiment()
                
                sentiment_signals = signal_service.detect_sentiment_signals(sentiment)
                
                if sentiment_signals:
                    result["signals_detected"] += len(sentiment_signals)
                    # æƒ…ç·’è¨Šè™Ÿç™¼é€çµ¦æ‰€æœ‰é–‹å•Ÿæ­¤é€šçŸ¥çš„ç”¨æˆ¶
                    # ï¼ˆé€™è£¡ç°¡åŒ–è™•ç†ï¼Œå¯¦éš›å¯ä»¥æ›´ç²¾ç´°æŽ§åˆ¶ï¼‰
                    logger.info(f"åµæ¸¬åˆ° {len(sentiment_signals)} å€‹æƒ…ç·’è¨Šè™Ÿ")
                    
            except Exception as e:
                logger.error(f"æª¢æŸ¥å¸‚å ´æƒ…ç·’æ™‚ç™¼ç”ŸéŒ¯èª¤: {e}")
            
        except Exception as e:
            logger.error(f"è¨Šè™Ÿæª¢æŸ¥ç™¼ç”Ÿåš´é‡éŒ¯èª¤: {e}", exc_info=True)
            result["errors"].append(f"critical: {str(e)}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        result["elapsed_seconds"] = round(elapsed, 2)
        
        logger.info(f"è¨Šè™Ÿæª¢æŸ¥å®Œæˆ: {result}")
        return result
    
    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict]:
        """å–å¾—ç”¨æˆ¶çš„é€šçŸ¥æ­·å²"""
        query = select(Notification).where(
            Notification.user_id == user_id
        ).order_by(Notification.triggered_at.desc()).limit(limit)
        
        if unread_only:
            query = query.where(Notification.sent == False)
        
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        return [n.to_dict() for n in notifications]


# å–®ä¾‹
notification_service = NotificationService()