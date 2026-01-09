"""
Yahoo Finance è³‡æ–™ä¾†æº
ä½¿ç”¨ yfinance å¥—ä»¶æŠ“å–ç¾Žè‚¡è³‡æ–™
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# å¸¸ç”¨å°è‚¡ä¸­æ–‡åç¨±å°ç…§è¡¨
TAIWAN_STOCK_NAMES = {
    # æ¬Šå€¼è‚¡
    "2330": "å°ç©é›»",
    "2317": "é´»æµ·",
    "2454": "è¯ç™¼ç§‘",
    "2308": "å°é”é›»",
    "2412": "ä¸­è¯é›»",
    "2303": "è¯é›»",
    "2002": "ä¸­é‹¼",
    "1301": "å°å¡‘",
    "1303": "å—äºž",
    "1326": "å°åŒ–",
    "6505": "å°å¡‘åŒ–",
    "1101": "å°æ³¥",
    "1102": "äºžæ³¥",
    # é‡‘èžè‚¡
    "2881": "å¯Œé‚¦é‡‘",
    "2882": "åœ‹æ³°é‡‘",
    "2884": "çŽ‰å±±é‡‘",
    "2886": "å…†è±é‡‘",
    "2891": "ä¸­ä¿¡é‡‘",
    "2892": "ç¬¬ä¸€é‡‘",
    "2880": "è¯å—é‡‘",
    "2883": "é–‹ç™¼é‡‘",
    "2885": "å…ƒå¤§é‡‘",
    "2887": "å°æ–°é‡‘",
    "2888": "æ–°å…‰é‡‘",
    "2890": "æ°¸è±é‡‘",
    "5880": "åˆåº«é‡‘",
    # é›»å­è‚¡
    "2912": "çµ±ä¸€è¶…",
    "2357": "è¯ç¢©",
    "2382": "å»£é”",
    "2395": "ç ”è¯",
    "3008": "å¤§ç«‹å…‰",
    "3711": "æ—¥æœˆå…‰æŠ•æŽ§",
    "2345": "æ™ºé‚¦",
    "2379": "ç‘žæ˜±",
    "2327": "åœ‹å·¨",
    "3034": "è¯è© ",
    "2301": "å…‰å¯¶ç§‘",
    "2408": "å—äºžç§‘",
    "2474": "å¯æˆ",
    "2049": "ä¸ŠéŠ€",
    "3045": "å°ç£å¤§",
    "4904": "é å‚³",
    "3231": "ç·¯å‰µ",
    "2356": "è‹±æ¥­é”",
    "2324": "ä»å¯¶",
    "2353": "å®ç¢",
    "2377": "å¾®æ˜Ÿ",
    "2376": "æŠ€å˜‰",
    "2388": "å¨ç››",
    "2409": "å‹é”",
    "3481": "ç¾¤å‰µ",
    "2404": "æ¼¢å”",
    # å‚³ç”¢è‚¡
    "5871": "ä¸­ç§Ÿ-KY",
    "1216": "çµ±ä¸€",
    "2207": "å’Œæ³°è»Š",
    "2105": "æ­£æ–°",
    "9910": "è±æ³°",
    "2603": "é•·æ¦®",
    "2609": "é™½æ˜Ž",
    "2615": "è¬æµ·",
    "2618": "é•·æ¦®èˆª",
    "2610": "è¯èˆª",
    "1402": "é æ±æ–°",
    "1590": "äºžå¾·å®¢-KY",
    "4938": "å’Œç¢©",
    "2014": "ä¸­é´»",
    "2006": "æ±å’Œé‹¼éµ",
    "2015": "è±èˆˆ",
    # AI æ¦‚å¿µè‚¡
    "3443": "å‰µæ„",
    "5274": "ä¿¡é©Š",
    "6669": "ç·¯ç©Ž",
    "3661": "ä¸–èŠ¯-KY",
    "6415": "çŸ½åŠ›-KY",
    "3533": "å˜‰æ¾¤",
    "2368": "é‡‘åƒé›»",
    "6176": "ç‘žå„€",
    "3037": "æ¬£èˆˆ",
    "5347": "ä¸–ç•Œ",
    "8046": "å—é›»",
    "6239": "åŠ›æˆ",
    # å…¶ä»–ç†±é–€è‚¡
    "2498": "å®é”é›»",
    "3706": "ç¥žé”",
    "2354": "é´»æº–",
    "2360": "è‡´èŒ‚",
    "2393": "å„„å…‰",
    "2383": "å°å…‰é›»",
    "3036": "æ–‡æ›„",
    "6446": "è—¥è¯è—¥",
    "4743": "åˆä¸€",
    "6547": "é«˜ç«¯ç–«è‹—",
    "2344": "è¯é‚¦é›»",
    "2449": "äº¬å…ƒé›»å­",
    "6531": "æ„›æ™®",
    "3017": "å¥‡é‹",
    "2059": "å·æ¹–",
    "2385": "ç¾¤å…‰",
    "6770": "åŠ›ç©é›»",
    "8299": "ç¾¤è¯",
    "6285": "å•Ÿç¢",
    "2347": "è¯å¼·",
    "2458": "ç¾©éš†",
    "3023": "ä¿¡é‚¦",
    "2492": "è¯æ–°ç§‘",
    "3044": "å¥é¼Ž",
    "5483": "ä¸­ç¾Žæ™¶",
    "6488": "ç’°çƒæ™¶",
    "3529": "åŠ›æ—º",
    "2542": "èˆˆå¯Œç™¼",
    "2545": "çš‡ç¿”",
    "2504": "åœ‹ç”¢",
    "2520": "å† å¾·",
    "2534": "å®ç››",
    "9921": "å·¨å¤§",
    "9914": "ç¾Žåˆ©é”",
    "1227": "ä½³æ ¼",
    "1229": "è¯è¯",
    "1234": "é»‘æ¾",
    "2912": "çµ±ä¸€è¶…",
    "2915": "æ½¤æ³°å…¨",
    "9904": "å¯¶æˆ",
    "9945": "æ½¤æ³°æ–°",
    # ä¸Šæ«ƒè‚¡ç¥¨ (.TWO)
    "8069": "å…ƒå¤ª",
    "6547": "é«˜ç«¯ç–«è‹—",
    "4743": "åˆä¸€",
    "6446": "è—¥è¯è—¥",
    "5765": "æ°¸ä¿¡é†«è—¥",
    "8086": "å®æ·ç§‘",
    "3105": "ç©©æ‡‹",
    "5269": "ç¥¥ç¢©",
    "6409": "æ—­éš¼",
    "6510": "ç²¾æ¸¬",
    "3293": "é‘«å–¬",
    "6533": "æ™¶å¿ƒç§‘",
    "6477": "å®‰é›†",
    "6568": "å®è§€",
    "3163": "æ³¢è‹¥å¨",
    "6197": "ä½³å¿…çª",
    "5388": "ä¸­ç£Š",
    "6781": "AES-KY",
    "3152": "ç’Ÿå¾·",
    "5289": "å®œé¼Ž",
    "6223": "æ—ºçŸ½",
    "8150": "å—èŒ‚",
    "5484": "æ…§å‹",
    "6442": "å…‰è–",
    "6472": "ä¿ç‘ž",
    "4966": "è­œç‘ž-KY",
    "6789": "é‡‡éˆº",
    "6640": "å‡è¯",
    "3260": "å¨å‰›",
    "4763": "ææ–™-KY",
    "5299": "æ°åŠ›",
    "8016": "çŸ½å‰µ",
    "6719": "åŠ›æ™º",
    "6456": "GIS-KY",
    "6451": "è¨ŠèŠ¯-KY",
    "3707": "æ¼¢ç£Š",
    "4968": "ç«‹ç©",
    "6679": "éˆºå¤ª",
    "6592": "å’Œæ½¤ä¼æ¥­",
    "6591": "å‹•åŠ›-KY",
    "5425": "å°åŠ",
    "6803": "å´‡è¶Šé›»",
    "3527": "èšç©",
    "6449": "éˆºé‚¦",
    # ETF
    "0050": "å…ƒå¤§å°ç£50",
    "0056": "å…ƒå¤§é«˜è‚¡æ¯",
    "00878": "åœ‹æ³°æ°¸çºŒé«˜è‚¡æ¯",
    "00919": "ç¾¤ç›Šå°ç£ç²¾é¸é«˜æ¯",
    "00929": "å¾©è¯å°ç£ç§‘æŠ€å„ªæ¯",
    "006208": "å¯Œé‚¦å°50",
    "00713": "å…ƒå¤§å°ç£é«˜æ¯ä½Žæ³¢",
    "00692": "å¯Œé‚¦å…¬å¸æ²»ç†",
}


class YahooFinanceClient:
    """Yahoo Finance è³‡æ–™æ“·å–å®¢æˆ¶ç«¯"""
    
    def __init__(self):
        pass
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        å–å¾—è‚¡ç¥¨åŸºæœ¬è³‡è¨Š
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ (å¦‚ AAPL, TSLA, 2330.TW)
            
        Returns:
            è‚¡ç¥¨è³‡è¨Šå­—å…¸ï¼ŒåŒ…å«åç¨±ã€å¸‚å€¼ç­‰
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            
            # å–å¾—åç¨±ï¼šå„ªå…ˆä½¿ç”¨ longNameï¼Œç„¶å¾Œ shortName
            name = info.get("longName") or info.get("shortName") or symbol
            
            # å°æ–¼å°è‚¡ï¼Œå„ªå…ˆä½¿ç”¨æœ¬åœ°æ˜ å°„è¡¨çš„ä¸­æ–‡åç¨±
            if symbol.endswith(".TW") or symbol.endswith(".TWO"):
                # æå–è‚¡ç¥¨ä»£è™Ÿ (åŽ»æŽ‰ .TW æˆ– .TWO)
                stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                # å„ªå…ˆä½¿ç”¨æœ¬åœ°æ˜ å°„è¡¨
                if stock_code in TAIWAN_STOCK_NAMES:
                    name = TAIWAN_STOCK_NAMES[stock_code]
                else:
                    # å˜—è©¦å¾ž Yahoo Finance å–å¾—ä¸­æ–‡å
                    display_name = info.get("displayName")
                    if display_name:
                        name = display_name
            
            # å³ä½¿ info ä¸å®Œæ•´ï¼Œä¹Ÿè¿”å›žåŸºæœ¬è³‡è¨Š
            return {
                "symbol": info.get("symbol", symbol),
                "name": name,
                "shortName": info.get("shortName", ""),
                "longName": info.get("longName", ""),
                "currency": info.get("currency", "TWD" if symbol.endswith((".TW", ".TWO")) else "USD"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            }
        except Exception as e:
            logger.error(f"å–å¾—è‚¡ç¥¨è³‡è¨Šå¤±æ•— {symbol}: {e}")
            # å³ä½¿å‡ºéŒ¯ï¼Œå°æ–¼å°è‚¡ä¹Ÿå˜—è©¦è¿”å›žæœ¬åœ°åç¨±
            if symbol.endswith(".TW") or symbol.endswith(".TWO"):
                stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                name = TAIWAN_STOCK_NAMES.get(stock_code, symbol)
                return {
                    "symbol": symbol,
                    "name": name,
                    "shortName": "",
                    "longName": "",
                    "currency": "TWD",
                    "market_cap": None,
                    "sector": None,
                    "industry": None,
                    "fifty_two_week_high": None,
                    "fifty_two_week_low": None,
                }
            return None
    
    def get_stock_history(
        self,
        symbol: str,
        period: str = "1y",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Optional[pd.DataFrame]:
        """
        å–å¾—è‚¡ç¥¨æ­·å²åƒ¹æ ¼è³‡æ–™
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            period: è³‡æ–™æœŸé–“ (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: é–‹å§‹æ—¥æœŸï¼ˆèˆ‡ end æ­é…ä½¿ç”¨æ™‚ï¼Œperiod æœƒè¢«å¿½ç•¥ï¼‰
            end: çµæŸæ—¥æœŸ
            
        Returns:
            åŒ…å« OHLCV çš„ DataFrameï¼Œå…¶ä¸­ï¼š
            - close: åŽŸå§‹æ”¶ç›¤åƒ¹ï¼ˆç”¨æ–¼é¡¯ç¤ºï¼‰
            - adj_close: åˆ†å‰²èª¿æ•´å¾Œåƒ¹æ ¼ï¼ˆç”¨æ–¼åœ–è¡¨ï¼Œä¸å«é…æ¯ï¼‰
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # å–å¾—åŽŸå§‹åƒ¹æ ¼
            if start and end:
                df_raw = ticker.history(start=start, end=end, auto_adjust=False)
            else:
                df_raw = ticker.history(period=period, auto_adjust=False)
            
            if df_raw.empty:
                logger.warning(f"ç„¡æ­·å²è³‡æ–™: {symbol}")
                return None
            
            df_raw = df_raw.reset_index()
            
            # æ¨™æº–åŒ–æ—¥æœŸæ¬„ä½
            date_col = "Date" if "Date" in df_raw.columns else "Datetime"
            
            # å»ºç«‹çµæžœ DataFrame
            df = pd.DataFrame()
            df["date"] = pd.to_datetime(df_raw[date_col]).dt.date
            df["open"] = df_raw["Open"].values
            df["high"] = df_raw["High"].values
            df["low"] = df_raw["Low"].values
            df["close"] = df_raw["Close"].values
            df["volume"] = df_raw["Volume"].values if "Volume" in df_raw.columns else 0
            
            # åµæ¸¬ä¸¦èª¿æ•´åˆ†å‰²ï¼ˆä¸å«é…æ¯ï¼‰
            df = self._detect_and_adjust_splits(df, symbol)
            
            # åŠ å…¥è‚¡ç¥¨ä»£è™Ÿ
            df["symbol"] = symbol.upper()
            
            return df
            
        except Exception as e:
            logger.error(f"å–å¾—æ­·å²è³‡æ–™å¤±æ•— {symbol}: {e}")
            return None
    
    def _detect_and_adjust_splits(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        åµæ¸¬åƒ¹æ ¼æ–·å´–ä¸¦èª¿æ•´æ­·å²åƒ¹æ ¼ï¼ˆåªè™•ç†åˆ†å‰²ï¼Œä¸å«é…æ¯ï¼‰
        
        ç•¶åµæ¸¬åˆ°åƒ¹æ ¼çªç„¶ä¸‹è·Œè¶…éŽ 40%ï¼ˆå¯èƒ½æ˜¯åˆ†å‰²ï¼‰ï¼Œ
        æœƒè‡ªå‹•èª¿æ•´åˆ†å‰²å‰çš„åƒ¹æ ¼ï¼Œä½¿æ•´å€‹åºåˆ—é€£çºŒã€‚
        """
        if len(df) < 2:
            df['adj_close'] = df['close'].copy()
            return df
        
        df = df.copy()
        df = df.sort_values('date').reset_index(drop=True)
        
        # è¨ˆç®—æ¯æ—¥æ¼²è·Œå¹…
        df['pct_change'] = df['close'].pct_change()
        
        # åµæ¸¬åˆ†å‰²é»žï¼ˆåƒ¹æ ¼ä¸‹è·Œè¶…éŽ 40%ï¼‰
        split_indices = []
        for i in range(1, len(df)):
            pct = df.loc[i, 'pct_change']
            if pd.notna(pct) and pct < -0.40:
                prev_close = float(df.loc[i-1, 'close'])
                curr_close = float(df.loc[i, 'close'])
                if curr_close > 0:
                    ratio = prev_close / curr_close
                    rounded_ratio = round(ratio)
                    # åªæœ‰æ¯”çŽ‡æŽ¥è¿‘æ•´æ•¸æ™‚æ‰èªç‚ºæ˜¯åˆ†å‰²ï¼ˆ2, 3, 4, 5, 10 ç­‰ï¼‰
                    if rounded_ratio >= 2 and abs(ratio - rounded_ratio) < 0.3:
                        split_indices.append({
                            'index': i,
                            'date': df.loc[i, 'date'],
                            'ratio': rounded_ratio,
                            'prev_close': prev_close,
                            'curr_close': curr_close
                        })
                        logger.info(f"{symbol} åµæ¸¬åˆ°åˆ†å‰²: {df.loc[i, 'date']}, æ¯”çŽ‡ 1:{rounded_ratio}, å‰æ”¶ {prev_close:.2f} -> ç¾æ”¶ {curr_close:.2f}")
        
        # åˆå§‹åŒ–èª¿æ•´å¾Œåƒ¹æ ¼
        df['adj_close'] = df['close'].astype(float)
        
        # å¾žæœ€è¿‘çš„åˆ†å‰²é–‹å§‹å¾€å‰èª¿æ•´ï¼ˆä½¿ç”¨ç´¯ç©å› å­ï¼‰
        if split_indices:
            cumulative_factor = 1.0
            
            for split in reversed(split_indices):
                idx = split['index']
                ratio = split['ratio']
                cumulative_factor *= ratio
                
                # èª¿æ•´åˆ†å‰²é»žä¹‹å‰çš„æ‰€æœ‰åƒ¹æ ¼ï¼ˆç”¨åŽŸå§‹ close é™¤ä»¥ç´¯ç©å› å­ï¼‰
                df.loc[:idx-1, 'adj_close'] = df.loc[:idx-1, 'close'].astype(float) / cumulative_factor
            
            logger.info(f"{symbol} å·²èª¿æ•´ {len(split_indices)} æ¬¡åˆ†å‰²ï¼Œç¸½èª¿æ•´å› å­: {cumulative_factor}")
        
        # ç§»é™¤è‡¨æ™‚æ¬„ä½
        df = df.drop(columns=['pct_change'], errors='ignore')
        
        return df
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        å–å¾—è‚¡ç¥¨å³æ™‚ï¼ˆå»¶é²ï¼‰å ±åƒ¹
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            
        Returns:
            åŒ…å«ç•¶å‰åƒ¹æ ¼å’Œæ¼²è·Œè³‡è¨Šçš„å­—å…¸
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            # å˜—è©¦å–å¾—å³æ™‚åƒ¹æ ¼
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
            
            if not current_price:
                # å¾žæ­·å²è³‡æ–™å–å¾—æœ€æ–°æ”¶ç›¤åƒ¹ï¼ˆä½¿ç”¨åŽŸå§‹åƒ¹æ ¼ï¼‰
                hist = ticker.history(period="5d", auto_adjust=False)
                if not hist.empty:
                    current_price = hist["Close"].iloc[-1]
                    if len(hist) >= 2:
                        previous_close = hist["Close"].iloc[-2]
            
            if not current_price:
                return None
            
            change = current_price - previous_close if previous_close else 0
            change_pct = (change / previous_close * 100) if previous_close else 0
            
            return {
                "symbol": symbol.upper(),
                "price": round(current_price, 2),
                "previous_close": round(previous_close, 2) if previous_close else None,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
            }
            
        except Exception as e:
            logger.error(f"å–å¾—å³æ™‚å ±åƒ¹å¤±æ•— {symbol}: {e}")
            return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        快速驗證股票代號是否有效
        
        使用 history API 而非 info，速度快 5-10 倍
        
        Args:
            symbol: 股票代號
            
        Returns:
            是否為有效代號
        """
        try:
            ticker = yf.Ticker(symbol)
            # 只抓 1 天資料，比 info 快很多
            hist = ticker.history(period="1d")
            return not hist.empty
        except Exception:
            return False
    
    def get_dividends(
        self,
        symbol: str,
        period: str = "10y",
    ) -> Optional[pd.DataFrame]:
        """
        å–å¾—è‚¡ç¥¨é…æ¯æ­·å²
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            period: è³‡æ–™æœŸé–“ (1y, 5y, 10y, max)
            
        Returns:
            åŒ…å«é…æ¯è¨˜éŒ„çš„ DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends
            
            if dividends.empty:
                logger.info(f"{symbol} ç„¡é…æ¯è¨˜éŒ„")
                return None
            
            # è½‰æ›æˆ DataFrame
            df = dividends.reset_index()
            df.columns = ["date", "amount"]
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["symbol"] = symbol.upper()
            
            # æ ¹æ“š period éŽæ¿¾
            if period != "max":
                years = int(period.replace("y", ""))
                cutoff_date = datetime.now().date() - timedelta(days=years * 365)
                df = df[df["date"] >= cutoff_date]
            
            return df
            
        except Exception as e:
            logger.error(f"å–å¾—é…æ¯è³‡æ–™å¤±æ•— {symbol}: {e}")
            return None
    
    def get_index_data(
        self,
        symbol: str,
        period: str = "10y",
    ) -> Optional[pd.DataFrame]:
        """
        å–å¾—å¸‚å ´æŒ‡æ•¸æ­·å²è³‡æ–™
        
        Args:
            symbol: æŒ‡æ•¸ä»£è™Ÿ (^GSPC, ^DJI, ^IXIC)
            period: è³‡æ–™æœŸé–“
            
        Returns:
            åŒ…å« OHLCV çš„ DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, auto_adjust=False)
            
            if df.empty:
                logger.warning(f"ç„¡æŒ‡æ•¸è³‡æ–™: {symbol}")
                return None
            
            # é‡è¨­ç´¢å¼•
            df = df.reset_index()
            
            # æ¨™æº–åŒ–æ¬„ä½åç¨±
            column_mapping = {
                "Date": "date",
                "Datetime": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
            existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=existing_columns)
            
            # ç¢ºä¿æ—¥æœŸæ˜¯ date é¡žåž‹
            df["date"] = pd.to_datetime(df["date"]).dt.date
            
            # è¨ˆç®—æ¼²è·Œ
            df["change"] = df["close"].diff()
            df["change_pct"] = df["close"].pct_change() * 100
            
            # åŠ å…¥ä»£è™Ÿ
            df["symbol"] = symbol
            
            # åªä¿ç•™éœ€è¦çš„æ¬„ä½
            keep_columns = ["symbol", "date", "open", "high", "low", "close", "volume", "change", "change_pct"]
            df = df[[c for c in keep_columns if c in df.columns]]
            
            return df
            
        except Exception as e:
            logger.error(f"å–å¾—æŒ‡æ•¸è³‡æ–™å¤±æ•— {symbol}: {e}")
            return None
    
    def get_all_indices(self, period: str = "10y") -> Dict[str, pd.DataFrame]:
        """
        å–å¾—æ‰€æœ‰ä¸‰å¤§æŒ‡æ•¸è³‡æ–™
        
        Returns:
            {symbol: DataFrame}
        """
        indices = ["^GSPC", "^DJI", "^IXIC"]
        result = {}
        
        for symbol in indices:
            df = self.get_index_data(symbol, period)
            if df is not None:
                result[symbol] = df
        
        return result
    
    def get_stock_history_extended(
        self,
        symbol: str,
        years: int = 10,
    ) -> Optional[pd.DataFrame]:
        """
        å–å¾—è‚¡ç¥¨å»¶ä¼¸æ­·å²è³‡æ–™ï¼ˆæ”¯æ´æ›´é•·æ™‚é–“ï¼‰
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            years: å¹´æ•¸ (1, 3, 5, 10)
            
        Returns:
            åŒ…å« OHLCV çš„ DataFrame
        """
        period_map = {
            1: "1y",
            2: "2y",
            3: "3y",  # yfinance ä¸æ”¯æ´ 3yï¼Œç”¨ 5y ä»£æ›¿
            5: "5y",
            10: "10y",
        }
        
        period = period_map.get(years, "10y")
        if years == 3:
            period = "5y"  # ç„¶å¾Œåœ¨ç¨‹å¼ä¸­éŽæ¿¾
        
        df = self.get_stock_history(symbol, period=period)
        
        if df is None:
            return None
        
        # å¦‚æžœæ˜¯ 3 å¹´ï¼Œéœ€è¦éŽæ¿¾
        if years == 3:
            cutoff_date = datetime.now().date() - timedelta(days=3 * 365)
            df = df[df["date"] >= cutoff_date]
        
        return df


# å»ºç«‹å…¨åŸŸå®¢æˆ¶ç«¯å¯¦ä¾‹
yahoo_finance = YahooFinanceClient()
