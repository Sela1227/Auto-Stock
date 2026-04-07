"""
çµ±ä¸€èªè­‰ä¾è³´æ¨¡çµ„
=================
è§£æ±ºå¤šå€‹ router é‡è¤‡å®šç¾© get_current_user çš„å•é¡Œ

ç”¨æ³•:
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
    å¾ž JWT Token å–å¾—ç•¶å‰ç™»å…¥ç”¨æˆ¶ï¼ˆå¿…é ˆç™»å…¥ï¼‰
    
    Raises:
        HTTPException 401: æœªæä¾› Token æˆ– Token ç„¡æ•ˆ
    """
    from app.services.auth_service import AuthService
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="æœªæä¾›èªè­‰ Token"
        )
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="ç„¡æ•ˆçš„ Token"
        )
    
    return user


async def get_admin_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    è¦æ±‚ç®¡ç†å“¡æ¬Šé™ï¼ˆå¿…é ˆæ˜¯ç®¡ç†å“¡ï¼‰
    
    Raises:
        HTTPException 401: æœªæä¾› Token æˆ– Token ç„¡æ•ˆ
        HTTPException 403: ä¸æ˜¯ç®¡ç†å“¡
    """
    from app.services.auth_service import AuthService
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="æœªæä¾›èªè­‰ Token")
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="ç„¡æ•ˆçš„ Token")
    
    # æª¢æŸ¥æ˜¯å¦ç‚ºç®¡ç†å“¡
    if not user.is_admin:
        # æª¢æŸ¥æ˜¯å¦åœ¨ç’°å¢ƒè®Šæ•¸çš„åˆå§‹ç®¡ç†å“¡åå–®ä¸­
        admin_ids = settings.get_admin_line_ids()
        if user.line_user_id not in admin_ids:
            raise HTTPException(status_code=403, detail="éœ€è¦ç®¡ç†å“¡æ¬Šé™")
        
        # è‡ªå‹•è¨­å®šç‚ºç®¡ç†å“¡
        user.is_admin = True
        await db.commit()
        logger.info(f"Auto-promoted user {user.id} to admin")
    
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """
    å¯é¸èªè­‰ - æœ‰ Token å°±é©—è­‰ï¼Œæ²’æœ‰ä¹Ÿå…è¨±ï¼ˆè¿”å›ž Noneï¼‰
    
    é©ç”¨å ´æ™¯:
        - å…¬é–‹ API ä½†ç™»å…¥ç”¨æˆ¶æœ‰é¡å¤–åŠŸèƒ½
        - éœ€è¦åˆ¤æ–·æ˜¯å¦ç™»å…¥çš„æ··åˆé é¢
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