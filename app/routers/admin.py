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
from app.services.exchange_rate_service import update_exchange_rate_sync  # 🆕 匯率更新
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


# ============== 訊號檢查與推播 ==============

@router.post("/signals/check", summary="執行訊號檢查")
async def run_signal_check(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    手動執行訊號檢查
    
    檢查所有用戶追蹤的股票，偵測技術指標訊號並發送 LINE 通知
    """
    from app.services.notification_service import notification_service
    
    try:
        result = await notification_service.run_signal_check(db)
        
        return {
            "success": True,
            "message": "訊號檢查完成",
            "result": result
        }
    except Exception as e:
        logger.error(f"訊號檢查失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/test/{symbol}", summary="測試單一股票訊號")
async def test_signal_detection(
    symbol: str,
    admin: User = Depends(get_admin_user),
):
    """
    測試單一股票的訊號偵測（不發送通知）
    """
    from app.services.signal_service import signal_service
    from app.services.indicator_service import indicator_service
    from app.data_sources.yahoo_finance import yahoo_finance
    
    symbol = symbol.upper()
    
    try:
        # 取得股價資料
        df = yahoo_finance.get_stock_history(symbol, period="6mo")
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"找不到股票: {symbol}")
        
        # 計算技術指標
        indicators = indicator_service.calculate_all_indicators(df)
        
        if not indicators:
            raise HTTPException(status_code=500, detail="無法計算技術指標")
        
        # 偵測訊號
        signals = signal_service.detect_signals(symbol, indicators, "stock")
        
        # 格式化輸出
        signals_data = []
        for s in signals:
            signals_data.append({
                "type": s.signal_type.value,
                "indicator": s.indicator,
                "message": s.message,
                "price": s.price,
                "details": s.details,
            })
        
        return {
            "success": True,
            "symbol": symbol,
            "current_price": indicators.get("current_price"),
            "signals_count": len(signals),
            "signals": signals_data,
            "indicators_summary": {
                "ma20": indicators.get("ma", {}).get("ma20"),
                "ma50": indicators.get("ma", {}).get("ma50"),
                "rsi": indicators.get("rsi", {}).get("value"),
                "macd_status": indicators.get("macd", {}).get("status"),
                "kd_k": indicators.get("kd", {}).get("k"),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"測試訊號偵測失敗 {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notify/test", summary="測試 LINE 推播")
async def test_line_push(
    message: str = Query("這是測試訊息", description="測試訊息內容"),
    admin: User = Depends(get_admin_user),
):
    """
    測試 LINE 推播功能（發送給管理員自己）
    """
    from app.services.line_notify_service import line_notify_service
    
    if not line_notify_service.enabled:
        raise HTTPException(
            status_code=400, 
            detail="LINE Messaging API 未設定，請設定 LINE_MESSAGING_CHANNEL_ACCESS_TOKEN 環境變數"
        )
    
    try:
        test_message = f"🔔 SELA 系統測試\n\n{message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        success = await line_notify_service.push_text_message(
            admin.line_user_id,
            test_message
        )
        
        if success:
            return {
                "success": True,
                "message": "測試訊息已發送，請檢查 LINE"
            }
        else:
            raise HTTPException(status_code=500, detail="LINE 推播失敗")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"測試 LINE 推播失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications", summary="通知記錄")
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[int] = None,
    symbol: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得通知記錄"""
    from app.models.notification import Notification
    
    query = select(Notification).order_by(Notification.triggered_at.desc())
    
    if user_id:
        query = query.where(Notification.user_id == user_id)
    
    if symbol:
        query = query.where(Notification.symbol == symbol.upper())
    
    # 計算總數
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分頁
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    # 取得用戶名稱
    user_ids = list(set(n.user_id for n in notifications))
    if user_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users_map = {u.id: u.display_name for u in users_result.scalars().all()}
    else:
        users_map = {}
    
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


@router.post("/signal/detect", summary="偵測訊號（測試）")
async def detect_signals(
    admin: User = Depends(get_admin_user),
):
    """
    手動執行訊號偵測（不發送通知）
    用於測試訊號偵測功能
    """
    from app.tasks.scheduler import scheduler_service
    
    try:
        result = scheduler_service.run_signal_detection_only()
        
        return {
            "success": True,
            "signals_count": len(result.get("signals", [])),
            "by_symbol": result.get("by_symbol", {}),
            "message": f"偵測到 {len(result.get('signals', []))} 個交叉訊號"
        }
    except Exception as e:
        logger.error(f"訊號偵測失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal/notify", summary="發送訊號通知")
async def send_signal_notifications(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    手動執行訊號偵測並發送通知
    會偵測所有追蹤股票的交叉訊號，並發送 LINE 推播給相關用戶
    """
    from app.tasks.scheduler import scheduler_service
    
    try:
        # 使用同步 session
        sync_db = scheduler_service._get_db()
        result = scheduler_service._detect_and_notify(sync_db)
        sync_db.close()
        
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
    from app.config import settings
    
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
    
    # 計算總數
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分頁
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    # 取得用戶名稱
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


# ============================================================
# 🆕 管理員觸發更新 API
# ============================================================

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
