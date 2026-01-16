"""
資料模型
"""
from app.models.stock_price import StockPrice
from app.models.crypto_price import CryptoPrice
from app.models.market_sentiment import MarketSentiment
from app.models.user import User, LoginLog, TokenBlacklist, SystemConfig
from app.models.watchlist import Watchlist
from app.models.user_settings import (
    UserIndicatorSettings,
    UserAlertSettings,
    UserIndicatorParams,
)
from app.models.notification import Notification
from app.models.index_price import IndexPrice, INDEX_SYMBOLS
from app.models.dividend_history import DividendHistory
from app.models.comparison import Comparison
from app.models.price_cache import StockPriceCache
from app.models.portfolio import PortfolioTransaction, PortfolioHolding, ExchangeRate

# 🏷️ P1: 標籤功能 - 必須在 Watchlist 之後 import
from app.models.watchlist_tag import UserTag, watchlist_tags

# 📊 P1: 股票資訊種子表
from app.models.stock_info import StockInfo

__all__ = [
    "StockPrice",
    "CryptoPrice", 
    "MarketSentiment",
    "User",
    "LoginLog",
    "TokenBlacklist",
    "SystemConfig",
    "Watchlist",
    "UserIndicatorSettings",
    "UserAlertSettings",
    "UserIndicatorParams",
    "Notification",
    "IndexPrice",
    "INDEX_SYMBOLS",
    "DividendHistory",
    "Comparison",
    "StockPriceCache",
    "PortfolioTransaction",
    "PortfolioHolding",
    "ExchangeRate",
    # P1
    "UserTag",
    "watchlist_tags",
    "StockInfo",
]
