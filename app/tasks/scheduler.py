"""
排程任務服務
每日自動更新股價、指數、情緒資料，並發送訊號通知
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct, and_
import logging

from app.database import SyncSessionLocal, AsyncSessionLocal
from app.models.watchlist import Watchlist
from app.models.stock_price import StockPrice
from app.models.index_price import IndexPrice, INDEX_SYMBOLS
from app.models.market_sentiment import MarketSentiment
from app.models.notification import Notification
from app.models.user import User
from app.models.user_settings import UserAlertSettings
from app.services.market_service import MarketService
from app.services.signal_service import signal_service, SignalType
from app.data_sources.yahoo_finance import yahoo_finance

logger = logging.getLogger(__name__)


class SchedulerService:
    """排程任務服務"""
    
    # 重要訊號類型（只通知這些）
    IMPORTANT_SIGNAL_TYPES = [
        # 交叉訊號
        SignalType.MA_GOLDEN_CROSS,
        SignalType.MA_DEATH_CROSS,
        SignalType.MACD_GOLDEN_CROSS,
        SignalType.MACD_DEATH_CROSS,
        SignalType.KD_GOLDEN_CROSS,
        SignalType.KD_DEATH_CROSS,
        # RSI 極端值
        SignalType.RSI_OVERBOUGHT,
        SignalType.RSI_OVERSOLD,
    ]
    
    def __init__(self):
        self.last_run: Optional[datetime] = None
        self.last_result: Dict[str, Any] = {}
    
    def _get_db(self) -> Session:
        """取得資料庫 session"""
        return SyncSessionLocal()
    
    def run_daily_update(self) -> Dict[str, Any]:
        """
        執行每日更新任務
        
        包含：
        1. 更新所有追蹤股票的價格
        2. 更新三大指數
        3. 更新市場情緒
        4. 偵測訊號並發送通知
        
        Returns:
            執行結果摘要
        """
        logger.info("=" * 50)
        logger.info("開始執行每日更新任務")
        logger.info(f"執行時間: {datetime.now()}")
        logger.info("=" * 50)
        
        result = {
            "start_time": datetime.now().isoformat(),
            "stocks_updated": 0,
            "indices_updated": {},
            "sentiment_updated": {},
            "signals_detected": 0,
            "notifications_sent": 0,
            "errors": [],
        }
        
        db = self._get_db()
        
        try:
            # 1. 更新追蹤股票
            stocks_result = self._update_watchlist_stocks(db)
            result["stocks_updated"] = stocks_result["count"]
            if stocks_result.get("errors"):
                result["errors"].extend(stocks_result["errors"])
            
            # 2. 更新三大指數
            market_service = MarketService(db)
            indices_result = self._update_indices(market_service)
            result["indices_updated"] = indices_result
            
            # 3. 更新市場情緒
            sentiment_result = market_service.update_today_sentiment()
            result["sentiment_updated"] = sentiment_result
            
            # 4. 偵測訊號並發送通知
            signal_result = self._detect_and_notify(db)
            result["signals_detected"] = signal_result.get("signals_count", 0)
            result["notifications_sent"] = signal_result.get("notifications_sent", 0)
            if signal_result.get("errors"):
                result["errors"].extend(signal_result["errors"])
            
            result["end_time"] = datetime.now().isoformat()
            result["success"] = True
            
            logger.info("=" * 50)
            logger.info("每日更新任務完成")
            logger.info(f"股票更新: {result['stocks_updated']} 檔")
            logger.info(f"指數更新: {result['indices_updated']}")
            logger.info(f"情緒更新: {result['sentiment_updated']}")
            logger.info(f"訊號偵測: {result['signals_detected']} 個")
            logger.info(f"通知發送: {result['notifications_sent']} 人")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"每日更新任務失敗: {e}")
            result["errors"].append(str(e))
            result["success"] = False
        finally:
            db.close()
        
        self.last_run = datetime.now()
        self.last_result = result
        
        return result
    
    def _detect_and_notify(self, db: Session) -> Dict[str, Any]:
        """
        偵測訊號並發送通知
        
        流程：
        1. 取得所有用戶的追蹤清單（聯集）
        2. 對每支股票計算指標並偵測訊號
        3. 根據用戶設定發送通知
        """
        result = {
            "signals_count": 0,
            "notifications_sent": 0,
            "errors": [],
        }
        
        logger.info("開始偵測訊號...")
        
        try:
            # 1. 取得所有追蹤的股票
            stmt = select(distinct(Watchlist.symbol)).where(Watchlist.asset_type == "stock")
            symbols = db.execute(stmt).scalars().all()
            logger.info(f"需要偵測的股票: {len(symbols)} 檔")
            
            # 2. 對每支股票偵測訊號
            all_signals = {}  # {symbol: [signals]}
            
            for symbol in symbols:
                try:
                    signals = self._detect_signals_for_symbol(symbol)
                    
                    # 只保留交叉訊號
                    cross_signals = [s for s in signals if s.signal_type in self.IMPORTANT_SIGNAL_TYPES]
                    
                    if cross_signals:
                        all_signals[symbol] = cross_signals
                        result["signals_count"] += len(cross_signals)
                        logger.info(f"{symbol}: 偵測到 {len(cross_signals)} 個交叉訊號")
                
                except Exception as e:
                    logger.error(f"偵測 {symbol} 訊號失敗: {e}")
                    result["errors"].append(f"{symbol}: {str(e)}")
            
            logger.info(f"共偵測到 {result['signals_count']} 個交叉訊號")
            
            if not all_signals:
                logger.info("今日無交叉訊號，不發送通知")
                return result
            
            # 3. 取得需要通知的用戶
            users_to_notify = self._get_users_to_notify(db, all_signals)
            logger.info(f"需要通知的用戶: {len(users_to_notify)} 人")
            
            # 4. 發送通知
            for user_id, user_data in users_to_notify.items():
                try:
                    success = self._send_notification(db, user_data)
                    if success:
                        result["notifications_sent"] += 1
                except Exception as e:
                    logger.error(f"發送通知給用戶 {user_id} 失敗: {e}")
                    result["errors"].append(f"notify user {user_id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"訊號偵測失敗: {e}")
            result["errors"].append(str(e))
        
        return result
    
    def _detect_signals_for_symbol(self, symbol: str) -> List:
        """對單一股票偵測訊號"""
        from app.services.indicator_service import indicator_service, SignalType as IndicatorSignalType
        
        # 取得股票資料
        df = yahoo_finance.get_stock_history(symbol, period="3mo")
        
        if df is None or df.empty:
            return []
        
        # 計算指標
        df = indicator_service.calculate_all_indicators(df)
        
        if df is None or df.empty:
            return []
        
        # 取得訊號
        indicator_signals = indicator_service.get_all_signals(df)
        
        if not indicator_signals:
            return []
        
        # 轉換訊號格式（從 indicator_service.Signal 到 signal_service.Signal）
        from app.services.signal_service import Signal, SignalType
        
        signals = []
        current_price = float(df.iloc[-1]['close']) if 'close' in df.columns else 0
        
        # 訊號類型對照
        type_mapping = {
            IndicatorSignalType.GOLDEN_CROSS: SignalType.MA_GOLDEN_CROSS,
            IndicatorSignalType.DEATH_CROSS: SignalType.MA_DEATH_CROSS,
            IndicatorSignalType.RSI_OVERBOUGHT: SignalType.RSI_OVERBOUGHT,
            IndicatorSignalType.RSI_OVERSOLD: SignalType.RSI_OVERSOLD,
            IndicatorSignalType.MACD_GOLDEN_CROSS: SignalType.MACD_GOLDEN_CROSS,
            IndicatorSignalType.MACD_DEATH_CROSS: SignalType.MACD_DEATH_CROSS,
            IndicatorSignalType.KD_GOLDEN_CROSS: SignalType.KD_GOLDEN_CROSS,
            IndicatorSignalType.KD_DEATH_CROSS: SignalType.KD_DEATH_CROSS,
            IndicatorSignalType.APPROACHING_BREAKOUT: SignalType.APPROACHING_BREAKOUT,
            IndicatorSignalType.APPROACHING_BREAKDOWN: SignalType.APPROACHING_BREAKDOWN,
        }
        
        for ind_sig in indicator_signals:
            sig_type = type_mapping.get(ind_sig.type)
            if sig_type:
                signals.append(Signal(
                    symbol=symbol,
                    asset_type="stock",
                    signal_type=sig_type,
                    indicator=ind_sig.indicator,
                    message=ind_sig.description,
                    price=current_price,
                    details={},
                    timestamp=datetime.now(),
                ))
        
        return signals
    
    def _get_users_to_notify(self, db: Session, all_signals: Dict) -> Dict:
        """
        取得需要通知的用戶
        
        Returns:
            {user_id: {
                "line_user_id": "xxx",
                "display_name": "xxx",
                "signals": [...]
            }}
        """
        users_to_notify = {}
        
        # 取得所有用戶和他們的追蹤清單
        stmt = select(User).where(User.is_active == True, User.is_blocked == False)
        users = db.execute(stmt).scalars().all()
        
        for user in users:
            # 取得用戶的追蹤清單
            watchlist_stmt = select(Watchlist.symbol).where(
                Watchlist.user_id == user.id,
                Watchlist.asset_type == "stock"
            )
            user_symbols = set(db.execute(watchlist_stmt).scalars().all())
            
            # 取得用戶的通知設定（檢查是否開啟交叉通知）
            alert_stmt = select(UserAlertSettings).where(UserAlertSettings.user_id == user.id)
            alert_settings = db.execute(alert_stmt).scalar_one_or_none()
            
            # 預設開啟 MA 和 MACD 交叉通知
            alert_ma = True
            alert_macd = True
            alert_kd = False
            alert_rsi = True  # 預設開啟 RSI
            
            if alert_settings:
                alert_ma = alert_settings.alert_ma_cross
                alert_macd = alert_settings.alert_macd
                alert_kd = alert_settings.alert_kd
                alert_rsi = alert_settings.alert_rsi
            
            # 找出用戶追蹤中有訊號的股票
            user_signals = []
            for symbol, signals in all_signals.items():
                if symbol not in user_symbols:
                    continue
                
                for signal in signals:
                    # 檢查用戶是否開啟該類型的通知
                    if signal.signal_type in [SignalType.MA_GOLDEN_CROSS, SignalType.MA_DEATH_CROSS]:
                        if not alert_ma:
                            continue
                    elif signal.signal_type in [SignalType.MACD_GOLDEN_CROSS, SignalType.MACD_DEATH_CROSS]:
                        if not alert_macd:
                            continue
                    elif signal.signal_type in [SignalType.KD_GOLDEN_CROSS, SignalType.KD_DEATH_CROSS]:
                        if not alert_kd:
                            continue
                    elif signal.signal_type in [SignalType.RSI_OVERBOUGHT, SignalType.RSI_OVERSOLD]:
                        if not alert_rsi:
                            continue
                    
                    # 檢查 24 小時內是否已通知過
                    if self._has_recent_notification(db, user.id, symbol, signal.signal_type.value):
                        continue
                    
                    user_signals.append(signal)
            
            if user_signals:
                users_to_notify[user.id] = {
                    "user_id": user.id,
                    "line_user_id": user.line_user_id,
                    "display_name": user.display_name,
                    "signals": user_signals,
                }
        
        return users_to_notify
    
    def _has_recent_notification(self, db: Session, user_id: int, symbol: str, alert_type: str) -> bool:
        """檢查 24 小時內是否已發送過相同通知"""
        cutoff = datetime.now() - timedelta(hours=24)
        
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.symbol == symbol,
            Notification.alert_type == alert_type,
            Notification.triggered_at >= cutoff,
        )
        
        existing = db.execute(stmt).scalar_one_or_none()
        return existing is not None
    
    def _send_notification(self, db: Session, user_data: Dict) -> bool:
        """發送通知給用戶"""
        from app.services.line_notify_service import line_notify_service
        
        line_user_id = user_data["line_user_id"]
        signals = user_data["signals"]
        
        if not line_user_id or not signals:
            return False
        
        # 分類訊號
        bullish = []
        bearish = []
        
        for signal in signals:
            signal_name = signal_service.SIGNAL_NAMES.get(signal.signal_type, str(signal.signal_type))
            item = {
                "symbol": signal.symbol,
                "signal": signal_name,
                "price": signal.price,
                "signal_type": signal.signal_type.value,
            }
            
            # 判斷多空
            if signal.signal_type in [
                SignalType.MA_GOLDEN_CROSS, 
                SignalType.MACD_GOLDEN_CROSS, 
                SignalType.KD_GOLDEN_CROSS,
                SignalType.RSI_OVERSOLD,
            ]:
                bullish.append(item)
            else:
                bearish.append(item)
        
        # 格式化訊息
        message = self._format_notification_message(bullish, bearish)
        
        # 發送訊息（使用 asyncio 執行）
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(
                line_notify_service.push_text_message(line_user_id, message)
            )
            loop.close()
        except Exception as e:
            logger.error(f"發送 LINE 訊息失敗: {e}")
            success = False
        
        # 記錄通知
        for signal in signals:
            notification = Notification(
                user_id=user_data.get("user_id"),
                symbol=signal.symbol,
                asset_type=signal.asset_type,
                alert_type=signal.signal_type.value,
                indicator=signal.indicator,
                message=signal.message,
                price_at_trigger=signal.price,
                sent=success,
                sent_at=datetime.now() if success else None,
            )
            db.add(notification)
        
        db.commit()
        
        return success
    
    def _format_notification_message(self, bullish: List[Dict], bearish: List[Dict]) -> str:
        """格式化每日訊號通知訊息"""
        lines = ["📊 SELA 選股系統 - 每日訊號", ""]
        
        if bullish:
            lines.append("🟢 偏多訊號")
            for item in bullish:
                price_str = f" @ ${item['price']:.2f}" if item['price'] > 0 else ""
                lines.append(f"  • {item['symbol']}{price_str}")
                lines.append(f"    {item['signal']}")
            lines.append("")
        
        if bearish:
            lines.append("🔴 偏空訊號")
            for item in bearish:
                price_str = f" @ ${item['price']:.2f}" if item['price'] > 0 else ""
                lines.append(f"  • {item['symbol']}{price_str}")
                lines.append(f"    {item['signal']}")
            lines.append("")
        
        if not bullish and not bearish:
            lines.append("今日您的追蹤清單無重要訊號 ✨")
            lines.append("")
        
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(lines)
    
    def run_signal_detection_only(self) -> Dict[str, Any]:
        """
        只執行訊號偵測（不發送通知）
        用於測試
        """
        logger.info("開始訊號偵測（測試模式）...")
        
        result = {
            "signals": [],
            "by_symbol": {},
        }
        
        db = self._get_db()
        
        try:
            stmt = select(distinct(Watchlist.symbol)).where(Watchlist.asset_type == "stock")
            symbols = db.execute(stmt).scalars().all()
            
            for symbol in symbols:
                try:
                    signals = self._detect_signals_for_symbol(symbol)
                    cross_signals = [s for s in signals if s.signal_type in self.IMPORTANT_SIGNAL_TYPES]
                    
                    if cross_signals:
                        result["by_symbol"][symbol] = [
                            {
                                "type": s.signal_type.value,
                                "message": s.message,
                                "price": s.price,
                            }
                            for s in cross_signals
                        ]
                        result["signals"].extend(cross_signals)
                
                except Exception as e:
                    logger.error(f"{symbol} 偵測失敗: {e}")
        
        finally:
            db.close()
        
        return result

    def _update_watchlist_stocks(self, db: Session) -> Dict[str, Any]:
        """
        更新所有追蹤清單中的股票
        """
        result = {"count": 0, "errors": []}
        
        # 取得所有不重複的追蹤股票
        stmt = select(distinct(Watchlist.symbol)).where(Watchlist.asset_type == "stock")
        symbols = db.execute(stmt).scalars().all()
        
        logger.info(f"需要更新的股票: {len(symbols)} 檔")
        
        for symbol in symbols:
            try:
                # 從 Yahoo Finance 抓取最新資料
                df = yahoo_finance.get_stock_history(symbol, period="5d")
                
                if df is None or df.empty:
                    logger.warning(f"無法取得 {symbol} 的資料")
                    result["errors"].append(f"{symbol}: 無資料")
                    continue
                
                # 儲存到資料庫
                count = self._save_stock_prices(db, df)
                result["count"] += 1
                logger.debug(f"{symbol} 更新完成，新增 {count} 筆")
                
            except Exception as e:
                logger.error(f"更新 {symbol} 失敗: {e}")
                result["errors"].append(f"{symbol}: {str(e)}")
        
        return result
    
    def _save_stock_prices(self, db: Session, df) -> int:
        """儲存股票價格"""
        if df is None or df.empty:
            return 0
        
        count = 0
        for _, row in df.iterrows():
            stmt = select(StockPrice).where(
                and_(
                    StockPrice.symbol == row["symbol"],
                    StockPrice.date == row["date"],
                )
            )
            existing = db.execute(stmt).scalar_one_or_none()
            
            if existing:
                existing.open = row["open"]
                existing.high = row["high"]
                existing.low = row["low"]
                existing.close = row["close"]
                existing.volume = row["volume"]
            else:
                price = StockPrice(
                    symbol=row["symbol"],
                    date=row["date"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                )
                db.add(price)
                count += 1
        
        db.commit()
        return count
    
    def _update_indices(self, market_service: MarketService) -> Dict[str, int]:
        """
        更新三大指數（只更新最近 5 天）
        """
        result = {}
        
        for symbol in INDEX_SYMBOLS.keys():
            try:
                df = yahoo_finance.get_index_data(symbol, period="5d")
                if df is not None:
                    count = market_service.save_index_data(df, symbol)
                    result[symbol] = count
                else:
                    result[symbol] = 0
            except Exception as e:
                logger.error(f"更新指數 {symbol} 失敗: {e}")
                result[symbol] = -1
        
        return result
    
    def initialize_historical_data(self, years: int = 10) -> Dict[str, Any]:
        """
        初始化歷史資料（首次執行時使用）
        
        包含：
        1. 三大指數 10 年歷史
        2. 幣圈情緒 365 天歷史
        
        Args:
            years: 指數歷史年數
            
        Returns:
            執行結果
        """
        logger.info("=" * 50)
        logger.info("開始初始化歷史資料")
        logger.info("=" * 50)
        
        result = {
            "start_time": datetime.now().isoformat(),
            "indices": {},
            "crypto_sentiment": 0,
            "errors": [],
        }
        
        db = self._get_db()
        
        try:
            market_service = MarketService(db)
            
            # 1. 初始化三大指數
            logger.info(f"初始化三大指數 ({years} 年資料)...")
            indices_result = market_service.fetch_and_save_all_indices(period=f"{years}y")
            result["indices"] = indices_result
            
            # 2. 初始化幣圈情緒歷史
            logger.info("初始化幣圈情緒歷史 (365 天)...")
            crypto_count = market_service.fetch_and_save_crypto_history(days=365)
            result["crypto_sentiment"] = crypto_count
            
            result["success"] = True
            result["end_time"] = datetime.now().isoformat()
            
            logger.info("=" * 50)
            logger.info("歷史資料初始化完成")
            logger.info(f"指數: {result['indices']}")
            logger.info(f"幣圈情緒: {result['crypto_sentiment']} 筆")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"初始化失敗: {e}")
            result["errors"].append(str(e))
            result["success"] = False
        finally:
            db.close()
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """取得排程狀態"""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_result": self.last_result,
        }


# 建立全域排程服務實例
scheduler_service = SchedulerService()
