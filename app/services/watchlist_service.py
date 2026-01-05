"""
追蹤清單服務
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import logging

from app.models.watchlist import Watchlist
from app.models.user import User
from app.services.stock_service import StockService
from app.services.crypto_service import CryptoService
from app.data_sources.coingecko import CRYPTO_MAP

logger = logging.getLogger(__name__)

# 支援的加密貨幣代號
SUPPORTED_CRYPTO = set(k for k in CRYPTO_MAP.keys() if k not in ("BITCOIN", "ETHEREUM"))


class WatchlistService:
    """追蹤清單服務"""
    
    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)
        self.crypto_service = CryptoService(db)
    
    def _get_asset_type(self, symbol: str) -> str:
        """判斷資產類型"""
        return "crypto" if symbol.upper() in SUPPORTED_CRYPTO else "stock"
    
    def add_to_watchlist(
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
        
        # 檢查是否已存在
        existing = self._get_watchlist_item(user_id, symbol, asset_type)
        if existing:
            return {
                "success": False,
                "message": f"{symbol} 已在追蹤清單中",
            }
        
        # 驗證代號是否有效
        if asset_type == "crypto":
            from app.data_sources.coingecko import coingecko
            if not coingecko.validate_symbol(symbol):
                return {
                    "success": False,
                    "message": f"不支援的加密貨幣: {symbol}",
                }
        else:
            from app.data_sources.yahoo_finance import yahoo_finance
            if not yahoo_finance.validate_symbol(symbol):
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
        self.db.commit()
        self.db.refresh(watchlist)
        
        logger.info(f"用戶 {user_id} 新增追蹤: {symbol} ({asset_type})")
        
        return {
            "success": True,
            "message": f"已新增 {symbol} 到追蹤清單",
            "watchlist": watchlist,
        }
    
    def remove_from_watchlist(
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
        if watchlist_id:
            stmt = select(Watchlist).where(
                and_(
                    Watchlist.id == watchlist_id,
                    Watchlist.user_id == user_id,
                )
            )
        elif symbol:
            symbol = symbol.upper()
            asset_type = self._get_asset_type(symbol)
            stmt = select(Watchlist).where(
                and_(
                    Watchlist.user_id == user_id,
                    Watchlist.symbol == symbol,
                    Watchlist.asset_type == asset_type,
                )
            )
        else:
            return {
                "success": False,
                "message": "請提供 symbol 或 watchlist_id",
            }
        
        watchlist = self.db.execute(stmt).scalar_one_or_none()
        
        if not watchlist:
            return {
                "success": False,
                "message": "找不到追蹤項目",
            }
        
        symbol = watchlist.symbol
        self.db.delete(watchlist)
        self.db.commit()
        
        logger.info(f"用戶 {user_id} 移除追蹤: {symbol}")
        
        return {
            "success": True,
            "message": f"已從追蹤清單移除 {symbol}",
        }
    
    def update_note(
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
        
        watchlist = self._get_watchlist_item(user_id, symbol, asset_type)
        if not watchlist:
            return {
                "success": False,
                "message": f"{symbol} 不在追蹤清單中",
            }
        
        watchlist.note = note
        self.db.commit()
        
        return {
            "success": True,
            "message": f"已更新 {symbol} 的備註",
        }
    
    def get_watchlist(self, user_id: int) -> List[Watchlist]:
        """
        取得用戶追蹤清單
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            追蹤清單列表
        """
        stmt = (
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .order_by(Watchlist.added_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
    
    def get_watchlist_overview(self, user_id: int) -> Dict[str, Any]:
        """
        取得追蹤清單總覽（含即時資訊）
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            {
                "stocks": [...],
                "crypto": [...],
                "sentiment": {...}
            }
        """
        watchlists = self.get_watchlist(user_id)
        
        stocks = []
        cryptos = []
        
        for item in watchlists:
            if item.asset_type == "stock":
                # 取得股票資訊
                analysis = self.stock_service.get_stock_analysis(item.symbol)
                if analysis:
                    stocks.append({
                        "id": item.id,
                        "symbol": item.symbol,
                        "name": analysis.get("name"),
                        "price": analysis["price"]["current"],
                        "change_day": analysis["change"].get("day"),
                        "ma_alignment": analysis["indicators"]["ma"].get("alignment"),
                        "rsi": analysis["indicators"]["rsi"].get("value"),
                        "score": analysis["score"],
                        "note": item.note,
                        "added_at": item.added_at.isoformat() if item.added_at else None,
                    })
            else:
                # 取得加密貨幣資訊
                analysis = self.crypto_service.get_crypto_analysis(item.symbol)
                if analysis:
                    cryptos.append({
                        "id": item.id,
                        "symbol": item.symbol,
                        "name": analysis.get("name"),
                        "price": analysis["price"]["current"],
                        "change_24h": analysis["change"].get("day"),
                        "ma_alignment": analysis["indicators"]["ma"].get("alignment"),
                        "rsi": analysis["indicators"]["rsi"].get("value"),
                        "score": analysis["score"],
                        "note": item.note,
                        "added_at": item.added_at.isoformat() if item.added_at else None,
                    })
        
        # 取得市場情緒
        sentiment = self.crypto_service.get_market_sentiment("all")
        
        return {
            "stocks": stocks,
            "crypto": cryptos,
            "sentiment": sentiment,
            "total_count": len(watchlists),
        }
    
    def get_watchlist_symbols(self, user_id: int) -> Dict[str, List[str]]:
        """
        取得用戶追蹤的代號列表（用於通知系統）
        
        Returns:
            {
                "stocks": ["AAPL", "TSLA"],
                "crypto": ["BTC", "ETH"]
            }
        """
        watchlists = self.get_watchlist(user_id)
        
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
    
    def _get_watchlist_item(
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
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_all_tracked_symbols(self) -> Dict[str, set]:
        """
        取得所有用戶追蹤的代號（用於批次更新）
        
        Returns:
            {
                "stocks": {"AAPL", "TSLA", ...},
                "crypto": {"BTC", "ETH"}
            }
        """
        stmt = select(Watchlist.symbol, Watchlist.asset_type).distinct()
        results = self.db.execute(stmt).all()
        
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
