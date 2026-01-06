"""
股票查詢 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import logging
import pandas as pd

from app.schemas.schemas import StockAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stock", tags=["股票"])


@router.get("/{symbol}", summary="查詢股票")
async def get_stock_analysis(
    symbol: str,
    refresh: bool = Query(False, description="是否強制更新資料"),
):
    """
    查詢單一股票的技術分析報告
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.indicator_service import indicator_service
    
    symbol = symbol.upper()
    original_symbol = symbol
    logger.info(f"開始查詢股票: {symbol}")
    
    try:
        # 取得股票資料 (抓取 2 年以計算 MA250)
        logger.info(f"正在從 Yahoo Finance 取得 {symbol} 資料...")
        df = yahoo_finance.get_stock_history(symbol, period="2y")
        
        # 如果 .TW 找不到，嘗試 .TWO (上櫃股票)
        if (df is None or df.empty) and symbol.endswith('.TW'):
            two_symbol = symbol.replace('.TW', '.TWO')
            logger.info(f"{symbol} 找不到，嘗試上櫃股票: {two_symbol}")
            df = yahoo_finance.get_stock_history(two_symbol, period="2y")
            if df is not None and not df.empty:
                symbol = two_symbol
                logger.info(f"成功找到上櫃股票: {two_symbol}")
        
        if df is None or df.empty:
            logger.warning(f"找不到股票資料: {original_symbol}")
            raise HTTPException(
                status_code=404,
                detail=f"找不到股票: {original_symbol}（已嘗試上市 .TW 和上櫃 .TWO）"
            )
        
        logger.info(f"取得 {len(df)} 筆資料，正在計算技術指標...")
        
        # 取得股票資訊
        info = yahoo_finance.get_stock_info(symbol)
        
        # 計算技術指標
        df = indicator_service.calculate_all_indicators(df)
        
        # 取得最新資料
        latest = df.iloc[-1]
        current_price = float(latest['close'])
        
        logger.info(f"{symbol} 現價: {current_price}")
        
        # 價格資訊
        high_52w = float(df['high'].tail(252).max()) if len(df) >= 252 else float(df['high'].max())
        low_52w = float(df['low'].tail(252).min()) if len(df) >= 252 else float(df['low'].min())
        
        # 漲跌幅計算
        def calc_change(days):
            if len(df) > days:
                old_price = float(df.iloc[-days-1]['close'])
                return round((current_price - old_price) / old_price * 100, 2)
            return None
        
        # 均線資訊 (indicator_service 用小寫: ma20, ma50, ma200)
        ma20 = float(latest.get('ma20', 0)) if 'ma20' in latest else None
        ma50 = float(latest.get('ma50', 0)) if 'ma50' in latest else None
        ma200 = float(latest.get('ma200', 0)) if 'ma200' in latest else None
        
        # 判斷均線排列
        alignment = "neutral"
        if ma20 and ma50 and ma200:
            if current_price > ma20 > ma50 > ma200:
                alignment = "bullish"
            elif current_price < ma20 < ma50 < ma200:
                alignment = "bearish"
        
        # RSI (小寫: rsi)
        rsi_value = float(latest.get('rsi', 50)) if 'rsi' in latest else 50
        rsi_status = "overbought" if rsi_value > 70 else "oversold" if rsi_value < 30 else "neutral"
        
        # MACD (小寫: macd_dif, macd_dea, macd_hist)
        macd_dif = float(latest.get('macd_dif', 0)) if 'macd_dif' in latest else 0
        macd_dea = float(latest.get('macd_dea', 0)) if 'macd_dea' in latest else 0
        macd_hist = float(latest.get('macd_hist', 0)) if 'macd_hist' in latest else 0
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
        
        logger.info(f"{symbol} 查詢完成，評分: {rating}")
        
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
                    "price_vs_ma20": "above" if ma20 and current_price > ma20 else "below" if ma20 else None,
                    "price_vs_ma50": "above" if ma50 and current_price > ma50 else "below" if ma50 else None,
                    "price_vs_ma200": "above" if ma200 and current_price > ma200 else "below" if ma200 else None,
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
            # 添加圖表數據 (最近 365 天，支援 1 年範圍)
            "chart_data": {
                "dates": [str(d) for d in df['date'].tail(365).tolist()],
                "prices": [float(p) for p in df['close'].tail(365).tolist()],
                "ma20": [float(v) if not pd.isna(v) else None for v in df['ma20'].tail(365).tolist()] if 'ma20' in df.columns else [],
                "ma50": [float(v) if not pd.isna(v) else None for v in df['ma50'].tail(365).tolist()] if 'ma50' in df.columns else [],
                "ma200": [float(v) if not pd.isna(v) else None for v in df['ma200'].tail(365).tolist()] if 'ma200' in df.columns else [],
                "ma250": [float(v) if not pd.isna(v) else None for v in df['ma250'].tail(365).tolist()] if 'ma250' in df.columns else [],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查詢 {symbol} 時發生錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查詢失敗: {str(e)}"
        )


@router.get("/{symbol}/chart", summary="取得股票圖表")
async def get_stock_chart(
    symbol: str,
    days: int = Query(120, ge=30, le=365, description="顯示天數"),
):
    """
    生成股票技術分析圖表
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.chart_service import chart_service
    
    symbol = symbol.upper()
    
    df = yahoo_finance.get_stock_history(symbol, period="1y")
    
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
