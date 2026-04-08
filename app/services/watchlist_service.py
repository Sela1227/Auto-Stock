"""
追蹤清單服務 (Async 版本)

🔧 修復版本 - 2026-01-16
- 新增追蹤後立即更新快取（加速追蹤清單載入）
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging
import pandas as pd

from app.models.watchlist import Watchlist
from app.models.user import User
from app.data_sources.coingecko import CRYPTO_MAP

logger = logging.getLogger(__name__)

# 支援的加密貨幣代號
SUPPORTED_CRYPTO = set(k for k in CRYPTO_MAP.keys() if k not in ("BITCOIN", "ETHEREUM"))


class WatchlistService:
    """追蹤清單服務 (Async)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _get_asset_type(self, symbol: str) -> str:
        """判斷資產類型"""
        return "crypto" if symbol.upper() in SUPPORTED_CRYPTO else "stock"
    
    async def add_to_watchlist(
        self,
        user_id: int,
        symbol: str,
        note: str = None,
    ) -> Dict[str, Any]:
        """
        新增追蹤標的
        
        🔧 優化版本：新增後立即更新快取
        
        Args:
            user_id: 用戶 ID
            symbol: 股票/加密貨幣代號
            note: 備註
            
        Returns:
            {
                "success": bool,
                "message": str,
                "watchlist": Watchlist (if success)
            }
        """
        symbol = symbol.upper()
        asset_type = self._get_asset_type(symbol)
        
        logger.info(f"=== 新增追蹤清單 ===")
        logger.info(f"用戶 ID: {user_id}, 代號: {symbol}, 類型: {asset_type}")
        
        # 檢查是否已存在
        existing = await self._get_watchlist_item(user_id, symbol, asset_type)
        if existing:
            logger.info(f"已存在追蹤: user_id={user_id}, symbol={symbol}")
            return {
                "success": False,
                "message": f"{symbol} 已在追蹤清單中",
            }
        
        # 驗證代號是否有效
        if asset_type == "crypto":
            from app.data_sources.coingecko import coingecko
            if not coingecko.validate_symbol(symbol):
                logger.warning(f"無效的加密貨幣: {symbol}")
                return {
                    "success": False,
                    "message": f"不支援的加密貨幣: {symbol}",
                }
        else:
            from app.data_sources.yahoo_finance import yahoo_finance
            if not yahoo_finance.validate_symbol(symbol):
                logger.warning(f"無效的股票代號: {symbol}")
                return {
                    "success": False,
                    "message": f"找不到股票: {symbol}",
                }
        
        # 新增
        watchlist = Watchlist(
            user_id=user_id,
            symbol=symbol,
            asset_type=asset_type,
            note=note,
        )
        self.db.add(watchlist)
        await self.db.commit()
        await self.db.refresh(watchlist)
        
        logger.info(f"★ 追蹤清單寫入成功: id={watchlist.id}, user_id={user_id}, symbol={symbol}")
        
        # 🆕 新增追蹤後立即更新快取（這樣追蹤清單馬上就有價格）
        try:
            await self._update_price_cache_for_symbol(symbol, asset_type)
            logger.info(f"✅ 已更新 {symbol} 快取")
        except Exception as e:
            logger.warning(f"更新 {symbol} 快取失敗: {e}")
            # 不影響主流程，快取會在下次排程更新
        
        return {
            "success": True,
            "message": f"已新增 {symbol} 到追蹤清單",
            "watchlist": watchlist,
        }
    
    async def _update_price_cache_for_symbol(self, symbol: str, asset_type: str):
        """
        🆕 更新單一股票/加密貨幣的價格快取
        用於新增追蹤後立即更新，不用等排程
        """
        from app.database import SyncSessionLocal
        from app.services.price_cache_service import PriceCacheService
        from app.data_sources.yahoo_finance import yahoo_finance
        from app.data_sources.coingecko import coingecko
        from app.services.indicator_service import indicator_service
        
        # 使用同步 session（因為 PriceCacheService 是同步的）
        sync_db = SyncSessionLocal()
        try:
            cache_service = PriceCacheService(sync_db)
            
            if asset_type == "crypto":
                # 加密貨幣
                price_data = coingecko.get_price(symbol)
                if price_data:
                    cache_service._upsert_cache(
                        symbol=symbol,
                        name=price_data.get("name", symbol),
                        price=price_data.get("price"),
                        prev_close=price_data.get("prev_close"),
                        change=price_data.get("change"),
                        change_pct=price_data.get("change_pct"),
                        volume=price_data.get("volume"),
                        asset_type="crypto",
                    )
                    sync_db.commit()
            else:
                # 股票
                df = yahoo_finance.get_stock_history(symbol, period="1mo")
                if df is not None and not df.empty:
                    # 計算 MA20
                    df = indicator_service.add_ma_indicators(df)
                    
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else None
                    
                    current_price = float(latest['close'])
                    prev_close = float(prev['close']) if prev is not None else None
                    change = current_price - prev_close if prev_close else None
                    change_pct = (change / prev_close * 100) if prev_close and change else None
                    ma20 = float(latest.get('ma20')) if 'ma20' in latest and not pd.isna(latest.get('ma20')) else None
                    
                    # 取得股票名稱
                    info = yahoo_finance.get_stock_info(symbol)
                    name = info.get("name", symbol) if info else symbol
                    
                    cache_service._upsert_cache(
                        symbol=symbol,
                        name=name,
                        price=current_price,
                        prev_close=prev_close,
                        change=change,
                        change_pct=change_pct,
                        volume=int(latest.get('volume', 0)),
                        asset_type="stock",
                        ma20=ma20,
                    )
                    sync_db.commit()
                    
        except Exception as e:
            logger.error(f"更新 {symbol} 快取失敗: {e}")
            raise
        finally:
            sync_db.close()
    
    async def remove_from_watchlist(
        self,
        user_id: int,
        symbol: str = None,
        watchlist_id: int = None,
    ) -> Dict[str, Any]:
        """
        從追蹤清單移除
        
        Args:
            user_id: 用戶 ID
            symbol: 代號（與 watchlist_id 二擇一）
            watchlist_id: 追蹤清單 ID
            
        Returns:
            {"success": bool, "message": str}
        """
        logger.info(f"=== 移除追蹤清單 ===")
        logger.info(f"用戶 ID: {user_id}, symbol: {symbol}, watchlist_id: {watchlist_id}")
        
        watchlist = None
        
        if watchlist_id:
            # 用 ID 查詢
            stmt = select(Watchlist).where(
                and_(
                    Watchlist.id == watchlist_id,
                    Watchlist.user_id == user_id,
                )
            )
            result = await self.db.execute(stmt)
            watchlist = result.scalar_one_or_none()
        elif symbol:
            # 用 symbol 查詢
            symbol = symbol.upper()
            asset_type = self._get_asset_type(symbol)
            watchlist = await self._get_watchlist_item(user_id, symbol, asset_type)
        
        if not watchlist:
            logger.warning(f"找不到追蹤: user_id={user_id}, symbol={symbol}, watchlist_id={watchlist_id}")
            return {
                "success": False,
                "message": "找不到該追蹤項目",
            }
        
        removed_symbol = watchlist.symbol
        await self.db.delete(watchlist)
        await self.db.commit()
        
        logger.info(f"★ 已移除追蹤: user_id={user_id}, symbol={removed_symbol}")
        
        return {
            "success": True,
            "message": f"已從追蹤清單移除 {removed_symbol}",
        }
    
    async def update_note(
        self,
        user_id: int,
        symbol: str,
        note: str,
    ) -> Dict[str, Any]:
        """
        更新備註
        """
        symbol = symbol.upper()
        asset_type = self._get_asset_type(symbol)
        
        watchlist = await self._get_watchlist_item(user_id, symbol, asset_type)
        
        if not watchlist:
            return {
                "success": False,
                "message": f"{symbol} 不在追蹤清單中",
            }
        
        watchlist.note = note
        await self.db.commit()
        
        return {
            "success": True,
            "message": f"已更新 {symbol} 的備註",
        }
    
    async def get_watchlist(self, user_id: int) -> List[Watchlist]:
        """
        取得用戶追蹤清單
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            追蹤清單列表
        """
        logger.debug(f"取得追蹤清單: user_id={user_id}")
        
        stmt = (
            select(Watchlist)
            .where(Watchlist.user_id == user_id)  # ★ 只取得該用戶的資料
            .order_by(Watchlist.added_at.desc())
        )
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())
        
        logger.info(f"取得追蹤清單: user_id={user_id}, 數量={len(items)}")
        for item in items:
            logger.debug(f"  - id={item.id}, symbol={item.symbol}, user_id={item.user_id}")
        
        return items
    
    async def get_watchlist_symbols(self, user_id: int) -> Dict[str, List[str]]:
        """
        取得用戶追蹤的代號列表（用於通知系統）
        
        Returns:
            {
                "stocks": ["AAPL", "TSLA"],
                "crypto": ["BTC", "ETH"]
            }
        """
        watchlists = await self.get_watchlist(user_id)
        
        stocks = []
        cryptos = []
        
        for item in watchlists:
            if item.asset_type == "stock":
                stocks.append(item.symbol)
            else:
                cryptos.append(item.symbol)
        
        return {
            "stocks": stocks,
            "crypto": cryptos,
        }
    
    async def _get_watchlist_item(
        self,
        user_id: int,
        symbol: str,
        asset_type: str,
    ) -> Optional[Watchlist]:
        """取得特定追蹤項目"""
        stmt = select(Watchlist).where(
            and_(
                Watchlist.user_id == user_id,
                Watchlist.symbol == symbol,
                Watchlist.asset_type == asset_type,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_tracked_symbols(self) -> Dict[str, set]:
        """
        取得所有用戶追蹤的代號（用於批次更新）
        
        Returns:
            {
                "stocks": {"AAPL", "TSLA", ...},
                "crypto": {"BTC", "ETH"}
            }
        """
        stmt = select(Watchlist.symbol, Watchlist.asset_type).distinct()
        result = await self.db.execute(stmt)
        results = result.all()
        
        stocks = set()
        cryptos = set()
        
        for symbol, asset_type in results:
            if asset_type == "stock":
                stocks.add(symbol)
            else:
                cryptos.add(symbol)
        
        return {
            "stocks": stocks,
            "crypto": cryptos,
        }
