"""
統一認證依賴模組
=================
解決多個 router 重複定義 get_current_user 的問題

用法:
    from app.dependencies import get_current_user, get_admin_user
    
    @router.get("/my-data")
    async def my_endpoint(user: User = Depends(get_current_user)):
        ...
    
    @router.post("/admin/action")
    async def admin_endpoint(admin: User = Depends(get_admin_user)):
        ...
"""
from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.database import get_async_session
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    從 JWT Token 取得當前登入用戶（必須登入）
    
    Raises:
        HTTPException 401: 未提供 Token 或 Token 無效
    """
    from app.services.auth_service import AuthService
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="未提供認證 Token"
        )
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="無效的 Token"
        )
    
    return user


async def get_admin_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    要求管理員權限（必須是管理員）
    
    Raises:
        HTTPException 401: 未提供 Token 或 Token 無效
        HTTPException 403: 不是管理員
    """
    from app.services.auth_service import AuthService
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供認證 Token")
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="無效的 Token")
    
    # 檢查是否為管理員
    if not user.is_admin:
        # 檢查是否在環境變數的初始管理員名單中
        admin_ids = settings.get_admin_line_ids()
        if user.line_user_id not in admin_ids:
            raise HTTPException(status_code=403, detail="需要管理員權限")
        
        # 自動設定為管理員
        user.is_admin = True
        await db.commit()
        logger.info(f"Auto-promoted user {user.id} to admin")
    
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """
    可選認證 - 有 Token 就驗證，沒有也允許（返回 None）
    
    適用場景:
        - 公開 API 但登入用戶有額外功能
        - 需要判斷是否登入的混合頁面
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    try:
        from app.services.auth_service import AuthService
        token = auth_header.split(" ")[1]
        auth_service = AuthService(db)
        user = await auth_service.get_user_from_token(token)
        return user
    except Exception:
        return None
