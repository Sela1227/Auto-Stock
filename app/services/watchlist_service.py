"""
追蹤清單服務 (Async 版本)
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

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
        
        return {
            "success": True,
            "message": f"已新增 {symbol} 到追蹤清單",
            "watchlist": watchlist,
        }
    
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
        logger.info(f"用戶 ID: {user_id}, 代號: {symbol}, watchlist_id: {watchlist_id}")
        
        if watchlist_id:
            stmt = select(Watchlist).where(
                and_(
                    Watchlist.id == watchlist_id,
                    Watchlist.user_id == user_id,  # ★ 確保只能刪除自己的
                )
            )
        elif symbol:
            symbol = symbol.upper()
            asset_type = self._get_asset_type(symbol)
            stmt = select(Watchlist).where(
                and_(
                    Watchlist.user_id == user_id,  # ★ 確保只能刪除自己的
                    Watchlist.symbol == symbol,
                    Watchlist.asset_type == asset_type,
                )
            )
        else:
            return {
                "success": False,
                "message": "請提供 symbol 或 watchlist_id",
            }
        
        result = await self.db.execute(stmt)
        watchlist = result.scalar_one_or_none()
        
        if not watchlist:
            logger.warning(f"找不到追蹤項目: user_id={user_id}, symbol={symbol}")
            return {
                "success": False,
                "message": "找不到追蹤項目",
            }
        
        # ★★★ 額外驗證：確保 watchlist 的 user_id 與請求的 user_id 一致 ★★★
        if watchlist.user_id != user_id:
            logger.error(f"權限錯誤！嘗試刪除他人資料: 請求 user_id={user_id}, 資料 user_id={watchlist.user_id}")
            return {
                "success": False,
                "message": "權限不足",
            }
        
        symbol = watchlist.symbol
        await self.db.delete(watchlist)
        await self.db.commit()
        
        logger.info(f"★ 追蹤清單刪除成功: user_id={user_id}, symbol={symbol}")
        
        return {
            "success": True,
            "message": f"已從追蹤清單移除 {symbol}",
        }
    
    async def update_note(
        self,
        user_id: int,
        symbol: str,
        note: str,
    ) -> Dict[str, Any]:
        """
        更新備註
        
        Args:
            user_id: 用戶 ID
            symbol: 代號
            note: 新備註
            
        Returns:
            {"success": bool, "message": str}
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
