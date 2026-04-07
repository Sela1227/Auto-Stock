"""
券商管理 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.database import get_async_session
from app.models.broker import Broker
from app.models.user import User
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brokers", tags=["券商管理"])


# ============================================================
# Schemas
# ============================================================

class BrokerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(default="#6B7280", max_length=20)
    is_default: Optional[bool] = False


class BrokerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    is_default: Optional[bool] = None


# ============================================================
# API 端點
# ============================================================

@router.get("", summary="取得券商列表")
async def get_brokers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得用戶的所有券商"""
    stmt = select(Broker).where(Broker.user_id == current_user.id).order_by(Broker.name)
    result = await db.execute(stmt)
    brokers = result.scalars().all()
    
    return {
        "success": True,
        "data": [b.to_dict() for b in brokers],
    }


@router.post("", summary="新增券商")
async def create_broker(
    data: BrokerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """新增券商"""
    # 檢查是否已存在同名券商
    stmt = select(Broker).where(
        Broker.user_id == current_user.id,
        Broker.name == data.name
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="券商名稱已存在")
    
    # 如果設為預設，先取消其他預設
    if data.is_default:
        await db.execute(
            update(Broker)
            .where(Broker.user_id == current_user.id)
            .values(is_default=False)
        )
    
    broker = Broker(
        user_id=current_user.id,
        name=data.name,
        color=data.color,
        is_default=data.is_default,
    )
    db.add(broker)
    await db.commit()
    await db.refresh(broker)
    
    return {
        "success": True,
        "message": "券商已新增",
        "data": broker.to_dict(),
    }


@router.put("/{broker_id}", summary="更新券商")
async def update_broker(
    broker_id: int,
    data: BrokerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """更新券商"""
    stmt = select(Broker).where(
        Broker.id == broker_id,
        Broker.user_id == current_user.id
    )
    result = await db.execute(stmt)
    broker = result.scalar_one_or_none()
    
    if not broker:
        raise HTTPException(status_code=404, detail="券商不存在")
    
    # 檢查名稱是否重複
    if data.name and data.name != broker.name:
        check_stmt = select(Broker).where(
            Broker.user_id == current_user.id,
            Broker.name == data.name,
            Broker.id != broker_id
        )
        check_result = await db.execute(check_stmt)
        if check_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="券商名稱已存在")
    
    # 如果設為預設，先取消其他預設
    if data.is_default:
        await db.execute(
            update(Broker)
            .where(Broker.user_id == current_user.id, Broker.id != broker_id)
            .values(is_default=False)
        )
    
    # 更新欄位
    if data.name is not None:
        broker.name = data.name
    if data.color is not None:
        broker.color = data.color
    if data.is_default is not None:
        broker.is_default = data.is_default
    
    await db.commit()
    await db.refresh(broker)
    
    return {
        "success": True,
        "message": "券商已更新",
        "data": broker.to_dict(),
    }


@router.delete("/{broker_id}", summary="刪除券商")
async def delete_broker(
    broker_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """刪除券商（交易記錄中的 broker_id 會變成 NULL）"""
    stmt = select(Broker).where(
        Broker.id == broker_id,
        Broker.user_id == current_user.id
    )
    result = await db.execute(stmt)
    broker = result.scalar_one_or_none()
    
    if not broker:
        raise HTTPException(status_code=404, detail="券商不存在")
    
    await db.delete(broker)
    await db.commit()
    
    return {
        "success": True,
        "message": "券商已刪除",
    }
