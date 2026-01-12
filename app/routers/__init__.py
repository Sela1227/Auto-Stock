"""
API 路由模組
"""
from app.routers.auth import router as auth_router
from app.routers.stock import router as stock_router
from app.routers.crypto import router as crypto_router
from app.routers.watchlist import router as watchlist_router
from app.routers.settings import router as settings_router
from app.routers.admin import router as admin_router
from app.routers.compare import router as compare_router
from app.routers.portfolio import router as portfolio_router  # 🆕 個人投資記錄

__all__ = [
    "auth_router",
    "stock_router",
    "crypto_router",
    "watchlist_router",
    "settings_router",
    "admin_router",
    "compare_router",
    "portfolio_router",  # 🆕 個人投資記錄
]
