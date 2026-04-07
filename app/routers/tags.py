"""
æ¨™ç±¤ç®¡ç† API è·¯ç”±
==================
è¿½è¹¤æ¸…å–®åˆ†çµ„ Tag åŠŸèƒ½

P1 åŠŸèƒ½
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from app.database import get_async_session
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.watchlist_tag import UserTag, watchlist_tags, TAG_COLORS, TAG_ICONS, DEFAULT_TAGS
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tags", tags=["æ¨™ç±¤ç®¡ç†"])


# ============================================================
# Schemas
# ============================================================

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$")
    icon: str = Field(default="fa-tag", max_length=50)


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = None


class WatchlistTagAssign(BaseModel):
    tag_ids: List[int] = Field(..., description="æ¨™ç±¤ ID åˆ—è¡¨")


# ============================================================
# æ¨™ç±¤ CRUD
# ============================================================

@router.get("", summary="å–å¾—æˆ‘çš„æ¨™ç±¤")
async def get_my_tags(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """å–å¾—ç”¨æˆ¶çš„æ‰€æœ‰æ¨™ç±¤"""
    stmt = (
        select(UserTag)
        .where(UserTag.user_id == user.id)
        .order_by(UserTag.sort_order, UserTag.id)
    )
    result = await db.execute(stmt)
    tags = result.scalars().all()
    
    return {
        "success": True,
        "data": [t.to_dict() for t in tags],
        "total": len(tags),
    }


@router.post("", summary="å»ºç«‹æ¨™ç±¤")
async def create_tag(
    data: TagCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """å»ºç«‹æ–°æ¨™ç±¤"""
    # æª¢æŸ¥æ˜¯å¦è¶…éŽé™åˆ¶ (æœ€å¤š 20 å€‹)
    count_stmt = select(UserTag).where(UserTag.user_id == user.id)
    count_result = await db.execute(count_stmt)
    existing_count = len(count_result.scalars().all())
    
    if existing_count >= 20:
        raise HTTPException(status_code=400, detail="æœ€å¤šåªèƒ½å»ºç«‹ 20 å€‹æ¨™ç±¤")
    
    # æª¢æŸ¥åç¨±æ˜¯å¦é‡è¤‡
    check_stmt = select(UserTag).where(
        UserTag.user_id == user.id,
        UserTag.name == data.name
    )
    check_result = await db.execute(check_stmt)
    if check_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="æ¨™ç±¤åç¨±å·²å­˜åœ¨")
    
    # å»ºç«‹æ¨™ç±¤
    tag = UserTag(
        user_id=user.id,
        name=data.name,
        color=data.color,
        icon=data.icon,
        sort_order=existing_count,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    
    logger.info(f"ç”¨æˆ¶ {user.id} å»ºç«‹æ¨™ç±¤: {tag.name}")
    
    return {
        "success": True,
        "message": "æ¨™ç±¤å·²å»ºç«‹",
        "data": tag.to_dict(),
    }


@router.put("/{tag_id}", summary="æ›´æ–°æ¨™ç±¤")
async def update_tag(
    tag_id: int,
    data: TagUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """æ›´æ–°æ¨™ç±¤"""
    stmt = select(UserTag).where(
        UserTag.id == tag_id,
        UserTag.user_id == user.id
    )
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="æ‰¾ä¸åˆ°æ¨™ç±¤")
    
    # æª¢æŸ¥åç¨±æ˜¯å¦èˆ‡å…¶ä»–æ¨™ç±¤é‡è¤‡
    if data.name and data.name != tag.name:
        check_stmt = select(UserTag).where(
            UserTag.user_id == user.id,
            UserTag.name == data.name,
            UserTag.id != tag_id
        )
        check_result = await db.execute(check_stmt)
        if check_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="æ¨™ç±¤åç¨±å·²å­˜åœ¨")
    
    # æ›´æ–°æ¬„ä½
    if data.name is not None:
        tag.name = data.name
    if data.color is not None:
        tag.color = data.color
    if data.icon is not None:
        tag.icon = data.icon
    if data.sort_order is not None:
        tag.sort_order = data.sort_order
    
    await db.commit()
    await db.refresh(tag)
    
    return {
        "success": True,
        "message": "æ¨™ç±¤å·²æ›´æ–°",
        "data": tag.to_dict(),
    }


@router.delete("/{tag_id}", summary="åˆªé™¤æ¨™ç±¤")
async def delete_tag(
    tag_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """åˆªé™¤æ¨™ç±¤"""
    stmt = select(UserTag).where(
        UserTag.id == tag_id,
        UserTag.user_id == user.id
    )
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="æ‰¾ä¸åˆ°æ¨™ç±¤")
    
    # åˆªé™¤é—œè¯å’Œæ¨™ç±¤
    await db.execute(
        delete(watchlist_tags).where(watchlist_tags.c.tag_id == tag_id)
    )
    await db.delete(tag)
    await db.commit()
    
    logger.info(f"ç”¨æˆ¶ {user.id} åˆªé™¤æ¨™ç±¤: {tag.name}")
    
    return {
        "success": True,
        "message": "æ¨™ç±¤å·²åˆªé™¤",
    }


@router.post("/init-defaults", summary="åˆå§‹åŒ–é è¨­æ¨™ç±¤")
async def init_default_tags(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """åˆå§‹åŒ–é è¨­æ¨™ç±¤ï¼ˆåƒ…é™ç„¡æ¨™ç±¤æ™‚ï¼‰"""
    # æª¢æŸ¥æ˜¯å¦å·²æœ‰æ¨™ç±¤
    check_stmt = select(UserTag).where(UserTag.user_id == user.id)
    check_result = await db.execute(check_stmt)
    if check_result.scalars().first():
        return {
            "success": False,
            "message": "å·²æœ‰æ¨™ç±¤å­˜åœ¨ï¼Œç„¡æ³•åˆå§‹åŒ–",
        }
    
    # å»ºç«‹é è¨­æ¨™ç±¤
    for i, tag_data in enumerate(DEFAULT_TAGS):
        tag = UserTag(
            user_id=user.id,
            name=tag_data["name"],
            color=tag_data["color"],
            icon=tag_data["icon"],
            sort_order=i,
        )
        db.add(tag)
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"å·²å»ºç«‹ {len(DEFAULT_TAGS)} å€‹é è¨­æ¨™ç±¤",
    }


# ============================================================
# è¿½è¹¤é …ç›®æ¨™ç±¤ç®¡ç†
# ============================================================

@router.get("/watchlist/{watchlist_id}", summary="å–å¾—è¿½è¹¤é …ç›®çš„æ¨™ç±¤")
async def get_watchlist_tags(
    watchlist_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """å–å¾—è¿½è¹¤é …ç›®çš„æ¨™ç±¤"""
    # ç¢ºèªè¿½è¹¤é …ç›®å±¬æ–¼ç”¨æˆ¶
    watchlist_stmt = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == user.id
    )
    watchlist_result = await db.execute(watchlist_stmt)
    watchlist = watchlist_result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="æ‰¾ä¸åˆ°è¿½è¹¤é …ç›®")
    
    # å–å¾—é—œè¯çš„æ¨™ç±¤
    tags_stmt = (
        select(UserTag)
        .join(watchlist_tags, UserTag.id == watchlist_tags.c.tag_id)
        .where(watchlist_tags.c.watchlist_id == watchlist_id)
    )
    tags_result = await db.execute(tags_stmt)
    tags = tags_result.scalars().all()
    
    return {
        "success": True,
        "watchlist_id": watchlist_id,
        "symbol": watchlist.symbol,
        "tags": [t.to_dict() for t in tags],
    }


@router.put("/watchlist/{watchlist_id}", summary="è¨­å®šè¿½è¹¤é …ç›®çš„æ¨™ç±¤")
async def set_watchlist_tags(
    watchlist_id: int,
    data: WatchlistTagAssign,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """è¨­å®šè¿½è¹¤é …ç›®çš„æ¨™ç±¤ï¼ˆè¦†è“‹ç¾æœ‰ï¼‰"""
    # ç¢ºèªè¿½è¹¤é …ç›®å±¬æ–¼ç”¨æˆ¶
    watchlist_stmt = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == user.id
    )
    watchlist_result = await db.execute(watchlist_stmt)
    watchlist = watchlist_result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="æ‰¾ä¸åˆ°è¿½è¹¤é …ç›®")
    
    # é©—è­‰æ¨™ç±¤éƒ½å±¬æ–¼ç”¨æˆ¶
    if data.tag_ids:
        tags_stmt = select(UserTag).where(
            UserTag.id.in_(data.tag_ids),
            UserTag.user_id == user.id
        )
        tags_result = await db.execute(tags_stmt)
        valid_tags = tags_result.scalars().all()
        valid_tag_ids = {t.id for t in valid_tags}
        
        invalid_ids = set(data.tag_ids) - valid_tag_ids
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"ç„¡æ•ˆçš„æ¨™ç±¤ ID: {invalid_ids}")
    
    # æ¸…é™¤ç¾æœ‰é—œè¯
    await db.execute(
        delete(watchlist_tags).where(watchlist_tags.c.watchlist_id == watchlist_id)
    )
    
    # å»ºç«‹æ–°é—œè¯
    if data.tag_ids:
        for tag_id in data.tag_ids:
            await db.execute(
                watchlist_tags.insert().values(
                    watchlist_id=watchlist_id,
                    tag_id=tag_id
                )
            )
    
    await db.commit()
    
    return {
        "success": True,
        "message": "æ¨™ç±¤å·²æ›´æ–°",
        "watchlist_id": watchlist_id,
        "tag_ids": data.tag_ids,
    }


@router.post("/watchlist/{watchlist_id}/add/{tag_id}", summary="æ–°å¢žæ¨™ç±¤åˆ°è¿½è¹¤é …ç›®")
async def add_tag_to_watchlist(
    watchlist_id: int,
    tag_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """æ–°å¢žå–®ä¸€æ¨™ç±¤åˆ°è¿½è¹¤é …ç›®"""
    # ç¢ºèªè¿½è¹¤é …ç›®å’Œæ¨™ç±¤éƒ½å±¬æ–¼ç”¨æˆ¶
    watchlist_stmt = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == user.id
    )
    watchlist_result = await db.execute(watchlist_stmt)
    watchlist = watchlist_result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="æ‰¾ä¸åˆ°è¿½è¹¤é …ç›®")
    
    tag_stmt = select(UserTag).where(
        UserTag.id == tag_id,
        UserTag.user_id == user.id
    )
    tag_result = await db.execute(tag_stmt)
    tag = tag_result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="æ‰¾ä¸åˆ°æ¨™ç±¤")
    
    # æª¢æŸ¥æ˜¯å¦å·²å­˜åœ¨
    from sqlalchemy import text
    check = await db.execute(
        text("SELECT 1 FROM watchlist_tags WHERE watchlist_id = :wid AND tag_id = :tid"),
        {"wid": watchlist_id, "tid": tag_id}
    )
    if check.scalar():
        return {
            "success": True,
            "message": "æ¨™ç±¤å·²å­˜åœ¨",
        }
    
    # æ–°å¢žé—œè¯
    await db.execute(
        watchlist_tags.insert().values(
            watchlist_id=watchlist_id,
            tag_id=tag_id
        )
    )
    await db.commit()
    
    return {
        "success": True,
        "message": f"å·²æ–°å¢žæ¨™ç±¤ {tag.name}",
    }


@router.delete("/watchlist/{watchlist_id}/remove/{tag_id}", summary="å¾žè¿½è¹¤é …ç›®ç§»é™¤æ¨™ç±¤")
async def remove_tag_from_watchlist(
    watchlist_id: int,
    tag_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """å¾žè¿½è¹¤é …ç›®ç§»é™¤æ¨™ç±¤"""
    # ç¢ºèªè¿½è¹¤é …ç›®å±¬æ–¼ç”¨æˆ¶
    watchlist_stmt = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == user.id
    )
    watchlist_result = await db.execute(watchlist_stmt)
    if not watchlist_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="æ‰¾ä¸åˆ°è¿½è¹¤é …ç›®")
    
    # ç§»é™¤é—œè¯
    await db.execute(
        delete(watchlist_tags).where(
            watchlist_tags.c.watchlist_id == watchlist_id,
            watchlist_tags.c.tag_id == tag_id
        )
    )
    await db.commit()
    
    return {
        "success": True,
        "message": "æ¨™ç±¤å·²ç§»é™¤",
    }


# ============================================================
# å–å¾—é¸é …
# ============================================================

@router.get("/options/colors", summary="å–å¾—é¡è‰²é¸é …")
async def get_color_options():
    """å–å¾—å¯ç”¨çš„æ¨™ç±¤é¡è‰²"""
    return {
        "success": True,
        "colors": TAG_COLORS,
    }


@router.get("/options/icons", summary="å–å¾—åœ–ç¤ºé¸é …")
async def get_icon_options():
    """å–å¾—å¯ç”¨çš„æ¨™ç±¤åœ–ç¤º"""
    return {
        "success": True,
        "icons": TAG_ICONS,
    }