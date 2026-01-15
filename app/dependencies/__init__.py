"""
依賴注入模組
統一管理認證、資料庫等共用依賴
"""
from app.dependencies.auth import (
    get_current_user,
    get_admin_user,
    get_optional_user,
)

__all__ = [
    "get_current_user",
    "get_admin_user", 
    "get_optional_user",
]
