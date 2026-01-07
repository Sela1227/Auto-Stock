"""
管理員 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timedelta
import logging

from app.database import get_async_session
from app.models.user import User, LoginLog, TokenBlacklist, SystemConfig
from app.services.auth_service import AuthService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["管理員"])


async def get_admin_user(request: Request, db: AsyncSession = Depends(get_async_session)) -> User:
    """驗證管理員身份"""
    # 從 Header 取得 Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供認證 Token")
    
    token = auth_header.split(" ")[1]
    
    # 驗證 Token 並取得用戶
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


@router.get("/stats", summary="系統統計")
async def get_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得系統統計資料"""
    # 用戶統計
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    blocked_users = await db.scalar(select(func.count(User.id)).where(User.is_blocked == True))
    admin_users = await db.scalar(select(func.count(User.id)).where(User.is_admin == True))
    
    # 總登入次數
    total_logins = await db.scalar(
        select(func.count(LoginLog.id))
        .where(LoginLog.action == "login")
    )
    
    # 今日登入
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logins = await db.scalar(
        select(func.count(LoginLog.id))
        .where(LoginLog.action == "login")
        .where(LoginLog.created_at >= today)
    )
    
    # 近 7 天活躍用戶
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_active = await db.scalar(
        select(func.count(func.distinct(LoginLog.user_id)))
        .where(LoginLog.created_at >= week_ago)
    )
    
    return {
        "success": True,
        "stats": {
            "total_users": total_users or 0,
            "active_users": active_users or 0,
            "blocked_users": blocked_users or 0,
            "admin_users": admin_users or 0,
            "total_logins": total_logins or 0,
            "today_logins": today_logins or 0,
            "weekly_active_users": weekly_active or 0,
        }
    }


@router.get("/users", summary="用戶列表")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    blocked_only: bool = False,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得用戶列表（含登入次數）"""
    query = select(User).order_by(User.last_login.desc())
    
    # 搜尋
    if search:
        query = query.where(
            (User.display_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.line_user_id.ilike(f"%{search}%"))
        )
    
    # 只顯示封鎖用戶
    if blocked_only:
        query = query.where(User.is_blocked == True)
    
    # 計算總數
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分頁
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # 取得每個用戶的登入次數
    user_ids = [u.id for u in users]
    login_counts = {}
    if user_ids:
        login_count_result = await db.execute(
            select(LoginLog.user_id, func.count(LoginLog.id).label('count'))
            .where(LoginLog.user_id.in_(user_ids))
            .where(LoginLog.action == "login")
            .group_by(LoginLog.user_id)
        )
        for row in login_count_result:
            login_counts[row.user_id] = row.count
    
    # 組合結果
    users_data = []
    for u in users:
        user_dict = u.to_dict()
        user_dict["login_count"] = login_counts.get(u.id, 0)
        users_data.append(user_dict)
    
    return {
        "success": True,
        "users": users_data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total or 0,
            "total_pages": ((total or 0) + page_size - 1) // page_size,
        }
    }


@router.get("/users/{user_id}", summary="用戶詳情")
async def get_user_detail(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得用戶詳細資訊"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    # 取得最近登入記錄
    logs_result = await db.execute(
        select(LoginLog)
        .where(LoginLog.user_id == user_id)
        .order_by(LoginLog.created_at.desc())
        .limit(20)
    )
    logs = logs_result.scalars().all()
    
    return {
        "success": True,
        "user": user.to_dict(),
        "recent_logs": [log.to_dict() for log in logs],
    }


@router.get("/logs", summary="登入日誌")
async def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得登入日誌"""
    query = select(LoginLog).order_by(LoginLog.created_at.desc())
    
    if user_id:
        query = query.where(LoginLog.user_id == user_id)
    
    if action:
        query = query.where(LoginLog.action == action)
    
    # 計算總數
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分頁
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # 取得用戶名稱
    user_ids = list(set(log.user_id for log in logs))
    if user_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users_map = {u.id: u.display_name for u in users_result.scalars().all()}
    else:
        users_map = {}
    
    logs_data = []
    for log in logs:
        log_dict = log.to_dict()
        log_dict["user_name"] = users_map.get(log.user_id, "Unknown")
        logs_data.append(log_dict)
    
    return {
        "success": True,
        "logs": logs_data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total or 0,
            "total_pages": ((total or 0) + page_size - 1) // page_size,
        }
    }


@router.post("/users/{user_id}/block", summary="封鎖用戶")
async def block_user(
    user_id: int,
    reason: str = Query("", description="封鎖原因"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """封鎖用戶"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能封鎖自己")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    user.is_blocked = True
    user.blocked_reason = reason
    user.blocked_at = datetime.utcnow()
    
    # 記錄日誌
    log = LoginLog(
        user_id=user_id,
        action="blocked",
        ip_address=f"by_admin:{admin.id}",
    )
    db.add(log)
    
    await db.commit()
    
    logger.info(f"User {user_id} blocked by admin {admin.id}, reason: {reason}")
    
    return {"success": True, "message": f"已封鎖用戶 {user.display_name}"}


@router.post("/users/{user_id}/unblock", summary="解除封鎖")
async def unblock_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """解除用戶封鎖"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    user.is_blocked = False
    user.blocked_reason = None
    user.blocked_at = None
    
    # 記錄日誌
    log = LoginLog(
        user_id=user_id,
        action="unblocked",
        ip_address=f"by_admin:{admin.id}",
    )
    db.add(log)
    
    await db.commit()
    
    logger.info(f"User {user_id} unblocked by admin {admin.id}")
    
    return {"success": True, "message": f"已解除封鎖 {user.display_name}"}


@router.post("/users/{user_id}/set-admin", summary="設為管理員")
async def set_admin(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """設定用戶為管理員"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    user.is_admin = True
    await db.commit()
    
    logger.info(f"User {user_id} promoted to admin by {admin.id}")
    
    return {"success": True, "message": f"已將 {user.display_name} 設為管理員"}


@router.post("/users/{user_id}/remove-admin", summary="移除管理員")
async def remove_admin(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """移除管理員權限"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能移除自己的管理員權限")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    user.is_admin = False
    await db.commit()
    
    logger.info(f"User {user_id} admin removed by {admin.id}")
    
    return {"success": True, "message": f"已移除 {user.display_name} 的管理員權限"}


@router.post("/users/{user_id}/kick", summary="踢出用戶")
async def kick_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """踢出單一用戶（使其 Token 失效）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    # 增加 token 版本，使舊 token 失效
    # 這裡我們用時間戳記錄
    config_key = f"user_token_version:{user_id}"
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == config_key)
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.value = str(int(datetime.utcnow().timestamp()))
    else:
        config = SystemConfig(
            key=config_key,
            value=str(int(datetime.utcnow().timestamp())),
            description=f"Token version for user {user_id}"
        )
        db.add(config)
    
    # 記錄日誌
    log = LoginLog(
        user_id=user_id,
        action="kicked",
        ip_address=f"by_admin:{admin.id}",
    )
    db.add(log)
    
    await db.commit()
    
    logger.info(f"User {user_id} kicked by admin {admin.id}")
    
    return {"success": True, "message": f"已踢出用戶 {user.display_name}"}


@router.post("/kick-all", summary="踢出所有用戶")
async def kick_all_users(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """踢出所有用戶（使所有 Token 失效）"""
    # 設定全域 token 版本
    config_key = "global_token_version"
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == config_key)
    )
    config = result.scalar_one_or_none()
    
    new_version = str(int(datetime.utcnow().timestamp()))
    
    if config:
        config.value = new_version
    else:
        config = SystemConfig(
            key=config_key,
            value=new_version,
            description="Global token version for kick-all"
        )
        db.add(config)
    
    # 記錄日誌
    log = LoginLog(
        user_id=admin.id,
        action="kick_all",
        ip_address=f"admin:{admin.id}",
    )
    db.add(log)
    
    await db.commit()
    
    logger.warning(f"All users kicked by admin {admin.id}")
    
    return {
        "success": True,
        "message": "已踢出所有用戶，所有人需要重新登入",
        "new_version": new_version
    }


@router.delete("/users/{user_id}", summary="刪除用戶")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """刪除用戶（危險操作）"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能刪除自己")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    display_name = user.display_name
    
    await db.delete(user)
    await db.commit()
    
    logger.warning(f"User {user_id} ({display_name}) deleted by admin {admin.id}")
    
    return {"success": True, "message": f"已刪除用戶 {display_name}"}


@router.get("/debug/watchlists", summary="診斷追蹤清單")
async def debug_watchlists(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    診斷追蹤清單（查看所有用戶的追蹤清單數量）
    """
    from app.models.watchlist import Watchlist
    
    # 統計每個用戶的追蹤清單數量
    result = await db.execute(
        select(
            Watchlist.user_id,
            func.count(Watchlist.id).label('count')
        ).group_by(Watchlist.user_id)
    )
    user_counts = result.all()
    
    # 取得用戶資訊
    user_data = []
    for user_id, count in user_counts:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        user_data.append({
            "user_id": user_id,
            "display_name": user.display_name if user else "未知",
            "line_user_id": user.line_user_id[:10] + "..." if user else "未知",
            "watchlist_count": count
        })
    
    # 總數
    total = await db.scalar(select(func.count(Watchlist.id)))
    
    return {
        "success": True,
        "total_watchlist_items": total,
        "users": user_data
    }
