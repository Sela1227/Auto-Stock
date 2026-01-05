"""
加密貨幣和市場情緒 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.services.crypto_service import CryptoService
from app.services.chart_service import chart_service
from app.schemas.schemas import CryptoAnalysisResponse, MarketSentimentResponse

router = APIRouter(tags=["加密貨幣"])


@router.get("/api/crypto/{symbol}", summary="查詢加密貨幣", response_model=CryptoAnalysisResponse)
async def get_crypto_analysis(
    symbol: str,
    refresh: bool = Query(False, description="是否強制更新資料"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    查詢單一加密貨幣的技術分析報告
    
    - **symbol**: 加密貨幣代號 (BTC, ETH)
    - **refresh**: 是否強制更新資料
    
    回傳包含：
    - 價格資訊（現價、ATH、距離 ATH%）
    - 漲跌幅（24H、7D、30D、1Y）
    - 市場資訊（市值、排名、24H 成交量）
    - 技術指標（MA7/25/99、RSI、MACD、布林）
    - 交易訊號
    - 綜合評分
    """
    service = CryptoService(db)
    analysis = service.get_crypto_analysis(symbol, force_refresh=refresh)
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"找不到加密貨幣: {symbol}"
        )
    
    return CryptoAnalysisResponse(
        success=True,
        **analysis
    )


@router.get("/api/crypto/{symbol}/chart", summary="取得加密貨幣圖表")
async def get_crypto_chart(
    symbol: str,
    days: int = Query(120, ge=30, le=365, description="顯示天數"),
    show_kd: bool = Query(False, description="顯示 KD 指標"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    生成加密貨幣技術分析圖表
    
    - **symbol**: 加密貨幣代號 (BTC, ETH)
    - **days**: 顯示天數 (30-365)
    - **show_kd**: 是否顯示 KD 指標
    
    回傳 PNG 圖片
    """
    service = CryptoService(db)
    df = service.get_crypto_data(symbol)
    
    if df is None:
        raise HTTPException(
            status_code=404,
            detail=f"找不到加密貨幣: {symbol}"
        )
    
    # 取得名稱
    from app.data_sources.coingecko import coingecko
    info = coingecko.get_coin_info(symbol)
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


@router.get("/api/market/sentiment", summary="取得市場情緒", response_model=MarketSentimentResponse)
async def get_market_sentiment(
    market: str = Query("all", description="市場類型 (stock, crypto, all)"),
):
    """
    取得市場情緒指數
    
    - **market**: 市場類型
      - `stock`: 美股 CNN Fear & Greed Index
      - `crypto`: 加密貨幣 Alternative.me
      - `all`: 兩者都取得
    
    情緒指數範圍 0-100：
    - 0-25: 極度恐懼
    - 26-45: 恐懼
    - 46-55: 中性
    - 56-75: 貪婪
    - 76-100: 極度貪婪
    """
    from app.data_sources.fear_greed import fear_greed
    
    result = {}
    
    if market in ("all", "stock"):
        stock_sentiment = fear_greed.get_stock_fear_greed()
        if stock_sentiment:
            result["stock"] = stock_sentiment
    
    if market in ("all", "crypto"):
        crypto_sentiment = fear_greed.get_crypto_fear_greed()
        if crypto_sentiment:
            result["crypto"] = crypto_sentiment
    
    return MarketSentimentResponse(
        success=True,
        stock=result.get("stock"),
        crypto=result.get("crypto"),
    )
