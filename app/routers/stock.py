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
            
            # 正規化：起始價格 = 100
            start_price = df.iloc[0]["close"]
            if start_price == 0 or pd.isna(start_price):
                continue
            
            df["normalized"] = (df["close"] / start_price) * 100
            
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
                    "price": round(float(row["close"]), 2),
                })
            
            if history:
                result[symbol] = {
                    "symbol": symbol,
                    "name": name,
                    "start_price": round(float(start_price), 2),
                    "end_price": round(float(df.iloc[-1]["close"]), 2),
                    "change_pct": round((df.iloc[-1]["close"] / start_price - 1) * 100, 2),
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
    計算股票的歷史年化報酬率（含配息再投入）
    
    回傳 1Y, 3Y, 5Y, 10Y 的：
    - price_return: 純價格報酬率
    - total_return: 含配息
    - reinvested_return: 配息再投入
    - dividend_yield: 年均殖利率
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
        
        # 取得配息歷史
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
        
        # 現價
        current_price = float(df.iloc[-1]['close'])
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
            start_price = float(start_row['close'])
            start_date = start_row['date']
            
            if start_price <= 0:
                results[period_name] = None
                continue
            
            # 實際年數（更精確）
            actual_days = (current_date - start_date).days
            actual_years = actual_days / 365.25
            
            if actual_years < 0.5:
                results[period_name] = None
                continue
            
            # === 1. 純價格報酬率 ===
            price_return = (current_price / start_price) ** (1 / actual_years) - 1
            
            # === 2. 計算期間內的配息 ===
            period_dividends = {d: amt for d, amt in dividends.items() 
                              if start_date < d <= current_date}
            
            total_dividends_per_share = sum(period_dividends.values())
            
            # === 3. 含配息報酬率（不再投入）===
            # 終值 = 現價 + 累積配息
            total_value = current_price + total_dividends_per_share
            total_return = (total_value / start_price) ** (1 / actual_years) - 1
            
            # === 4. 配息再投入報酬率 ===
            # 模擬持有 1 股，配息再投入
            shares = 1.0
            
            # 取得期間內的每日股價用於配息再投入
            period_df = df[(df['date'] > start_date) & (df['date'] <= current_date)]
            
            # 按年度計算殖利率
            yearly_yields = {}  # {year: 該年度殖利率總和}
            
            for div_date, div_amount in sorted(period_dividends.items()):
                # 找到配息日的股價
                div_day_df = period_df[period_df['date'] <= div_date]
                if div_day_df.empty:
                    continue
                    
                div_price = float(div_day_df.iloc[-1]['close'])
                if div_price > 0:
                    # 計算該次配息的殖利率 = 配息金額 / 該日股價
                    div_yield = div_amount / div_price
                    
                    # 按年度累加殖利率
                    div_year = div_date.year
                    yearly_yields[div_year] = yearly_yields.get(div_year, 0) + div_yield
                    
                    # 配息再投入計算
                    dividend_received = shares * div_amount
                    new_shares = dividend_received / div_price
                    shares += new_shares
            
            # 年均殖利率 = 各年度殖利率加總 / 年數
            if yearly_yields:
                total_yearly_yield = sum(yearly_yields.values())
                annual_div_yield = total_yearly_yield / len(yearly_yields)
                logger.info(f"{symbol} {period_name} 殖利率計算: 年度數={len(yearly_yields)}, 各年={yearly_yields}, 平均={annual_div_yield*100:.2f}%")
            else:
                annual_div_yield = 0
            
            # 終值 = 累積股數 × 現價
            reinvested_value = shares * current_price
            reinvested_return = (reinvested_value / start_price) ** (1 / actual_years) - 1
            
            # 檢查數值有效性
            def safe_pct(val):
                if val is None or math.isnan(val) or math.isinf(val):
                    return None
                return round(val * 100, 2)
            
            results[period_name] = {
                "years": round(actual_years, 1),
                "start_date": start_date.isoformat(),
                "start_price": round(start_price, 2),
                "end_price": round(current_price, 2),
                "price_return": safe_pct(price_return),
                "total_return": safe_pct(total_return),
                "reinvested_return": safe_pct(reinvested_return),
                "dividend_count": len(period_dividends),
                "total_dividends": round(total_dividends_per_share, 4),
                "annual_yield": safe_pct(annual_div_yield),
            }
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "name": stock_name,
                "current_price": round(current_price, 2),
                "current_date": current_date.isoformat(),
                "returns": results,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"計算年化報酬率失敗 {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
