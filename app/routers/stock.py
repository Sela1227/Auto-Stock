"""
股票查詢 API 路由

修復: 台股代號自動轉換 (0050 → 0050.TW)
新增: 查詢結果自動快取（含 MA20）

🔧 修復版本 - 2026-01-16
- 移除 Git merge conflict 標記
- 禁用快取返回簡化資料（確保圖表和完整指標顯示）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import logging
import pandas as pd
from datetime import datetime

from app.schemas.schemas import StockAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stock", tags=["股票"])


def normalize_tw_symbol(symbol: str) -> str:
    """
    標準化台股代號
    - 純數字 4-6 位 → 自動加 .TW
    - ETF 槓桿/反向 (如 00631L, 00632R) → 自動加 .TW
    - 已有後綴 → 保持不變
    """
    symbol = symbol.strip().upper()
    
    # 如果已經有後綴，不處理
    if '.' in symbol or symbol.startswith('^'):
        return symbol
    
    # 台股代號：4-6 位純數字
    if symbol.isdigit() and 4 <= len(symbol) <= 6:
        return f"{symbol}.TW"
    
    # 台股 ETF 槓桿/反向：數字開頭 + L/R/U 結尾 (如 00631L, 00632R, 00635U)
    if len(symbol) >= 5 and symbol[:-1].isdigit() and symbol[-1] in ('L', 'R', 'U'):
        return f"{symbol}.TW"
    
    return symbol


@router.get("/{symbol}", summary="查詢股票")
async def get_stock_analysis(
    symbol: str,
    refresh: bool = Query(False, description="是否強制更新資料"),
):
    """
    查詢單一股票的技術分析報告
    
    注意：此 API 總是返回完整資料（含圖表和所有指標）
    查詢完成後會自動更新價格快取（供追蹤清單使用）
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.indicator_service import indicator_service
    from app.services.price_cache_service import PriceCacheService
    from app.database import get_sync_db
    
    # 台股代號自動轉換
    symbol = normalize_tw_symbol(symbol)
    original_symbol = symbol
    logger.info(f"開始查詢股票: {symbol}, refresh={refresh}")
    
    # ========== 🔧 修復：禁用快取返回簡化資料 ==========
    # 註：為確保圖表和完整指標顯示，不使用快取簡化返回
    # 快取仍會在查詢完成後更新，供追蹤清單使用
    # 
    # 原始快取邏輯已被禁用：
    # if not refresh:
    #     try:
    #         sync_db = next(get_sync_db())
    #         cache_service = PriceCacheService(sync_db)
    #         cached = cache_service.get_cached_price(symbol, max_age_minutes=5)
    #         if cached and cached.get("price"):
    #             return {...簡化資料...}  # 沒有 chart_data
    #     except Exception as e:
    #         pass
    # ==========
    
    # ========== 從 Yahoo Finance 查詢 ==========
    try:
        # 取得股票資料 (抓取 10 年以計算長期 CAGR)
        logger.info(f"正在從 Yahoo Finance 取得 {symbol} 資料...")
        df = yahoo_finance.get_stock_history(symbol, period="10y")
        
        # 如果 .TW 找不到，嘗試 .TWO (上櫃股票)
        if (df is None or df.empty) and symbol.endswith('.TW'):
            two_symbol = symbol.replace('.TW', '.TWO')
            logger.info(f"{symbol} 找不到，嘗試上櫃股票: {two_symbol}")
            df = yahoo_finance.get_stock_history(two_symbol, period="10y")
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
        
        # 保存原始收盤價（用於顯示）
        df['close_raw'] = df['close'].copy()
        
        # 使用調整後價格計算技術指標（處理分割和配息）
        # 這樣 MA 線和圖表才不會有斷崖
        if 'adj_close' in df.columns:
            df['close'] = df['adj_close']
            logger.info(f"{symbol} 使用調整後價格計算指標")
        
        # 計算技術指標（基於調整後價格）
        df = indicator_service.calculate_all_indicators(df)
        
        # 取得最新資料
        latest = df.iloc[-1]
        # 顯示用原始價格（用戶習慣看的價格）
        current_price = float(latest['close_raw'])
        
        logger.info(f"{symbol} 現價: {current_price}")
        
        # 價格資訊（用原始價格顯示 52 週高低）
        high_52w = float(df['close_raw'].tail(252).max()) if len(df) >= 252 else float(df['close_raw'].max())
        low_52w = float(df['close_raw'].tail(252).min()) if len(df) >= 252 else float(df['close_raw'].min())
        
        # 漲跌幅計算（用調整後價格計算，反映真實報酬）
        current_price_adj = float(latest['close'])  # 調整後現價
        def calc_change(days):
            if len(df) > days:
                old_price_adj = float(df.iloc[-days-1]['close'])  # 調整後歷史價格
                return round((current_price_adj - old_price_adj) / old_price_adj * 100, 2)
            return None
        
        # 均線資訊 (indicator_service 用小寫: ma20, ma50, ma200)
        ma20 = float(latest.get('ma20', 0)) if 'ma20' in latest else None
        ma50 = float(latest.get('ma50', 0)) if 'ma50' in latest else None
        ma200 = float(latest.get('ma200', 0)) if 'ma200' in latest else None
        
        # 判斷均線排列（用調整後價格比較）
        alignment = "neutral"
        if ma20 and ma50 and ma200:
            if current_price_adj > ma20 > ma50 > ma200:
                alignment = "bullish"
            elif current_price_adj < ma20 < ma50 < ma200:
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
        
        # 確保 name 正確粹取
        stock_name = ""
        if info:
            stock_name = info.get("name", "")
        if not stock_name:
            # 再次嘗試從本地映射表粹取
            from app.data_sources.yahoo_finance import TAIWAN_STOCK_NAMES
            stock_code = symbol.replace(".TW", "").replace(".TWO", "")
            stock_name = TAIWAN_STOCK_NAMES.get(stock_code, symbol)
        
        # 🆕 將查詢結果寫入快取（含 MA20）
        day_change = calc_change(1)
        prev_close = float(df.iloc[-2]['close_raw']) if len(df) > 1 else None
        change_amount = current_price - prev_close if prev_close else None
        
        try:
            from app.services.price_cache_service import PriceCacheService
            from app.database import SyncSessionLocal
            
            db = SyncSessionLocal()
            try:
                cache_service = PriceCacheService(db)
                cache_service._upsert_cache(
                    symbol=symbol,
                    name=stock_name,
                    price=current_price,
                    prev_close=prev_close,
                    change=change_amount,
                    change_pct=day_change,
                    volume=volume_today,
                    asset_type="stock",
                    ma20=ma20,
                )
                db.commit()
                logger.info(f"💾 已快取: {symbol}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"快取寫入失敗: {e}")
        
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
            # 添加圖表數據 (最近 1500 天，支援 5 年範圍)
            "chart_data": {
                "dates": [str(d) for d in df['date'].tail(1500).tolist()],
                "prices": [float(p) for p in df['close'].tail(1500).tolist()],
                "ma20": [float(v) if not pd.isna(v) else None for v in df['ma20'].tail(1500).tolist()] if 'ma20' in df.columns else [],
                "ma50": [float(v) if not pd.isna(v) else None for v in df['ma50'].tail(1500).tolist()] if 'ma50' in df.columns else [],
                "ma200": [float(v) if not pd.isna(v) else None for v in df['ma200'].tail(1500).tolist()] if 'ma200' in df.columns else [],
                "ma250": [float(v) if not pd.isna(v) else None for v in df['ma250'].tail(1500).tolist()] if 'ma250' in df.columns else [],
                "volume": [int(v) if not pd.isna(v) else 0 for v in df['volume'].tail(1500).tolist()] if 'volume' in df.columns else [],
            },
            "from_cache": False,  # 🆕 標記：這是從 Yahoo Finance 取得的新鮮資料
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
    
    # 台股代號自動轉換
    symbol = normalize_tw_symbol(symbol)
    
    df = yahoo_finance.get_stock_history(symbol, period="1y")
    
    # 如果 .TW 找不到，嘗試 .TWO
    if (df is None or df.empty) and symbol.endswith('.TW'):
        two_symbol = symbol.replace('.TW', '.TWO')
        df = yahoo_finance.get_stock_history(two_symbol, period="1y")
        if df is not None and not df.empty:
            symbol = two_symbol
    
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


@router.get("/compare/history", summary="走勢比較")
async def compare_stocks(
    symbols: str = Query(..., description="股票代號，逗號分隔，最多 5 個"),
    days: int = Query(90, ge=7, le=365, description="比較天數"),
):
    """
    取得多支股票的正規化走勢資料（用於比較圖表）
    
    - 價格會正規化為起始日 = 100%
    - 回傳各股票的日期、正規化價格
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    import math
    
    # 解析 symbols，並自動轉換台股代號
    symbol_list = [normalize_tw_symbol(s.strip()) for s in symbols.split(",") if s.strip()]
    
    if len(symbol_list) < 1:
        raise HTTPException(status_code=400, detail="請至少輸入一個代號")
    
    if len(symbol_list) > 5:
        raise HTTPException(status_code=400, detail="最多比較 5 個標的")
    
    logger.info(f"走勢比較: {symbol_list}, {days} 天")
    
    result = {}
    common_dates = None
    
    for symbol in symbol_list:
        try:
            # 判斷是指數還是股票
            if symbol.startswith("^"):
                df = yahoo_finance.get_index_data(symbol, period="2y")
            else:
                df = yahoo_finance.get_stock_history(symbol, period="2y")
                
                # 如果 .TW 找不到，嘗試 .TWO
                if (df is None or df.empty) and symbol.endswith('.TW'):
                    two_symbol = symbol.replace('.TW', '.TWO')
                    df = yahoo_finance.get_stock_history(two_symbol, period="2y")
                    if df is not None and not df.empty:
                        symbol = two_symbol
            
            if df is None or df.empty:
                logger.warning(f"找不到資料: {symbol}")
                continue
            
            # 取最近 N 天
            df = df.tail(days).copy()
            
            if len(df) < 5:
                logger.warning(f"{symbol} 資料不足")
                continue
            
            # 正規化：起始價格 = 100（使用調整後價格以處理分割）
            # 如果沒有 adj_close，用 close
            price_col = "adj_close" if "adj_close" in df.columns else "close"
            start_price = df.iloc[0][price_col]
            if start_price == 0 or pd.isna(start_price):
                continue
            
            df["normalized"] = (df[price_col] / start_price) * 100
            
            # 清理 NaN
            df = df.dropna(subset=["normalized"])
            
            # 取得名稱
            if symbol.startswith("^"):
                from app.models.index_price import INDEX_SYMBOLS
                info = INDEX_SYMBOLS.get(symbol, {})
                name = info.get("name_zh", symbol)
            else:
                info = yahoo_finance.get_stock_info(symbol)
                name = info.get("name", symbol) if info else symbol
            
            # 轉為列表
            history = []
            for _, row in df.iterrows():
                val = row["normalized"]
                # 檢查 NaN/Inf
                if math.isnan(val) or math.isinf(val):
                    continue
                history.append({
                    "date": str(row["date"]),
                    "value": round(val, 2),
                })
            
            if history:
                result[symbol] = {
                    "name": name,
                    "history": history,
                }
                
        except Exception as e:
            logger.error(f"處理 {symbol} 時發生錯誤: {e}")
            continue
    
    if not result:
        raise HTTPException(status_code=404, detail="找不到任何有效資料")
    
    return {
        "success": True,
        "days": days,
        "data": result,
    }
