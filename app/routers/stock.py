"""
股票查詢 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.services.stock_service import StockService
from app.services.chart_service import chart_service
from app.schemas.schemas import StockAnalysisResponse

router = APIRouter(prefix="/api/stock", tags=["股票"])


@router.get("/{symbol}", summary="查詢股票", response_model=StockAnalysisResponse)
async def get_stock_analysis(
    symbol: str,
    refresh: bool = Query(False, description="是否強制更新資料"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    查詢單一股票的技術分析報告
    
    - **symbol**: 股票代號 (如 AAPL, TSLA, NVDA)
    - **refresh**: 是否強制更新資料
    
    回傳包含：
    - 價格資訊（現價、52週高低、距離高低點%）
    - 漲跌幅（日、週、月、季、年）
    - 成交量資訊
    - 技術指標（MA、RSI、MACD、KD、布林、OBV）
    - 交易訊號
    - 綜合評分
    """
    service = StockService(db)
    analysis = service.get_stock_analysis(symbol, force_refresh=refresh)
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"找不到股票: {symbol}"
        )
    
    return StockAnalysisResponse(
        success=True,
        **analysis
    )


@router.get("/{symbol}/chart", summary="取得股票圖表")
async def get_stock_chart(
    symbol: str,
    days: int = Query(120, ge=30, le=365, description="顯示天數"),
    show_kd: bool = Query(False, description="顯示 KD 指標"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    生成股票技術分析圖表
    
    - **symbol**: 股票代號
    - **days**: 顯示天數 (30-365)
    - **show_kd**: 是否顯示 KD 指標
    
    回傳 PNG 圖片
    """
    service = StockService(db)
    df = service.get_stock_data(symbol)
    
    if df is None:
        raise HTTPException(
            status_code=404,
            detail=f"找不到股票: {symbol}"
        )
    
    # 取得股票名稱
    from app.data_sources.yahoo_finance import yahoo_finance
    info = yahoo_finance.get_stock_info(symbol)
    name = info.get("name", "") if info else ""
    
    # 生成圖表
    chart_path = chart_service.plot_stock_analysis(
        df,
        symbol=symbol.upper(),
        name=name,
        days=days,
        show_kd=show_kd,
    )
    
    return FileResponse(
        chart_path,
        media_type="image/png",
        filename=f"{symbol}_chart.png",
    )
