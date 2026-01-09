"""
報酬率比較 API 路由
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_async_session
from app.services.compare_service import compare_service, ComparisonCRUD
from app.services.auth_service import AuthService
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compare", tags=["Compare"])


# ==================== 認證依賴 ====================

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """依賴注入：取得當前用戶"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Compare API: 未提供認證 Token")
        raise HTTPException(
            status_code=401,
            detail="未提供認證 Token"
        )
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        logger.warning("Compare API: Token 驗證失敗")
        raise HTTPException(
            status_code=401,
            detail="無效的 Token"
        )
    
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> Optional[User]:
    """依賴注入：取得當前用戶（可選，未登入返回 None）"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    return user


# ==================== Schemas ====================

class CompareRequest(BaseModel):
    """比較請求"""
    symbols: List[str] = Field(..., min_length=1, max_length=5, description="標的代號列表")
    periods: List[str] = Field(default=["1y", "3y", "5y", "10y"], description="時間週期")
    custom_range: Optional[dict] = Field(default=None, description="自訂區間 {start, end}")
    benchmark: str = Field(default="^GSPC", description="基準指數")
    sort_by: str = Field(default="5y", description="排序依據")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")


class SaveComparisonRequest(BaseModel):
    """儲存比較組合請求"""
    name: str = Field(..., min_length=1, max_length=100, description="組合名稱")
    symbols: List[str] = Field(..., min_length=1, max_length=5, description="標的代號列表")
    benchmark: str = Field(default="^GSPC", description="基準指數")


class UpdateComparisonRequest(BaseModel):
    """更新比較組合請求"""
    name: Optional[str] = Field(default=None, max_length=100)
    symbols: Optional[List[str]] = Field(default=None, max_length=5)
    benchmark: Optional[str] = Field(default=None)


# ==================== 公開 API ====================

@router.post("/cagr", summary="計算年化報酬率比較")
async def compare_cagr(request: CompareRequest):
    """
    比較多個標的的年化報酬率 (CAGR)
    
    - 支援股票、加密貨幣、指數混合比較
    - 最多 5 個標的
    - 可選時間週期：1年、3年、5年、10年、自訂區間
    """
    result = await compare_service.compare_cagr(
        symbols=request.symbols,
        periods=request.periods,
        custom_range=request.custom_range,
        benchmark=request.benchmark,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "比較失敗"))
    
    return result


@router.get("/presets", summary="取得預設組合列表")
async def get_presets():
    """取得所有預設比較組合"""
    presets = compare_service.get_presets()
    return {
        "success": True,
        "presets": presets,
    }


@router.get("/presets/{preset_id}", summary="取得預設組合詳情")
async def get_preset_detail(preset_id: str):
    """取得預設組合的詳細內容"""
    preset = compare_service.get_preset_detail(preset_id)
    
    if not preset:
        raise HTTPException(status_code=404, detail="找不到該預設組合")
    
    return {
        "success": True,
        "preset": preset,
    }


@router.get("/benchmarks", summary="取得基準指數選項")
async def get_benchmarks():
    """取得可用的基準指數選項"""
    benchmarks = compare_service.get_benchmark_options()
    return {
        "success": True,
        "benchmarks": [
            {"symbol": k, "name": v}
            for k, v in benchmarks.items()
        ],
    }


# ==================== 用戶儲存的組合 API ====================

@router.get("/saved", summary="取得我的比較組合")
async def get_saved_comparisons(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得當前用戶儲存的所有比較組合"""
    crud = ComparisonCRUD(db)
    comparisons = await crud.get_user_comparisons(user.id)
    
    return {
        "success": True,
        "comparisons": [c.to_dict() for c in comparisons],
    }


@router.post("/saved", summary="儲存比較組合")
async def save_comparison(
    request: SaveComparisonRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """儲存新的比較組合"""
    crud = ComparisonCRUD(db)
    
    # 檢查用戶已有的組合數量（限制最多 10 個）
    existing = await crud.get_user_comparisons(user.id)
    if len(existing) >= 10:
        raise HTTPException(status_code=400, detail="最多只能儲存 10 個比較組合")
    
    # 正規化 symbols
    symbols = [s.upper().strip() for s in request.symbols]
    
    comparison = await crud.create_comparison(
        user_id=user.id,
        name=request.name,
        symbols=symbols,
        benchmark=request.benchmark,
    )
    
    return {
        "success": True,
        "message": "比較組合已儲存",
        "comparison": comparison.to_dict(),
    }


@router.get("/saved/{comparison_id}", summary="取得單一比較組合")
async def get_saved_comparison(
    comparison_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """取得單一比較組合詳情"""
    crud = ComparisonCRUD(db)
    comparison = await crud.get_comparison(comparison_id, user.id)
    
    if not comparison:
        raise HTTPException(status_code=404, detail="找不到該比較組合")
    
    return {
        "success": True,
        "comparison": comparison.to_dict(),
    }


@router.put("/saved/{comparison_id}", summary="更新比較組合")
async def update_saved_comparison(
    comparison_id: int,
    request: UpdateComparisonRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """更新儲存的比較組合"""
    crud = ComparisonCRUD(db)
    
    # 正規化 symbols
    symbols = None
    if request.symbols:
        symbols = [s.upper().strip() for s in request.symbols]
    
    comparison = await crud.update_comparison(
        comparison_id=comparison_id,
        user_id=user.id,
        name=request.name,
        symbols=symbols,
        benchmark=request.benchmark,
    )
    
    if not comparison:
        raise HTTPException(status_code=404, detail="找不到該比較組合")
    
    return {
        "success": True,
        "message": "比較組合已更新",
        "comparison": comparison.to_dict(),
    }


@router.delete("/saved/{comparison_id}", summary="刪除比較組合")
async def delete_saved_comparison(
    comparison_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """刪除儲存的比較組合"""
    crud = ComparisonCRUD(db)
    deleted = await crud.delete_comparison(comparison_id, user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="找不到該比較組合")
    
    return {
        "success": True,
        "message": "比較組合已刪除",
    }


# ==================== 快速比較 (結合 preset + 計算) ====================

@router.get("/quick/{preset_id}", summary="快速比較預設組合")
async def quick_compare_preset(
    preset_id: str,
    benchmark: str = Query(default="^GSPC", description="基準指數"),
    sort_by: str = Query(default="5y", description="排序依據"),
):
    """
    快速比較預設組合
    直接載入預設組合並計算 CAGR
    """
    preset = compare_service.get_preset_detail(preset_id)
    
    if not preset:
        raise HTTPException(status_code=404, detail="找不到該預設組合")
    
    result = await compare_service.compare_cagr(
        symbols=preset["symbols"],
        periods=["1y", "3y", "5y", "10y"],
        benchmark=benchmark,
        sort_by=sort_by,
        sort_order="desc",
    )
    
    result["preset"] = preset
    return result
