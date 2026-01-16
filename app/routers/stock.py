"""
股票查詢 API 路由

🚀 效能優化版 - 2026-01-16
- 歷史資料存入 PostgreSQL
- 修正路由順序（具體路由在前）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stock", tags=["股票"])


def normalize_tw_symbol(symbol: str) -> str:
    """標準化台股代號"""
    symbol = symbol.strip().upper()
    
    if '.' in symbol or symbol.startswith('^'):
        return symbol
    
    if symbol.isdigit() and 4 <= len(symbol) <= 6:
        return f"{symbol}.TW"
    
    if len(symbol) >= 5 and symbol[:-1].isdigit() and symbol[-1] in ('L', 'R', 'U'):
        return f"{symbol}.TW"
    
    return symbol


def _get_stock_df(symbol: str, years: int = 10, force_refresh: bool = False):
    """
    取得股票 DataFrame（帶快取）
    
    Returns:
        (df, symbol, data_source)
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.stock_history_service import StockHistoryService
    from app.database import SyncSessionLocal
    
    df = None
    data_source = "yahoo"
    
    try:
        db = SyncSessionLocal()
        try:
            history_service = StockHistoryService(db)
            df, data_source = history_service.get_stock_history(symbol, years=years, force_refresh=force_refresh)
            
            if (df is None or df.empty) and symbol.endswith('.TW'):
                two_symbol = symbol.replace('.TW', '.TWO')
                df, data_source = history_service.get_stock_history(two_symbol, years=years, force_refresh=force_refresh)
                if df is not None and not df.empty:
                    symbol = two_symbol
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"快取服務異常: {e}")
        df = yahoo_finance.get_stock_history(symbol, period=f"{years}y")
        if (df is None or df.empty) and symbol.endswith('.TW'):
            two_symbol = symbol.replace('.TW', '.TWO')
            df = yahoo_finance.get_stock_history(two_symbol, period=f"{years}y")
            if df is not None and not df.empty:
                symbol = two_symbol
        data_source = "yahoo"
    
    return df, symbol, data_source


# ============================================================
# 🔴 重要：靜態路由必須放在動態路由之前！
# ============================================================

@router.get("/cache/stats", summary="快取統計")
async def get_cache_stats(symbol: str = Query(None)):
    """取得歷史資料快取統計"""
    from app.services.stock_history_service import StockHistoryService
    from app.database import SyncSessionLocal
    
    try:
        db = SyncSessionLocal()
        try:
            stats = StockHistoryService(db).get_cache_stats(symbol)
        finally:
            db.close()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/history", summary="走勢比較")
async def compare_stocks(
    symbols: str = Query(..., description="股票代號，逗號分隔，最多 5 個"),
    days: int = Query(90, ge=7, le=365, description="比較天數"),
):
    """取得多支股票的正規化走勢資料"""
    from app.data_sources.yahoo_finance import yahoo_finance
    import math
    
    symbol_list = [normalize_tw_symbol(s.strip()) for s in symbols.split(",") if s.strip()]
    
    if len(symbol_list) < 1:
        raise HTTPException(status_code=400, detail="請至少輸入一個代號")
    if len(symbol_list) > 5:
        raise HTTPException(status_code=400, detail="最多比較 5 個標的")
    
    result = {}
    
    for symbol in symbol_list:
        try:
            if symbol.startswith("^"):
                df = yahoo_finance.get_index_data(symbol, period="2y")
            else:
                df, symbol, _ = _get_stock_df(symbol, years=2)
            
            if df is None or df.empty:
                continue
            
            df.columns = [c.lower() for c in df.columns]
            if 'date' not in df.columns:
                df['date'] = df.index
            
            df = df.tail(days).copy()
            if len(df) < 5:
                continue
            
            price_col = "adj_close" if "adj_close" in df.columns else "close"
            start_price = df.iloc[0][price_col]
            if start_price == 0 or pd.isna(start_price):
                continue
            
            df["normalized"] = (df[price_col] / start_price) * 100
            df = df.dropna(subset=["normalized"])
            
            if symbol.startswith("^"):
                from app.models.index_price import INDEX_SYMBOLS
                info = INDEX_SYMBOLS.get(symbol, {})
                name = info.get("name_zh", symbol)
            else:
                info = yahoo_finance.get_stock_info(symbol)
                name = info.get("name", symbol) if info else symbol
            
            history = []
            for _, row in df.iterrows():
                val = row["normalized"]
                if not (math.isnan(val) or math.isinf(val)):
                    history.append({"date": str(row["date"]), "value": round(val, 2)})
            
            if history:
                result[symbol] = {"name": name, "history": history}
                
        except Exception as e:
            logger.error(f"處理 {symbol} 錯誤: {e}")
    
    if not result:
        raise HTTPException(status_code=404, detail="找不到任何有效資料")
    
    return {"success": True, "days": days, "data": result}


# ============================================================
# 🔴 帶路徑參數的子路由（必須在 /{symbol} 之前）
# ============================================================

@router.get("/{symbol}/returns", summary="年化報酬率")
async def get_stock_returns(symbol: str):
    """
    計算股票的年化報酬率 (CAGR)
    
    Returns:
        - returns: 累積報酬率 (1m, 3m, 6m, 1y)
        - cagr: 年化報酬率 (cagr_1y, cagr_3y, cagr_5y, cagr_10y)
    """
    symbol = normalize_tw_symbol(symbol)
    logger.info(f"計算年化報酬率: {symbol}")
    
    df, symbol, _ = _get_stock_df(symbol, years=10, force_refresh=False)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"找不到股票: {symbol}")
    
    try:
        df.columns = [c.lower() for c in df.columns]
        
        # 使用調整後價格計算報酬
        price_col = 'adj_close' if 'adj_close' in df.columns else 'close'
        
        current_price = float(df.iloc[-1][price_col])
        
        # 累積報酬率
        def calc_return(days):
            if len(df) > days:
                old_price = float(df.iloc[-days-1][price_col])
                if old_price > 0:
                    return round((current_price - old_price) / old_price * 100, 2)
            return None
        
        returns = {
            "1m": calc_return(22),
            "3m": calc_return(65),
            "6m": calc_return(130),
            "1y": calc_return(252),
        }
        
        # CAGR 計算
        def calc_cagr(years):
            days = years * 252
            if len(df) > days:
                start_price = float(df.iloc[-days-1][price_col])
                if start_price > 0:
                    cagr = ((current_price / start_price) ** (1 / years) - 1) * 100
                    return round(cagr, 2)
            return None
        
        cagr = {
            "cagr_1y": calc_cagr(1),
            "cagr_3y": calc_cagr(3),
            "cagr_5y": calc_cagr(5),
            "cagr_10y": calc_cagr(10),
        }
        
        return {
            "success": True,
            "symbol": symbol,
            "returns": returns,
            "cagr": cagr,
            "note": "CAGR 已包含分割調整及配息再投入效果",
        }
        
    except Exception as e:
        logger.error(f"計算 {symbol} 年化報酬率失敗: {e}")
        raise HTTPException(status_code=500, detail=f"計算失敗: {str(e)}")


@router.get("/{symbol}/chart", summary="取得股票圖表")
async def get_stock_chart(
    symbol: str,
    days: int = Query(120, ge=30, le=365, description="顯示天數"),
):
    """生成股票技術分析圖表"""
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.indicator_service import indicator_service
    from app.services.chart_service import chart_service
    
    symbol = normalize_tw_symbol(symbol)
    logger.info(f"生成圖表: {symbol}, days={days}")
    
    df, symbol, _ = _get_stock_df(symbol, years=2, force_refresh=False)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"找不到股票: {symbol}")
    
    df.columns = [c.lower() for c in df.columns]
    
    if 'adj_close' in df.columns:
        df['close'] = df['adj_close']
    
    if 'date' not in df.columns:
        df['date'] = df.index
    
    # 計算技術指標
    df = indicator_service.calculate_all_indicators(df)
    
    info = yahoo_finance.get_stock_info(symbol)
    name = info.get("name", "") if info else ""
    
    chart_path = chart_service.plot_stock_analysis(
        df,
        symbol=symbol,
        name=name,
        days=days,
        show_kd=False,
    )
    
    logger.info(f"圖表生成完成: {chart_path}")
    
    return FileResponse(chart_path, media_type="image/png", filename=f"{symbol}_chart.png")


@router.delete("/cache/{symbol}", summary="清除快取")
async def clear_cache(symbol: str):
    """清除指定股票的快取"""
    from app.services.stock_history_service import StockHistoryService
    from app.database import SyncSessionLocal
    
    try:
        db = SyncSessionLocal()
        try:
            count = StockHistoryService(db).clear_cache(symbol)
        finally:
            db.close()
        return {"success": True, "deleted_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 🔴 最通用的路由放最後
# ============================================================

@router.get("/{symbol}", summary="查詢股票")
async def get_stock_analysis(
    symbol: str,
    refresh: bool = Query(False, description="是否強制更新資料"),
):
    """查詢單一股票的技術分析報告"""
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.indicator_service import indicator_service
    from app.services.price_cache_service import PriceCacheService
    from app.database import SyncSessionLocal
    
    symbol = normalize_tw_symbol(symbol)
    original_symbol = symbol
    logger.info(f"開始查詢股票: {symbol}, refresh={refresh}")
    
    df, symbol, data_source = _get_stock_df(symbol, years=10, force_refresh=refresh)
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"找不到股票: {original_symbol}")
    
    logger.info(f"取得 {len(df)} 筆資料，來源: {data_source}")
    
    try:
        df.columns = [c.lower() for c in df.columns]
        df['close_raw'] = df['close'].copy()
        
        if 'adj_close' in df.columns:
            df['close'] = df['adj_close']
        
        if 'date' not in df.columns:
            df['date'] = df.index
        
        df = indicator_service.calculate_all_indicators(df)
        
        latest = df.iloc[-1]
        current_price = float(latest.get('close_raw', latest['close']))
        
        info = yahoo_finance.get_stock_info(symbol)
        
        close_col = 'close_raw' if 'close_raw' in df.columns else 'close'
        high_52w = float(df[close_col].tail(252).max()) if len(df) >= 252 else float(df[close_col].max())
        low_52w = float(df[close_col].tail(252).min()) if len(df) >= 252 else float(df[close_col].min())
        
        current_price_adj = float(latest['close'])
        def calc_change(days):
            if len(df) > days:
                old = float(df.iloc[-days-1]['close'])
                return round((current_price_adj - old) / old * 100, 2)
            return None
        
        ma20 = float(latest['ma20']) if 'ma20' in latest and pd.notna(latest.get('ma20')) else None
        ma50 = float(latest['ma50']) if 'ma50' in latest and pd.notna(latest.get('ma50')) else None
        ma200 = float(latest['ma200']) if 'ma200' in latest and pd.notna(latest.get('ma200')) else None
        
        alignment = "neutral"
        if ma20 and ma50 and ma200:
            if current_price_adj > ma20 > ma50 > ma200:
                alignment = "bullish"
            elif current_price_adj < ma20 < ma50 < ma200:
                alignment = "bearish"
        
        rsi_value = float(latest['rsi']) if 'rsi' in latest and pd.notna(latest.get('rsi')) else 50
        rsi_status = "overbought" if rsi_value > 70 else "oversold" if rsi_value < 30 else "neutral"
        
        macd_dif = float(latest['macd_dif']) if 'macd_dif' in latest and pd.notna(latest.get('macd_dif')) else 0
        macd_dea = float(latest['macd_dea']) if 'macd_dea' in latest and pd.notna(latest.get('macd_dea')) else 0
        macd_hist = float(latest['macd_hist']) if 'macd_hist' in latest and pd.notna(latest.get('macd_hist')) else 0
        macd_status = "bullish" if macd_dif > macd_dea else "bearish"
        
        volume_today = int(latest['volume']) if pd.notna(latest.get('volume')) else 0
        volume_avg = int(df['volume'].tail(20).mean()) if 'volume' in df.columns else 0
        volume_ratio = round(volume_today / volume_avg, 2) if volume_avg > 0 else 1.0
        
        buy_score = 0
        sell_score = 0
        if alignment == "bullish": buy_score += 1
        elif alignment == "bearish": sell_score += 1
        if rsi_value < 30: buy_score += 1
        elif rsi_value > 70: sell_score += 1
        if macd_status == "bullish": buy_score += 1
        else: sell_score += 1
        rating = "bullish" if buy_score > sell_score else "bearish" if sell_score > buy_score else "neutral"
        
        stock_name = info.get("name", "") if info else ""
        if not stock_name:
            from app.data_sources.yahoo_finance import TAIWAN_STOCK_NAMES
            stock_code = symbol.replace(".TW", "").replace(".TWO", "")
            stock_name = TAIWAN_STOCK_NAMES.get(stock_code, symbol)
        
        # 更新價格快取
        try:
            db = SyncSessionLocal()
            try:
                day_change = calc_change(1)
                prev_close = float(df.iloc[-2][close_col]) if len(df) > 1 else None
                change_amount = current_price - prev_close if prev_close else None
                
                cache_service = PriceCacheService(db)
                cache_service._upsert_cache(
                    symbol=symbol, name=stock_name, price=current_price,
                    prev_close=prev_close, change=change_amount, change_pct=day_change,
                    volume=volume_today, asset_type="stock", ma20=ma20,
                )
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"價格快取更新失敗: {e}")
        
        # 圖表資料
        df_chart = df.tail(1500)
        
        return {
            "success": True,
            "symbol": symbol,
            "name": stock_name,
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
            "volume": {"today": volume_today, "avg_20d": volume_avg, "ratio": volume_ratio},
            "indicators": {
                "ma": {
                    "ma20": ma20, "ma50": ma50, "ma200": ma200,
                    "alignment": alignment,
                    "price_vs_ma20": "above" if ma20 and current_price > ma20 else "below" if ma20 else None,
                    "price_vs_ma50": "above" if ma50 and current_price > ma50 else "below" if ma50 else None,
                    "price_vs_ma200": "above" if ma200 and current_price > ma200 else "below" if ma200 else None,
                },
                "rsi": {"value": rsi_value, "period": 14, "status": rsi_status},
                "macd": {"dif": macd_dif, "macd": macd_dea, "histogram": macd_hist, "status": macd_status},
            },
            "score": {"buy": buy_score, "sell": sell_score, "rating": rating},
            "chart_data": {
                "dates": [str(d) for d in df_chart['date'].tolist()],
                "prices": [float(p) if pd.notna(p) else None for p in df_chart['close'].tolist()],
                "ma20": [float(v) if pd.notna(v) else None for v in df_chart['ma20'].tolist()] if 'ma20' in df_chart.columns else [],
                "ma50": [float(v) if pd.notna(v) else None for v in df_chart['ma50'].tolist()] if 'ma50' in df_chart.columns else [],
                "ma200": [float(v) if pd.notna(v) else None for v in df_chart['ma200'].tolist()] if 'ma200' in df_chart.columns else [],
                "ma250": [float(v) if pd.notna(v) else None for v in df_chart['ma250'].tolist()] if 'ma250' in df_chart.columns else [],
                "volume": [int(v) if pd.notna(v) else 0 for v in df_chart['volume'].tolist()] if 'volume' in df_chart.columns else [],
            },
            "from_cache": data_source in ('cache', 'partial'),
            "data_source": data_source,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"處理 {symbol} 時發生錯誤: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")
