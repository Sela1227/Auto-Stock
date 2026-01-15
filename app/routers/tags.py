"""
標籤管理 API 路由
==================
追蹤清單分組 Tag 功能

P1 功能
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

router = APIRouter(prefix="/api/tags", tags=["標籤管理"])


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
    tag_ids: List[int] = Field(..., description="標籤 ID 列表")


# ============================================================
# 標籤 CRUD
# ============================================================

@router.get("", summary="取得我的標籤")
async def get_my_tags(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得用戶的所有標籤"""
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


@router.post("", summary="建立標籤")
async def create_tag(
    data: TagCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """建立新標籤"""
    # 檢查是否超過限制 (最多 20 個)
    count_stmt = select(UserTag).where(UserTag.user_id == user.id)
    count_result = await db.execute(count_stmt)
    existing_count = len(count_result.scalars().all())
    
    if existing_count >= 20:
        raise HTTPException(status_code=400, detail="最多只能建立 20 個標籤")
    
    # 檢查名稱是否重複
    check_stmt = select(UserTag).where(
        UserTag.user_id == user.id,
        UserTag.name == data.name
    )
    check_result = await db.execute(check_stmt)
    if check_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="標籤名稱已存在")
    
    # 建立標籤
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
    
    logger.info(f"用戶 {user.id} 建立標籤: {tag.name}")
    
    return {
        "success": True,
        "message": "標籤已建立",
        "data": tag.to_dict(),
    }


@router.put("/{tag_id}", summary="更新標籤")
async def update_tag(
    tag_id: int,
    data: TagUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """更新標籤"""
    stmt = select(UserTag).where(
        UserTag.id == tag_id,
        UserTag.user_id == user.id
    )
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="找不到標籤")
    
    # 檢查名稱是否與其他標籤重複
    if data.name and data.name != tag.name:
        check_stmt = select(UserTag).where(
            UserTag.user_id == user.id,
            UserTag.name == data.name,
            UserTag.id != tag_id
        )
        check_result = await db.execute(check_stmt)
        if check_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="標籤名稱已存在")
    
    # 更新欄位
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
        "message": "標籤已更新",
        "data": tag.to_dict(),
    }


@router.delete("/{tag_id}", summary="刪除標籤")
async def delete_tag(
    tag_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """刪除標籤"""
    stmt = select(UserTag).where(
        UserTag.id == tag_id,
        UserTag.user_id == user.id
    )
    result = await db.execute(stmt)
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="找不到標籤")
    
    # 刪除關聯和標籤
    await db.execute(
        delete(watchlist_tags).where(watchlist_tags.c.tag_id == tag_id)
    )
    await db.delete(tag)
    await db.commit()
    
    logger.info(f"用戶 {user.id} 刪除標籤: {tag.name}")
    
    return {
        "success": True,
        "message": "標籤已刪除",
    }


@router.post("/init-defaults", summary="初始化預設標籤")
async def init_default_tags(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """初始化預設標籤（僅限無標籤時）"""
    # 檢查是否已有標籤
    check_stmt = select(UserTag).where(UserTag.user_id == user.id)
    check_result = await db.execute(check_stmt)
    if check_result.scalars().first():
        return {
            "success": False,
            "message": "已有標籤存在，無法初始化",
        }
    
    # 建立預設標籤
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
        "message": f"已建立 {len(DEFAULT_TAGS)} 個預設標籤",
    }


# ============================================================
# 追蹤項目標籤管理
# ============================================================

@router.get("/watchlist/{watchlist_id}", summary="取得追蹤項目的標籤")
async def get_watchlist_tags(
    watchlist_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得追蹤項目的標籤"""
    # 確認追蹤項目屬於用戶
    watchlist_stmt = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == user.id
    )
    watchlist_result = await db.execute(watchlist_stmt)
    watchlist = watchlist_result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="找不到追蹤項目")
    
    # 取得關聯的標籤
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


@router.put("/watchlist/{watchlist_id}", summary="設定追蹤項目的標籤")
async def set_watchlist_tags(
    watchlist_id: int,
    data: WatchlistTagAssign,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """設定追蹤項目的標籤（覆蓋現有）"""
    # 確認追蹤項目屬於用戶
    watchlist_stmt = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == user.id
    )
    watchlist_result = await db.execute(watchlist_stmt)
    watchlist = watchlist_result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="找不到追蹤項目")
    
    # 驗證標籤都屬於用戶
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
            raise HTTPException(status_code=400, detail=f"無效的標籤 ID: {invalid_ids}")
    
    # 清除現有關聯
    await db.execute(
        delete(watchlist_tags).where(watchlist_tags.c.watchlist_id == watchlist_id)
    )
    
    # 建立新關聯
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
        "message": "標籤已更新",
        "watchlist_id": watchlist_id,
        "tag_ids": data.tag_ids,
    }


@router.post("/watchlist/{watchlist_id}/add/{tag_id}", summary="新增標籤到追蹤項目")
async def add_tag_to_watchlist(
    watchlist_id: int,
    tag_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """新增單一標籤到追蹤項目"""
    # 確認追蹤項目和標籤都屬於用戶
    watchlist_stmt = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == user.id
    )
    watchlist_result = await db.execute(watchlist_stmt)
    watchlist = watchlist_result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="找不到追蹤項目")
    
    tag_stmt = select(UserTag).where(
        UserTag.id == tag_id,
        UserTag.user_id == user.id
    )
    tag_result = await db.execute(tag_stmt)
    tag = tag_result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail="找不到標籤")
    
    # 檢查是否已存在
    from sqlalchemy import text
    check = await db.execute(
        text("SELECT 1 FROM watchlist_tags WHERE watchlist_id = :wid AND tag_id = :tid"),
        {"wid": watchlist_id, "tid": tag_id}
    )
    if check.scalar():
        return {
            "success": True,
            "message": "標籤已存在",
        }
    
    # 新增關聯
    await db.execute(
        watchlist_tags.insert().values(
            watchlist_id=watchlist_id,
            tag_id=tag_id
        )
    )
    await db.commit()
    
    return {
        "success": True,
        "message": f"已新增標籤 {tag.name}",
    }


@router.delete("/watchlist/{watchlist_id}/remove/{tag_id}", summary="從追蹤項目移除標籤")
async def remove_tag_from_watchlist(
    watchlist_id: int,
    tag_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """從追蹤項目移除標籤"""
    # 確認追蹤項目屬於用戶
    watchlist_stmt = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == user.id
    )
    watchlist_result = await db.execute(watchlist_stmt)
    if not watchlist_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="找不到追蹤項目")
    
    # 移除關聯
    await db.execute(
        delete(watchlist_tags).where(
            watchlist_tags.c.watchlist_id == watchlist_id,
            watchlist_tags.c.tag_id == tag_id
        )
    )
    await db.commit()
    
    return {
        "success": True,
        "message": "標籤已移除",
    }


# ============================================================
# 取得選項
# ============================================================

@router.get("/options/colors", summary="取得顏色選項")
async def get_color_options():
    """取得可用的標籤顏色"""
    return {
        "success": True,
        "colors": TAG_COLORS,
    }


@router.get("/options/icons", summary="取得圖示選項")
async def get_icon_options():
    """取得可用的標籤圖示"""
    return {
        "success": True,
        "icons": TAG_ICONS,
    }
