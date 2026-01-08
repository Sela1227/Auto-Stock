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
        
        # 確保 name 正確獲取
        stock_name = ""
        if info:
            stock_name = info.get("name", "")
        if not stock_name:
            # 再次嘗試從本地映射表獲取
            from app.data_sources.yahoo_finance import TAIWAN_STOCK_NAMES
            stock_code = symbol.replace(".TW", "").replace(".TWO", "")
            stock_name = TAIWAN_STOCK_NAMES.get(stock_code, symbol)
        
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
    
    # 解析 symbols
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    
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
                    "date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else str(row["date"]),
                    "value": round(val, 2),
                    "price": round(float(row["close"]), 2),  # 顯示用原始價格
                })
            
            if history:
                end_price_adj = float(df.iloc[-1][price_col])
                result[symbol] = {
                    "symbol": symbol,
                    "name": name,
                    "start_price": round(float(df.iloc[0]["close"]), 2),  # 顯示用原始價格
                    "end_price": round(float(df.iloc[-1]["close"]), 2),   # 顯示用原始價格
                    "change_pct": round((end_price_adj / start_price - 1) * 100, 2),  # 計算用調整後價格
                    "data": history,
                }
                
                # 記錄日期用於對齊
                dates = set(h["date"] for h in history)
                if common_dates is None:
                    common_dates = dates
                else:
                    common_dates = common_dates.intersection(dates)
        
        except Exception as e:
            logger.error(f"處理 {symbol} 失敗: {e}")
            continue
    
    if not result:
        raise HTTPException(status_code=404, detail="找不到任何有效資料")
    
    return {
        "success": True,
        "data": {
            "symbols": list(result.keys()),
            "days": days,
            "stocks": result,
        }
    }


@router.get("/{symbol}/returns", summary="年化報酬率")
async def get_stock_returns(
    symbol: str,
):
    """
    計算股票的歷史年化報酬率 (CAGR)
    
    注意：Yahoo Finance 返回的是除權息調整後價格，
    因此計算出的 CAGR 已經等同於「配息再投入報酬率」
    
    回傳 1Y, 3Y, 5Y, 10Y 的 CAGR
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    from datetime import date, timedelta
    import math
    
    symbol = symbol.upper()
    logger.info(f"計算年化報酬率: {symbol}")
    
    try:
        # 取得 10 年股價歷史
        df = yahoo_finance.get_stock_history(symbol, period="10y")
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"找不到股票: {symbol}")
        
        # 確保有 date 欄位
        if 'date' not in df.columns:
            df = df.reset_index()
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'date'})
        
        df['date'] = pd.to_datetime(df['date']).dt.date
        df = df.sort_values('date').reset_index(drop=True)
        
        # 取得配息歷史（用於計算配息次數和殖利率參考）
        dividends_df = yahoo_finance.get_dividends(symbol, period="10y")
        
        # 建立配息字典 {date: amount}
        dividends = {}
        if dividends_df is not None and not dividends_df.empty:
            for _, row in dividends_df.iterrows():
                div_date = row['date']
                if isinstance(div_date, str):
                    div_date = datetime.strptime(div_date, '%Y-%m-%d').date()
                dividends[div_date] = float(row['amount'])
        
        logger.info(f"{symbol} 配息記錄: {len(dividends)} 筆")
        
        # 取得股票名稱
        info = yahoo_finance.get_stock_info(symbol)
        stock_name = info.get("name", symbol) if info else symbol
        
        # 現價（顯示用，用原始收盤價）
        current_price_display = float(df.iloc[-1]['close'])
        # 調整後現價（計算報酬率用）
        current_price_adj = float(df.iloc[-1]['adj_close'])
        current_date = df.iloc[-1]['date']
        
        # 計算不同期間的報酬率
        periods = [
            ("1Y", 1),
            ("3Y", 3),
            ("5Y", 5),
            ("10Y", 10),
        ]
        
        results = {}
        
        for period_name, years in periods:
            target_date = current_date - timedelta(days=years * 365)
            
            # 找到最接近目標日期的股價
            past_df = df[df['date'] <= target_date]
            
            if past_df.empty or len(past_df) < 10:
                results[period_name] = None
                continue
            
            start_row = past_df.iloc[-1]
            # 使用調整後價格計算報酬率（已包含分割和配息調整）
            start_price_adj = float(start_row['adj_close'])
            start_date = start_row['date']
            
            if start_price_adj <= 0:
                results[period_name] = None
                continue
            
            # 實際年數（更精確）
            actual_days = (current_date - start_date).days
            actual_years = actual_days / 365.25
            
            if actual_years < 0.5:
                results[period_name] = None
                continue
            
            # CAGR 計算（使用調整後價格，已包含分割和配息再投入效果）
            cagr = (current_price_adj / start_price_adj) ** (1 / actual_years) - 1
            
            # 計算期間內的配息統計（參考用）
            period_dividends = {d: amt for d, amt in dividends.items() 
                              if start_date < d <= current_date}
            
            total_dividends_per_share = sum(period_dividends.values())
            
            logger.info(f"{symbol} {period_name}: 起始日={start_date}, 起始價(調整後)={start_price_adj:.2f}, 現價(調整後)={current_price_adj:.2f}, CAGR={cagr*100:.2f}%")
            
            # 檢查數值有效性
            def safe_pct(val):
                if val is None or math.isnan(val) or math.isinf(val):
                    return None
                return round(val * 100, 2)
            
            results[period_name] = {
                "years": round(actual_years, 1),
                "start_date": start_date.isoformat(),
                "start_price": round(start_price_adj, 2),
                "end_price": round(current_price_adj, 2),
                "cagr": safe_pct(cagr),
                "dividend_count": len(period_dividends),
                "total_dividends": round(total_dividends_per_share, 4),
            }
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "name": stock_name,
                "current_price": round(current_price_display, 2),
                "current_date": current_date.isoformat(),
                "returns": results,
                "note": "CAGR 基於 Yahoo Finance 調整後價格計算，已包含分割調整及配息再投入效果"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"計算年化報酬率失敗 {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/debug-prices", summary="Debug: 查看原始價格")
async def debug_prices(
    symbol: str,
    years: int = Query(5, description="查詢年數"),
):
    """
    Debug 用：查看 Yahoo Finance 返回的原始價格
    用於驗證是否有除權息調整
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    from datetime import date, timedelta
    
    symbol = symbol.upper()
    
    try:
        df = yahoo_finance.get_stock_history(symbol, period=f"{years}y")
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"找不到股票: {symbol}")
        
        # 確保有 date 欄位
        if 'date' not in df.columns:
            df = df.reset_index()
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'date'})
        
        df['date'] = pd.to_datetime(df['date']).dt.date
        df = df.sort_values('date').reset_index(drop=True)
        
        # 取得配息記錄
        dividends_df = yahoo_finance.get_dividends(symbol, period=f"{years}y")
        dividends = []
        if dividends_df is not None and not dividends_df.empty:
            for _, row in dividends_df.iterrows():
                dividends.append({
                    "date": str(row['date']),
                    "amount": round(float(row['amount']), 4)
                })
        
        # 取樣幾個關鍵日期的價格
        sample_dates = []
        
        # 第一筆
        first = df.iloc[0]
        sample_dates.append({
            "date": str(first['date']),
            "close": round(float(first['close']), 2),
            "note": "最早"
        })
        
        # 每年初的價格
        for y in range(years, 0, -1):
            target = date.today() - timedelta(days=y*365)
            closest = df[df['date'] <= target]
            if not closest.empty:
                row = closest.iloc[-1]
                sample_dates.append({
                    "date": str(row['date']),
                    "close": round(float(row['close']), 2),
                    "note": f"約 {y} 年前"
                })
        
        # 最後一筆
        last = df.iloc[-1]
        sample_dates.append({
            "date": str(last['date']),
            "close": round(float(last['close']), 2),
            "note": "最新"
        })
        
        return {
            "success": True,
            "symbol": symbol,
            "total_records": len(df),
            "date_range": {
                "start": str(df.iloc[0]['date']),
                "end": str(df.iloc[-1]['date'])
            },
            "sample_prices": sample_dates,
            "dividends": dividends,
            "dividend_count": len(dividends),
            "total_dividends": round(sum(d['amount'] for d in dividends), 4)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug prices 失敗 {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
