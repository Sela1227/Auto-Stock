"""
設定管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_session
from app.services.auth_service import AuthService
from app.models.user import User
from app.models.user_settings import (
    UserIndicatorSettings,
    UserAlertSettings,
    UserIndicatorParams,
)
from app.schemas.schemas import (
    IndicatorSettingsUpdate,
    IndicatorSettingsResponse,
    AlertSettingsUpdate,
    AlertSettingsResponse,
    IndicatorParamsUpdate,
    IndicatorParamsResponse,
    ResponseBase,
)

router = APIRouter(prefix="/api/settings", tags=["設定"])


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """依賴注入：取得當前用戶"""
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


# ==================== 指標顯示設定 ====================

@router.get("/indicators", summary="取得指標顯示設定", response_model=IndicatorSettingsResponse)
async def get_indicator_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶的指標顯示設定
    """
    stmt = select(UserIndicatorSettings).where(
        UserIndicatorSettings.user_id == user.id
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    
    if not settings:
        # 建立預設設定
        settings = UserIndicatorSettings.create_default(user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return IndicatorSettingsResponse(
        success=True,
        data=settings.to_dict(),
    )


@router.put("/indicators", summary="更新指標顯示設定", response_model=IndicatorSettingsResponse)
async def update_indicator_settings(
    data: IndicatorSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    更新用戶的指標顯示設定
    """
    stmt = select(UserIndicatorSettings).where(
        UserIndicatorSettings.user_id == user.id
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserIndicatorSettings.create_default(user.id)
        db.add(settings)
    
    # 更新設定
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    await db.commit()
    await db.refresh(settings)
    
    return IndicatorSettingsResponse(
        success=True,
        message="設定已更新",
        data=settings.to_dict(),
    )


# ==================== 通知設定 ====================

@router.get("/alerts", summary="取得通知設定", response_model=AlertSettingsResponse)
async def get_alert_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶的通知設定
    """
    stmt = select(UserAlertSettings).where(
        UserAlertSettings.user_id == user.id
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserAlertSettings.create_default(user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return AlertSettingsResponse(
        success=True,
        data=settings.to_dict(),
    )


@router.put("/alerts", summary="更新通知設定", response_model=AlertSettingsResponse)
async def update_alert_settings(
    data: AlertSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    更新用戶的通知設定
    """
    stmt = select(UserAlertSettings).where(
        UserAlertSettings.user_id == user.id
    )
    result = await db.execute(stmt)
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserAlertSettings.create_default(user.id)
        db.add(settings)
    
    # 更新設定
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    await db.commit()
    await db.refresh(settings)
    
    return AlertSettingsResponse(
        success=True,
        message="設定已更新",
        data=settings.to_dict(),
    )


# ==================== 指標參數設定 ====================

@router.get("/params", summary="取得指標參數", response_model=IndicatorParamsResponse)
async def get_indicator_params(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶的指標參數設定
    """
    stmt = select(UserIndicatorParams).where(
        UserIndicatorParams.user_id == user.id
    )
    result = await db.execute(stmt)
    params = result.scalar_one_or_none()
    
    if not params:
        params = UserIndicatorParams.create_default(user.id)
        db.add(params)
        await db.commit()
        await db.refresh(params)
    
    return IndicatorParamsResponse(
        success=True,
        data=params.to_dict(),
    )


@router.put("/params", summary="更新指標參數", response_model=IndicatorParamsResponse)
async def update_indicator_params(
    data: IndicatorParamsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    更新用戶的指標參數設定
    
    可自訂參數包括：
    - 均線週期 (ma_short, ma_mid, ma_long)
    - RSI 參數 (rsi_period, rsi_overbought, rsi_oversold)
    - MACD 參數 (macd_fast, macd_slow, macd_signal)
    - KD 週期 (kd_period)
    - 布林通道 (bollinger_period, bollinger_std)
    - 警戒值 (breakout_threshold, volume_alert_ratio)
    """
    stmt = select(UserIndicatorParams).where(
        UserIndicatorParams.user_id == user.id
    )
    result = await db.execute(stmt)
    params = result.scalar_one_or_none()
    
    if not params:
        params = UserIndicatorParams.create_default(user.id)
        db.add(params)
    
    # 更新參數
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(params, key, value)
    
    await db.commit()
    await db.refresh(params)
    
    return IndicatorParamsResponse(
        success=True,
        message="參數已更新",
        data=params.to_dict(),
    )


# ==================== 預設模板 ====================

TEMPLATES = {
    "minimal": {
        "indicators": {
            "show_ma": True,
            "show_rsi": False,
            "show_macd": False,
            "show_kd": False,
            "show_bollinger": False,
            "show_obv": False,
            "show_volume": True,
        },
        "alerts": {
            "alert_ma_cross": True,
            "alert_ma_breakout": True,
            "alert_rsi": False,
            "alert_macd": False,
            "alert_kd": False,
            "alert_bollinger": False,
            "alert_volume": False,
            "alert_sentiment": False,
        },
    },
    "standard": {
        "indicators": {
            "show_ma": True,
            "show_rsi": True,
            "show_macd": True,
            "show_kd": False,
            "show_bollinger": True,
            "show_obv": False,
            "show_volume": True,
        },
        "alerts": {
            "alert_ma_cross": True,
            "alert_ma_breakout": True,
            "alert_rsi": True,
            "alert_macd": True,
            "alert_kd": False,
            "alert_bollinger": False,
            "alert_volume": False,
            "alert_sentiment": True,
        },
    },
    "full": {
        "indicators": {
            "show_ma": True,
            "show_rsi": True,
            "show_macd": True,
            "show_kd": True,
            "show_bollinger": True,
            "show_obv": True,
            "show_volume": True,
        },
        "alerts": {
            "alert_ma_cross": True,
            "alert_ma_breakout": True,
            "alert_rsi": True,
            "alert_macd": True,
            "alert_kd": True,
            "alert_bollinger": True,
            "alert_volume": True,
            "alert_sentiment": True,
        },
    },
    "short_term": {
        "indicators": {
            "show_ma": True,
            "show_rsi": True,
            "show_macd": True,
            "show_kd": True,
            "show_bollinger": True,
            "show_obv": False,
            "show_volume": True,
        },
        "alerts": {
            "alert_ma_cross": True,
            "alert_ma_breakout": True,
            "alert_rsi": True,
            "alert_macd": True,
            "alert_kd": True,
            "alert_bollinger": True,
            "alert_volume": True,
            "alert_sentiment": False,
        },
        "params": {
            "ma_short": 5,
            "ma_mid": 10,
            "ma_long": 20,
        },
    },
}


@router.post("/template/{template_name}", summary="套用預設模板", response_model=ResponseBase)
async def apply_template(
    template_name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    套用預設設定模板
    
    可用模板：
    - **minimal**: 極簡 (只顯示均線和成交量)
    - **standard**: 標準 (預設，含主要指標)
    - **full**: 完整 (顯示所有指標)
    - **short_term**: 短線 (使用較短的均線週期)
    """
    if template_name not in TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"不存在的模板: {template_name}"
        )
    
    template = TEMPLATES[template_name]
    
    # 更新指標設定
    if "indicators" in template:
        stmt = select(UserIndicatorSettings).where(
            UserIndicatorSettings.user_id == user.id
        )
        result = await db.execute(stmt)
        ind_settings = result.scalar_one_or_none()
        if not ind_settings:
            ind_settings = UserIndicatorSettings.create_default(user.id)
            db.add(ind_settings)
        
        for key, value in template["indicators"].items():
            setattr(ind_settings, key, value)
    
    # 更新通知設定
    if "alerts" in template:
        stmt = select(UserAlertSettings).where(
            UserAlertSettings.user_id == user.id
        )
        result = await db.execute(stmt)
        alert_settings = result.scalar_one_or_none()
        if not alert_settings:
            alert_settings = UserAlertSettings.create_default(user.id)
            db.add(alert_settings)
        
        for key, value in template["alerts"].items():
            setattr(alert_settings, key, value)
    
    # 更新參數設定
    if "params" in template:
        stmt = select(UserIndicatorParams).where(
            UserIndicatorParams.user_id == user.id
        )
        result = await db.execute(stmt)
        params = result.scalar_one_or_none()
        if not params:
            params = UserIndicatorParams.create_default(user.id)
            db.add(params)
        
        for key, value in template["params"].items():
            setattr(params, key, value)
    
    await db.commit()
    
    return ResponseBase(
        success=True,
        message=f"已套用模板: {template_name}",
    )
