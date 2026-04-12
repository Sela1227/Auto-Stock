"""
管理員 API 路由
🔧 P0修復：使用統一認證模組
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
from app.services.exchange_rate_service import update_exchange_rate_sync
from app.config import settings

from app.dependencies import get_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["管理員"])


@router.get("/stats", summary="系統統計")
async def get_stats(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得系統統計資料"""
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    blocked_users = await db.scalar(select(func.count(User.id)).where(User.is_blocked == True))
    admin_users = await db.scalar(select(func.count(User.id)).where(User.is_admin == True))
    
    total_logins = await db.scalar(
        select(func.count(LoginLog.id))
        .where(LoginLog.action == "login")
    )
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logins = await db.scalar(
        select(func.count(LoginLog.id))
        .where(LoginLog.action == "login")
        .where(LoginLog.created_at >= today)
    )
    
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
    
    if search:
        query = query.where(
            (User.display_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.line_user_id.ilike(f"%{search}%"))
        )
    
    if blocked_only:
        query = query.where(User.is_blocked == True)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
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
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()
    
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
    
    if user.is_admin:
        raise HTTPException(status_code=400, detail="不能封鎖管理員")
    
    user.is_blocked = True
    user.block_reason = reason
    
    log = LoginLog(
        user_id=user_id,
        action="blocked",
        ip_address=None,
        user_agent=f"By admin: {admin.display_name}",
    )
    db.add(log)
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"已封鎖用戶: {user.display_name}",
    }


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
    user.block_reason = None
    
    log = LoginLog(
        user_id=user_id,
        action="unblocked",
        ip_address=None,
        user_agent=f"By admin: {admin.display_name}",
    )
    db.add(log)
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"已解除封鎖: {user.display_name}",
    }


@router.post("/users/{user_id}/set-admin", summary="設定管理員")
async def set_admin(
    user_id: int,
    is_admin: bool = Query(..., description="是否為管理員"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """設定或取消管理員權限"""
    if user_id == admin.id and not is_admin:
        raise HTTPException(status_code=400, detail="不能取消自己的管理員權限")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    user.is_admin = is_admin
    
    action = "promoted_to_admin" if is_admin else "demoted_from_admin"
    log = LoginLog(
        user_id=user_id,
        action=action,
        ip_address=None,
        user_agent=f"By admin: {admin.display_name}",
    )
    db.add(log)
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"已{'設定' if is_admin else '取消'} {user.display_name} 的管理員權限",
    }


@router.delete("/users/{user_id}", summary="刪除用戶")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """刪除用戶（僅限測試環境）"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能刪除自己")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    if user.is_admin:
        raise HTTPException(status_code=400, detail="不能刪除管理員")
    
    await db.execute(delete(LoginLog).where(LoginLog.user_id == user_id))
    await db.delete(user)
    await db.commit()
    
    return {
        "success": True,
        "message": f"已刪除用戶: {user.display_name}",
    }



@router.get("/config", summary="取得系統設定")
async def get_config(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得系統設定"""
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    
    return {
        "success": True,
        "configs": {c.key: c.value for c in configs},
    }


@router.put("/config/{key}", summary="更新系統設定")
async def update_config(
    key: str,
    value: str = Query(..., description="設定值"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """更新系統設定"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    
    if config:
        config.value = value
    else:
        config = SystemConfig(key=key, value=value)
        db.add(config)
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"已更新設定: {key}",
    }



@router.post("/signal/send-now", summary="立即發送訊號通知")
async def send_signal_now(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    立即執行訊號偵測並發送通知
    """
    from app.tasks.scheduler import scheduler_service
    
    logger.info(f"管理員 {admin.display_name} 觸發立即發送訊號通知")
    
    try:
        result = scheduler_service.run_signal_notification()
        
        return {
            "success": True,
            "signals_detected": result.get("signals_count", 0),
            "notifications_sent": result.get("notifications_sent", 0),
            "errors": result.get("errors", []),
            "message": f"偵測到 {result.get('signals_count', 0)} 個訊號，發送 {result.get('notifications_sent', 0)} 則通知"
        }
    except Exception as e:
        logger.error(f"訊號通知失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal/test-push", summary="測試 LINE 推播")
async def test_line_push(
    message: str = Query("這是測試訊息", description="測試訊息內容"),
    admin: User = Depends(get_admin_user),
):
    """
    測試 LINE 推播功能
    發送測試訊息給管理員自己
    """
    from app.services.line_notify_service import line_notify_service
    
    if not line_notify_service.enabled:
        return {
            "success": False,
            "message": "LINE Messaging API 未啟用，請設定 LINE_MESSAGING_CHANNEL_ACCESS_TOKEN"
        }
    
    try:
        test_message = f"📊 SELA 系統測試\n\n{message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        success = await line_notify_service.push_text_message(admin.line_user_id, test_message)
        
        return {
            "success": success,
            "message": "測試訊息已發送" if success else "發送失敗",
            "line_user_id": admin.line_user_id[:10] + "..."
        }
    except Exception as e:
        logger.error(f"測試推播失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signal/status", summary="通知系統狀態")
async def get_signal_status(
    admin: User = Depends(get_admin_user),
):
    """
    取得訊號通知系統狀態
    """
    from app.services.line_notify_service import line_notify_service
    from app.tasks.scheduler import scheduler_service
    
    return {
        "success": True,
        "status": {
            "line_messaging_enabled": line_notify_service.enabled,
            "line_messaging_token_set": bool(settings.LINE_MESSAGING_CHANNEL_ACCESS_TOKEN),
            "scheduler_last_run": scheduler_service.last_run.isoformat() if scheduler_service.last_run else None,
            "scheduler_last_result": scheduler_service.last_result,
        }
    }


@router.post("/signal/detect", summary="手動偵測訊號")
async def detect_signals_manual(
    admin: User = Depends(get_admin_user),
):
    """
    手動執行訊號偵測（不發送通知）
    用於測試訊號偵測邏輯
    """
    from app.tasks.scheduler import scheduler_service
    
    try:
        result = scheduler_service.run_signal_detection_only()
        
        return {
            "success": True,
            "message": f"偵測完成，共 {len(result.get('signals', []))} 個訊號",
            "signals_by_symbol": result.get("by_symbol", {}),
            "total_signals": len(result.get("signals", [])),
        }
    except Exception as e:
        logger.error(f"訊號偵測失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal/notify", summary="手動發送通知")
async def send_notifications_manual(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    手動執行訊號偵測並發送通知
    等同於每日排程任務
    """
    from app.tasks.scheduler import scheduler_service
    
    try:
        result = scheduler_service.run_daily_update()
        
        return {
            "success": result.get("success", False),
            "message": "每日更新任務已執行",
            "result": {
                "stocks_updated": result.get("stocks_updated", 0),
                "signals_detected": result.get("signals_detected", 0),
                "notifications_sent": result.get("notifications_sent", 0),
                "errors": result.get("errors", []),
            }
        }
    except Exception as e:
        logger.error(f"通知任務失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications", summary="通知記錄")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    symbol: Optional[str] = None,
    sent_only: bool = False,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得通知記錄
    """
    from app.models.notification import Notification
    
    query = select(Notification).order_by(Notification.triggered_at.desc())
    
    if user_id:
        query = query.where(Notification.user_id == user_id)
    
    if symbol:
        query = query.where(Notification.symbol == symbol.upper())
    
    if sent_only:
        query = query.where(Notification.sent == True)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    user_ids = list(set(n.user_id for n in notifications))
    users_map = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u.display_name for u in users_result.scalars().all()}
    
    notifications_data = []
    for n in notifications:
        n_dict = n.to_dict()
        n_dict["user_name"] = users_map.get(n.user_id, "Unknown")
        notifications_data.append(n_dict)
    
    return {
        "success": True,
        "notifications": notifications_data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total or 0,
            "total_pages": ((total or 0) + page_size - 1) // page_size,
        }
    }



@router.post("/update-exchange-rate", summary="更新匯率")
async def admin_update_exchange_rate(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    管理員手動觸發 USD/TWD 匯率更新
    """
    from app.database import SyncSessionLocal
    
    logger.info(f"管理員 {admin.display_name} 觸發匯率更新")
    
    try:
        sync_db = SyncSessionLocal()
        try:
            rate = update_exchange_rate_sync(sync_db)
            return {
                "success": True,
                "message": f"匯率已更新: USD/TWD = {rate:.4f}",
                "rate": rate,
            }
        finally:
            sync_db.close()
    except Exception as e:
        logger.error(f"匯率更新失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-indices", summary="更新四大指數")
async def admin_update_indices(
    admin: User = Depends(get_admin_user),
):
    """
    管理員手動觸發四大指數更新
    """
    from app.services.index_service import update_all_indices
    
    logger.info(f"管理員 {admin.display_name} 觸發四大指數更新")
    
    try:
        result = update_all_indices()
        return {
            "success": True,
            "message": "四大指數已更新",
            "updated": result.get("updated", 0),
            "errors": result.get("errors", []),
        }
    except Exception as e:
        logger.error(f"四大指數更新失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-price-cache", summary="更新價格快取")
async def admin_update_price_cache(
    admin: User = Depends(get_admin_user),
):
    """
    管理員手動觸發追蹤清單價格快取更新
    """
    from app.database import SyncSessionLocal
    from app.services.price_cache_service import PriceCacheService
    
    logger.info(f"管理員 {admin.display_name} 觸發價格快取更新")
    
    try:
        sync_db = SyncSessionLocal()
        try:
            service = PriceCacheService(sync_db)
            result = service.update_all(force=True)
            return {
                "success": True,
                "message": "價格快取已更新",
                "total_updated": result.get("total_updated", 0),
                "errors": result.get("errors", []),
            }
        finally:
            sync_db.close()
    except Exception as e:
        logger.error(f"價格快取更新失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
