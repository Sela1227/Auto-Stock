"""
股票查詢 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.schemas.schemas import StockAnalysisResponse

router = APIRouter(prefix="/api/stock", tags=["股票"])


@router.get("/{symbol}", summary="查詢股票")
async def get_stock_analysis(
    symbol: str,
    refresh: bool = Query(False, description="是否強制更新資料"),
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
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.indicator_service import indicator_service
    
    symbol = symbol.upper()
    
    # 取得股票資料
    df = yahoo_finance.get_stock_data(symbol, period="1y")
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"找不到股票: {symbol}"
        )
    
    # 取得股票資訊
    info = yahoo_finance.get_stock_info(symbol)
    
    # 計算技術指標
    df = indicator_service.calculate_all_indicators(df)
    
    # 取得最新資料
    latest = df.iloc[-1]
    current_price = float(latest['close'])
    
    # 價格資訊
    high_52w = float(df['high'].tail(252).max()) if len(df) >= 252 else float(df['high'].max())
    low_52w = float(df['low'].tail(252).min()) if len(df) >= 252 else float(df['low'].min())
    
    # 漲跌幅計算
    def calc_change(days):
        if len(df) > days:
            old_price = float(df.iloc[-days-1]['close'])
            return round((current_price - old_price) / old_price * 100, 2)
        return None
    
    # 均線資訊
    ma20 = float(latest.get('MA20', 0)) if 'MA20' in latest else None
    ma50 = float(latest.get('MA50', 0)) if 'MA50' in latest else None
    ma200 = float(latest.get('MA200', 0)) if 'MA200' in latest else None
    
    # 判斷均線排列
    alignment = "neutral"
    if ma20 and ma50 and ma200:
        if current_price > ma20 > ma50 > ma200:
            alignment = "bullish"
        elif current_price < ma20 < ma50 < ma200:
            alignment = "bearish"
    
    # RSI
    rsi_value = float(latest.get('RSI', 50)) if 'RSI' in latest else 50
    rsi_status = "overbought" if rsi_value > 70 else "oversold" if rsi_value < 30 else "neutral"
    
    # MACD
    macd_dif = float(latest.get('MACD_DIF', 0)) if 'MACD_DIF' in latest else 0
    macd_dea = float(latest.get('MACD_DEA', 0)) if 'MACD_DEA' in latest else 0
    macd_hist = float(latest.get('MACD_HIST', 0)) if 'MACD_HIST' in latest else 0
    macd_status = "bullish" if macd_dif > macd_dea else "bearish"
    
    # 成交量
    volume_today = int(latest['volume']) if 'volume' in latest else 0
    volume_avg = int(df['volume'].tail(20).mean()) if 'volume' in df.columns else 0
    volume_ratio = round(volume_today / volume_avg, 2) if volume_avg > 0 else 1.0
    
    # 綜合評分
    buy_score = 0
    sell_score = 0
    
    if alignment == "bullish":
        buy_score += 1
    elif alignment == "bearish":
        sell_score += 1
    
    if rsi_value < 30:
        buy_score += 1
    elif rsi_value > 70:
        sell_score += 1
    
    if macd_status == "bullish":
        buy_score += 1
    else:
        sell_score += 1
    
    rating = "bullish" if buy_score > sell_score else "bearish" if sell_score > buy_score else "neutral"
    
    return {
        "success": True,
        "symbol": symbol,
        "name": info.get("name", "") if info else "",
        "asset_type": "stock",
        "price": {
            "current": current_price,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "from_high_pct": round((current_price - high_52w) / high_52w * 100, 2),
            "from_low_pct": round((current_price - low_52w) / low_52w * 100, 2),
        },
        "change": {
            "day": calc_change(1),
            "week": calc_change(5),
            "month": calc_change(20),
            "quarter": calc_change(60),
            "year": calc_change(250),
        },
        "volume": {
            "today": volume_today,
            "avg_20d": volume_avg,
            "ratio": volume_ratio,
        },
        "indicators": {
            "ma": {
                "ma20": ma20,
                "ma50": ma50,
                "ma200": ma200,
                "alignment": alignment,
                "price_vs_ma20": "above" if current_price > ma20 else "below" if ma20 else None,
                "price_vs_ma50": "above" if current_price > ma50 else "below" if ma50 else None,
                "price_vs_ma200": "above" if current_price > ma200 else "below" if ma200 else None,
            },
            "rsi": {
                "value": rsi_value,
                "period": 14,
                "status": rsi_status,
            },
            "macd": {
                "dif": macd_dif,
                "macd": macd_dea,
                "histogram": macd_hist,
                "status": macd_status,
            },
        },
        "score": {
            "buy": buy_score,
            "sell": sell_score,
            "rating": rating,
        },
    }


@router.get("/{symbol}/chart", summary="取得股票圖表")
async def get_stock_chart(
    symbol: str,
    days: int = Query(120, ge=30, le=365, description="顯示天數"),
):
    """
    生成股票技術分析圖表
    
    - **symbol**: 股票代號
    - **days**: 顯示天數 (30-365)
    
    回傳 PNG 圖片
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.chart_service import chart_service
    
    symbol = symbol.upper()
    
    df = yahoo_finance.get_stock_data(symbol, period="1y")
    
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"找不到股票: {symbol}"
        )
    
    # 取得股票名稱
    info = yahoo_finance.get_stock_info(symbol)
    name = info.get("name", "") if info else ""
    
    # 生成圖表
    chart_path = chart_service.plot_stock_analysis(
        df,
        symbol=symbol,
        name=name,
        days=days,
        show_kd=False,
    )
    
    return FileResponse(
        chart_path,
        media_type="image/png",
        filename=f"{symbol}_chart.png",
    )
