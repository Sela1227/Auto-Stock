"""
åˆ¸å•†ç®¡ç† API
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

router = APIRouter(prefix="/api/brokers", tags=["åˆ¸å•†ç®¡ç†"])


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
# API ç«¯é»ž
# ============================================================

@router.get("", summary="å–å¾—åˆ¸å•†åˆ—è¡¨")
async def get_brokers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """å–å¾—ç”¨æˆ¶çš„æ‰€æœ‰åˆ¸å•†"""
    stmt = select(Broker).where(Broker.user_id == current_user.id).order_by(Broker.name)
    result = await db.execute(stmt)
    brokers = result.scalars().all()
    
    return {
        "success": True,
        "data": [b.to_dict() for b in brokers],
    }


@router.post("", summary="æ–°å¢žåˆ¸å•†")
async def create_broker(
    data: BrokerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """æ–°å¢žåˆ¸å•†"""
    # æª¢æŸ¥æ˜¯å¦å·²å­˜åœ¨åŒååˆ¸å•†
    stmt = select(Broker).where(
        Broker.user_id == current_user.id,
        Broker.name == data.name
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="åˆ¸å•†åç¨±å·²å­˜åœ¨")
    
    # å¦‚æžœè¨­ç‚ºé è¨­ï¼Œå…ˆå–æ¶ˆå…¶ä»–é è¨­
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
        "message": "åˆ¸å•†å·²æ–°å¢ž",
        "data": broker.to_dict(),
    }


@router.put("/{broker_id}", summary="æ›´æ–°åˆ¸å•†")
async def update_broker(
    broker_id: int,
    data: BrokerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """æ›´æ–°åˆ¸å•†"""
    stmt = select(Broker).where(
        Broker.id == broker_id,
        Broker.user_id == current_user.id
    )
    result = await db.execute(stmt)
    broker = result.scalar_one_or_none()
    
    if not broker:
        raise HTTPException(status_code=404, detail="åˆ¸å•†ä¸å­˜åœ¨")
    
    # æª¢æŸ¥åç¨±æ˜¯å¦é‡è¤‡
    if data.name and data.name != broker.name:
        check_stmt = select(Broker).where(
            Broker.user_id == current_user.id,
            Broker.name == data.name,
            Broker.id != broker_id
        )
        check_result = await db.execute(check_stmt)
        if check_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="åˆ¸å•†åç¨±å·²å­˜åœ¨")
    
    # å¦‚æžœè¨­ç‚ºé è¨­ï¼Œå…ˆå–æ¶ˆå…¶ä»–é è¨­
    if data.is_default:
        await db.execute(
            update(Broker)
            .where(Broker.user_id == current_user.id, Broker.id != broker_id)
            .values(is_default=False)
        )
    
    # æ›´æ–°æ¬„ä½
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
        "message": "åˆ¸å•†å·²æ›´æ–°",
        "data": broker.to_dict(),
    }


@router.delete("/{broker_id}", summary="åˆªé™¤åˆ¸å•†")
async def delete_broker(
    broker_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """åˆªé™¤åˆ¸å•†ï¼ˆäº¤æ˜“è¨˜éŒ„ä¸­çš„ broker_id æœƒè®Šæˆ NULLï¼‰"""
    stmt = select(Broker).where(
        Broker.id == broker_id,
        Broker.user_id == current_user.id
    )
    result = await db.execute(stmt)
    broker = result.scalar_one_or_none()
    
    if not broker:
        raise HTTPException(status_code=404, detail="åˆ¸å•†ä¸å­˜åœ¨")
    
    await db.delete(broker)
    await db.commit()
    
    return {
        "success": True,
        "message": "åˆ¸å•†å·²åˆªé™¤",
    }