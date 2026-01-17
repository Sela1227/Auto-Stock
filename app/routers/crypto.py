"""
加密貨幣和市場情緒 API 路由

🆕 2026-01-17 更新：
- 加入查詢結果快取功能，查詢過的加密貨幣會儲存到本地資料庫
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import pandas as pd
import logging

from app.schemas.schemas import MarketSentimentResponse

router = APIRouter(tags=["加密貨幣"])
logger = logging.getLogger(__name__)

# 加密貨幣對應的 Yahoo Finance 代號
CRYPTO_YAHOO_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BITCOIN": "BTC-USD",
    "ETHEREUM": "ETH-USD",
}


@router.get("/api/crypto/{symbol}", summary="查詢加密貨幣")
async def get_crypto_analysis(
    symbol: str,
    refresh: bool = Query(False, description="是否強制更新資料"),
):
    """
    查詢單一加密貨幣的技術分析報告
    
    - **symbol**: 加密貨幣代號 (BTC, ETH)
    - **refresh**: 是否強制更新資料
    """
    from app.data_sources.coingecko import coingecko
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.indicator_service import indicator_service
    
    symbol = symbol.upper()
    logger.info(f"開始查詢加密貨幣: {symbol}")
    
    # 驗證代號
    yahoo_symbol = CRYPTO_YAHOO_MAP.get(symbol)
    if not yahoo_symbol and not coingecko.validate_symbol(symbol):
        logger.warning(f"不支援的加密貨幣: {symbol}")
        raise HTTPException(
            status_code=400,
            detail=f"不支援的加密貨幣: {symbol}，目前僅支援 BTC 和 ETH"
        )
    
    df = None
    info = None
    data_source = None
    
    # 優先嘗試 CoinGecko
    try:
        logger.info(f"嘗試從 CoinGecko 取得 {symbol} 資料...")
        df = coingecko.get_ohlc(symbol, days=365)
        if df is not None and not df.empty:
            info = coingecko.get_coin_info(symbol)
            data_source = "CoinGecko"
            logger.info(f"成功從 CoinGecko 取得 {len(df)} 筆資料")
    except Exception as e:
        logger.warning(f"CoinGecko API 失敗: {e}")
    
    # 如果 CoinGecko 失敗，使用 Yahoo Finance 備用
    if df is None or df.empty:
        yahoo_symbol = CRYPTO_YAHOO_MAP.get(symbol, f"{symbol}-USD")
        logger.info(f"CoinGecko 失敗，嘗試 Yahoo Finance: {yahoo_symbol}")
        
        try:
            df = yahoo_finance.get_stock_history(yahoo_symbol, period="1y")
            if df is not None and not df.empty:
                data_source = "Yahoo Finance"
                logger.info(f"成功從 Yahoo Finance 取得 {len(df)} 筆資料")
                # 從 Yahoo Finance 取得基本資訊
                try:
                    yf_info = yahoo_finance.get_stock_info(yahoo_symbol)
                    if yf_info:
                        info = {
                            "name": yf_info.get("shortName") or yf_info.get("name") or symbol,
                            "market_cap": yf_info.get("market_cap") or yf_info.get("marketCap"),
                            "total_volume": yf_info.get("total_volume"),
                        }
                except Exception as e:
                    logger.warning(f"取得 Yahoo Finance info 失敗: {e}")
                    info = {"name": symbol}
        except Exception as e:
            logger.error(f"Yahoo Finance 也失敗: {e}")
    
    # 如果兩個都失敗
    if df is None or df.empty:
        raise HTTPException(
            status_code=503,
            detail=f"無法取得 {symbol} 資料。CoinGecko 和 Yahoo Finance 都無法連接。請稍後再試。"
        )
    
    logger.info(f"使用 {data_source} 資料，共 {len(df)} 筆")
    
    # 確保有必要的欄位 (在 try 塊外面先處理)
    if 'volume' not in df.columns:
        df['volume'] = 0
        logger.warning(f"{symbol} 沒有 volume 資料，已填入 0")
    
    # 確保 volume 不是 None 或 NaN
    df['volume'] = df['volume'].fillna(0).astype(float)
    
    try:
        # 計算技術指標
        df = indicator_service.calculate_all_indicators(df)
        
        # 取得最新資料
        latest = df.iloc[-1]
        current_price = float(latest['close'])
        
        # 漲跌幅計算
        def calc_change(days):
            try:
                if len(df) > days:
                    old_price = float(df.iloc[-days-1]['close'])
                    return round((current_price - old_price) / old_price * 100, 2)
            except:
                pass
            return None
        
        # 均線資訊 (加密貨幣用 MA7/25/99)
        ma7 = float(df['close'].tail(7).mean()) if len(df) >= 7 else None
        ma25 = float(df['close'].tail(25).mean()) if len(df) >= 25 else None
        ma99 = float(df['close'].tail(99).mean()) if len(df) >= 99 else None
        
        # 判斷均線排列
        alignment = "neutral"
        if ma7 and ma25 and ma99:
            if current_price > ma7 > ma25 > ma99:
                alignment = "bullish"
            elif current_price < ma7 < ma25 < ma99:
                alignment = "bearish"
        
        # RSI (小寫: rsi)
        rsi_value = float(latest.get('rsi', 50)) if 'rsi' in latest else 50
        rsi_status = "overbought" if rsi_value > 70 else "oversold" if rsi_value < 30 else "neutral"
        
        # MACD (小寫: macd_dif, macd_dea)
        macd_dif = float(latest.get('macd_dif', 0)) if 'macd_dif' in latest else 0
        macd_dea = float(latest.get('macd_dea', 0)) if 'macd_dea' in latest else 0
        macd_status = "bullish" if macd_dif > macd_dea else "bearish"
        
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
        
        # 取得名稱和成交量
        crypto_name = info.get("name", symbol) if info else symbol
        volume_24h = info.get("total_volume") if info else None
        day_change = calc_change(1)
        
        # 🆕 將查詢結果寫入快取
        try:
            from app.services.cache_helper import cache_crypto_price
            
            cache_crypto_price(
                symbol=symbol,
                name=crypto_name,
                price=current_price,
                change_pct=day_change,
                volume=int(volume_24h) if volume_24h else None
            )
            logger.info(f"📦 加密貨幣快取已更新: {symbol} = ${current_price}")
        except Exception as e:
            # 快取失敗不影響主流程
            logger.warning(f"加密貨幣快取更新失敗（不影響查詢）: {e}")
        
        return {
            "success": True,
            "symbol": symbol,
            "name": crypto_name,
            "asset_type": "crypto",
            "price": {
                "current": current_price,
                "ath": info.get("ath") if info else None,
                "from_ath_pct": info.get("ath_change_percentage") if info else None,
            },
            "change": {
                "day": day_change,
                "week": calc_change(7),
                "month": calc_change(30),
                "year": calc_change(365),
            },
            "market": {
                "market_cap": info.get("market_cap") if info else None,
                "market_cap_rank": info.get("market_cap_rank") if info else None,
                "volume_24h": volume_24h,
            },
            "indicators": {
                "ma": {
                    "ma7": ma7,
                    "ma25": ma25,
                    "ma99": ma99,
                    "alignment": alignment,
                    "price_vs_ma7": "above" if ma7 and current_price > ma7 else "below",
                    "price_vs_ma25": "above" if ma25 and current_price > ma25 else "below",
                    "price_vs_ma99": "above" if ma99 and current_price > ma99 else "below",
                },
                "rsi": {
                    "value": rsi_value,
                    "period": 14,
                    "status": rsi_status,
                },
                "macd": {
                    "dif": macd_dif,
                    "macd": macd_dea,
                    "status": macd_status,
                },
            },
            "score": {
                "buy": buy_score,
                "sell": sell_score,
                "rating": rating,
            },
            "chart_data": {
                "dates": [str(d) for d in df['date'].tail(365).tolist()] if 'date' in df.columns else [],
                "prices": [float(p) for p in df['close'].tail(365).tolist()] if 'close' in df.columns else [],
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


@router.get("/api/crypto/{symbol}/chart", summary="取得加密貨幣圖表")
async def get_crypto_chart(
    symbol: str,
    days: int = Query(120, ge=30, le=365, description="顯示天數"),
):
    """
    生成加密貨幣技術分析圖表
    
    - **symbol**: 加密貨幣代號 (BTC, ETH)
    - **days**: 顯示天數 (30-365)
    
    回傳 PNG 圖片
    """
    from app.data_sources.coingecko import coingecko
    from app.services.chart_service import chart_service
    
    symbol = symbol.upper()
    
    df = coingecko.get_ohlc(symbol, days=days)
    
    if df is None or df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"找不到加密貨幣: {symbol}"
        )
    
    # 取得名稱
    info = coingecko.get_coin_info(symbol)
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
