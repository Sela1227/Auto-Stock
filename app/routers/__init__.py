"""
API 路由模組
"""
from app.routers.auth import router as auth_router
from app.routers.stock import router as stock_router
from app.routers.crypto import router as crypto_router
from app.routers.watchlist import router as watchlist_router
from app.routers.settings import router as settings_router
from app.routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "stock_router",
    "crypto_router",
    "watchlist_router",
    "settings_router",
    "admin_router",
]
