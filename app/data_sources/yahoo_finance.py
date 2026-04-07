"""
Yahoo Finance Ã¨Â³â€¡Ã¦â€“â„¢Ã¤Â¾â€ Ã¦ÂºÂ
Ã¤Â½Â¿Ã§â€Â¨ yfinance Ã¥Â¥â€”Ã¤Â»Â¶Ã¦Å â€œÃ¥Ââ€“Ã§Â¾Å½Ã¨â€šÂ¡Ã¨Â³â€¡Ã¦â€“â„¢
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Ã¥Â¸Â¸Ã§â€Â¨Ã¥ÂÂ°Ã¨â€šÂ¡Ã¤Â¸Â­Ã¦â€“â€¡Ã¥ÂÂÃ§Â¨Â±Ã¥Â°ÂÃ§â€¦Â§Ã¨Â¡Â¨
TAIWAN_STOCK_NAMES = {
    # ===== 權值股 =====
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2308": "台達電",
    "2412": "中華電",
    "2303": "聯電",
    "2002": "中鋼",
    "1301": "台塑",
    "1303": "南亞",
    "1326": "台化",
    "6505": "台塑化",
    "1101": "台泥",
    "1102": "亞泥",
    "1216": "統一",
    "2207": "和泰車",
    # ===== 金融股 =====
    "2881": "富邦金",
    "2882": "國泰金",
    "2884": "玉山金",
    "2886": "兆豐金",
    "2891": "中信金",
    "2892": "第一金",
    "2880": "華南金",
    "2883": "開發金",
    "2885": "元大金",
    "2887": "台新金",
    "2888": "新光金",
    "2890": "永豐金",
    "5880": "合庫金",
    "5876": "上海商銀",
    # ===== 電子股 =====
    "2912": "統一超",
    "2357": "華碩",
    "2382": "廣達",
    "2395": "研華",
    "3008": "大立光",
    "3711": "日月光投控",
    "2345": "智邦",
    "2379": "瑞昱",
    "2327": "國巨",
    "3034": "聯詠",
    "2301": "光寶科",
    "2408": "南亞科",
    "2474": "可成",
    "3045": "台灣大",
    "4904": "遠傳",
    "3231": "緯創",
    "2356": "英業達",
    "2353": "宏碁",
    "2324": "仁寶",
    "2377": "微星",
    "2376": "技嘉",
    "4938": "和碩",
    "2409": "友達",
    "3481": "群創",
    "6669": "緯穎",
    "3037": "欣興",
    "2344": "華邦電",
    "2337": "旺宏",
    "3443": "創意",
    "6488": "環球晶",
    "5269": "祥碩",
    "6415": "矽力-KY",
    "3661": "世芯-KY",
    "6239": "力成",
    "8046": "南電",
    "3017": "奇鋐",
    "6176": "瑞儀",
    "6285": "啟碁",
    "2492": "華新科",
    "3533": "嘉澤",
    "6531": "愛普",
    "3665": "貿聯-KY",
    "8454": "富邦媒",
    "2383": "台光電",
    "2351": "順德",
    "2354": "鴻準",
    "2360": "致茂",
    "2385": "群光",
    "2388": "威盛",
    "2392": "正崴",
    "2401": "凌陽",
    "2402": "毅嘉",
    # ===== 航運/傳產 =====
    "2603": "長榮",
    "2609": "陽明",
    "2615": "萬海",
    "2618": "長榮航",
    "2610": "華航",
    "2633": "台灣高鐵",
    "9910": "豐泰",
    "9921": "巨大",
    "5871": "中租-KY",
    "9941": "裕融",
    # ===== 生技 =====
    "6446": "藥華藥",
    "6547": "高端疫苗",
    # ===== ETF =====
    "0050": "元大台灣50",
    "0051": "元大中型100",
    "0052": "富邦科技",
    "0053": "元大電子",
    "0055": "元大MSCI金融",
    "0056": "元大高股息",
    "0057": "富邦摩台",
    "006205": "富邦上證",
    "006206": "元大上證50",
    "006208": "富邦台50",
    "00631L": "元大台灣50正2",
    "00632R": "元大台灣50反1",
    "00635U": "元大S&P黃金",
    "00636": "國泰中國A50",
    "00637L": "元大滬深300正2",
    "00639": "富邦深100",
    "00642U": "元大S&P石油",
    "00645": "富邦日本",
    "00646": "元大S&P500",
    "00647L": "元大S&P500正2",
    "00648R": "元大S&P500反1",
    "00650L": "復華香港正2",
    "00655L": "國泰中國A50正2",
    "00657": "國泰日經225",
    "00661": "元大日經225",
    "00662": "富邦NASDAQ",
    "00663L": "國泰臺灣加權正2",
    "00664R": "國泰臺灣加權反1",
    "00668": "國泰美國道瓊",
    "00669R": "國泰美國道瓊反1",
    "00670L": "富邦NASDAQ正2",
    "00675L": "富邦臺灣加權正2",
    "00676R": "富邦臺灣加權反1",
    "00677U": "富邦VIX",
    "00678": "群益NBI生技",
    "00680L": "元大美債20正2",
    "00681R": "元大美債20反1",
    "00682U": "元大美債20年",
    "00690": "兆豐藍籌30",
    "00692": "富邦公司治理",
    "00701": "國泰股利精選30",
    "00713": "元大台灣高息低波",
    "00730": "富邦臺灣優質高息",
    "00733": "富邦臺灣中小",
    "00757": "統一FANG+",
    "00762": "元大全球AI",
    "00770": "國泰北美科技",
    "00850": "元大臺灣ESG永續",
    "00851": "台新全球AI",
    "00852L": "國泰美國費半正2",
    "00875": "國泰網路資安",
    "00876": "元大全球5G",
    "00878": "國泰永續高股息",
    "00881": "國泰台灣5G+",
    "00882": "中信中國高股息",
    "00885": "富邦越南",
    "00886": "元大全球雲端服務",
    "00887": "永豐台灣ESG",
    "00888": "永豐美國費半",
    "00889": "永豐台灣智能車",
    "00891": "中信關鍵半導體",
    "00892": "富邦台灣半導體",
    "00893": "國泰智能電動車",
    "00894": "中信小資高價30",
    "00895": "富邦未來車",
    "00896": "中信綠能電動車",
    "00900": "富邦特選高股息30",
    "00901": "永豐智能車供應鏈",
    "00904": "新光臺灣半導體30",
    "00905": "FT臺灣Smart",
    "00907": "永豐優息存股",
    "00912": "中信臺灣智慧50",
    "00915": "凱基優選高股息30",
    "00916": "國泰全球品牌50",
    "00918": "大華優利高填息30",
    "00919": "群益台灣精選高息",
    "00921": "兆豐龍頭等權重",
    "00922": "國泰台灣領袖50",
    "00923": "群益半導體收益",
    "00929": "復華台灣科技優息",
    "00930": "永豐ESG低碳高息",
    "00931": "統一台灣高息動能",
    "00932": "兆豐永續高息等權",
    "00934": "中信成長高股息",
    "00935": "野村台灣新科技50",
    "00936": "台新臺灣IC設計",
    "00939": "統一台灣高息優選",
    "00940": "元大台灣價值高息",
}



class YahooFinanceClient:
    """Yahoo Finance Ã¨Â³â€¡Ã¦â€“â„¢Ã¦â€œÂ·Ã¥Ââ€“Ã¥Â®Â¢Ã¦Ë†Â¶Ã§Â«Â¯"""
    
    def __init__(self):
        pass
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Ã¥Ââ€“Ã¥Â¾â€”Ã¨â€šÂ¡Ã§Â¥Â¨Ã¥Å¸ÂºÃ¦Å“Â¬Ã¨Â³â€¡Ã¨Â¨Å 
        
        Args:
            symbol: Ã¨â€šÂ¡Ã§Â¥Â¨Ã¤Â»Â£Ã¨â„¢Å¸ (Ã¥Â¦â€š AAPL, TSLA, 2330.TW)
            
        Returns:
            Ã¨â€šÂ¡Ã§Â¥Â¨Ã¨Â³â€¡Ã¨Â¨Å Ã¥Â­â€”Ã¥â€¦Â¸Ã¯Â¼Å’Ã¥Å’â€¦Ã¥ÂÂ«Ã¥ÂÂÃ§Â¨Â±Ã£â‚¬ÂÃ¥Â¸â€šÃ¥â‚¬Â¼Ã§Â­â€°
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info or {}
            
            # Ã¥Ââ€“Ã¥Â¾â€”Ã¥ÂÂÃ§Â¨Â±Ã¯Â¼Å¡Ã¥â€žÂªÃ¥â€¦Ë†Ã¤Â½Â¿Ã§â€Â¨ longNameÃ¯Â¼Å’Ã§â€žÂ¶Ã¥Â¾Å’ shortName
            name = info.get("longName") or info.get("shortName") or symbol
            
            # Ã¥Â°ÂÃ¦â€“Â¼Ã¥ÂÂ°Ã¨â€šÂ¡Ã¯Â¼Å’Ã¥â€žÂªÃ¥â€¦Ë†Ã¤Â½Â¿Ã§â€Â¨Ã¦Å“Â¬Ã¥Å“Â°Ã¦ËœÂ Ã¥Â°â€žÃ¨Â¡Â¨Ã§Å¡â€žÃ¤Â¸Â­Ã¦â€“â€¡Ã¥ÂÂÃ§Â¨Â±
            if symbol.endswith(".TW") or symbol.endswith(".TWO"):
                # Ã¦ÂÂÃ¥Ââ€“Ã¨â€šÂ¡Ã§Â¥Â¨Ã¤Â»Â£Ã¨â„¢Å¸ (Ã¥Å½Â»Ã¦Å½â€° .TW Ã¦Ë†â€“ .TWO)
                stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                # Ã¥â€žÂªÃ¥â€¦Ë†Ã¤Â½Â¿Ã§â€Â¨Ã¦Å“Â¬Ã¥Å“Â°Ã¦ËœÂ Ã¥Â°â€žÃ¨Â¡Â¨
                if stock_code in TAIWAN_STOCK_NAMES:
                    name = TAIWAN_STOCK_NAMES[stock_code]
                else:
                    # Ã¥Ëœâ€”Ã¨Â©Â¦Ã¥Â¾Å¾ Yahoo Finance Ã¥Ââ€“Ã¥Â¾â€”Ã¤Â¸Â­Ã¦â€“â€¡Ã¥ÂÂ
                    display_name = info.get("displayName")
                    if display_name:
                        name = display_name
            
            # Ã¥ÂÂ³Ã¤Â½Â¿ info Ã¤Â¸ÂÃ¥Â®Å’Ã¦â€¢Â´Ã¯Â¼Å’Ã¤Â¹Å¸Ã¨Â¿â€Ã¥â€ºÅ¾Ã¥Å¸ÂºÃ¦Å“Â¬Ã¨Â³â€¡Ã¨Â¨Å 
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
            logger.error(f"Ã¥Ââ€“Ã¥Â¾â€”Ã¨â€šÂ¡Ã§Â¥Â¨Ã¨Â³â€¡Ã¨Â¨Å Ã¥Â¤Â±Ã¦â€¢â€” {symbol}: {e}")
            # Ã¥ÂÂ³Ã¤Â½Â¿Ã¥â€¡ÂºÃ©Å’Â¯Ã¯Â¼Å’Ã¥Â°ÂÃ¦â€“Â¼Ã¥ÂÂ°Ã¨â€šÂ¡Ã¤Â¹Å¸Ã¥Ëœâ€”Ã¨Â©Â¦Ã¨Â¿â€Ã¥â€ºÅ¾Ã¦Å“Â¬Ã¥Å“Â°Ã¥ÂÂÃ§Â¨Â±
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
        Ã¥Ââ€“Ã¥Â¾â€”Ã¨â€šÂ¡Ã§Â¥Â¨Ã¦Â­Â·Ã¥ÂÂ²Ã¥Æ’Â¹Ã¦Â Â¼Ã¨Â³â€¡Ã¦â€“â„¢
        
        Args:
            symbol: Ã¨â€šÂ¡Ã§Â¥Â¨Ã¤Â»Â£Ã¨â„¢Å¸
            period: Ã¨Â³â€¡Ã¦â€“â„¢Ã¦Å“Å¸Ã©â€“â€œ (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: Ã©â€“â€¹Ã¥Â§â€¹Ã¦â€”Â¥Ã¦Å“Å¸Ã¯Â¼Ë†Ã¨Ë†â€¡ end Ã¦ÂÂ­Ã©â€¦ÂÃ¤Â½Â¿Ã§â€Â¨Ã¦â„¢â€šÃ¯Â¼Å’period Ã¦Å“Æ’Ã¨Â¢Â«Ã¥Â¿Â½Ã§â€¢Â¥Ã¯Â¼â€°
            end: Ã§ÂµÂÃ¦ÂÅ¸Ã¦â€”Â¥Ã¦Å“Å¸
            
        Returns:
            Ã¥Å’â€¦Ã¥ÂÂ« OHLCV Ã§Å¡â€ž DataFrameÃ¯Â¼Å’Ã¥â€¦Â¶Ã¤Â¸Â­Ã¯Â¼Å¡
            - close: Ã¥Å½Å¸Ã¥Â§â€¹Ã¦â€Â¶Ã§â€ºÂ¤Ã¥Æ’Â¹Ã¯Â¼Ë†Ã§â€Â¨Ã¦â€“Â¼Ã©Â¡Â¯Ã§Â¤ÂºÃ¯Â¼â€°
            - adj_close: Ã¥Ë†â€ Ã¥â€°Â²Ã¨ÂªÂ¿Ã¦â€¢Â´Ã¥Â¾Å’Ã¥Æ’Â¹Ã¦Â Â¼Ã¯Â¼Ë†Ã§â€Â¨Ã¦â€“Â¼Ã¥Å“â€“Ã¨Â¡Â¨Ã¯Â¼Å’Ã¤Â¸ÂÃ¥ÂÂ«Ã©â€¦ÂÃ¦ÂÂ¯Ã¯Â¼â€°
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Ã¥Ââ€“Ã¥Â¾â€”Ã¥Å½Å¸Ã¥Â§â€¹Ã¥Æ’Â¹Ã¦Â Â¼
            if start and end:
                df_raw = ticker.history(start=start, end=end, auto_adjust=False)
            else:
                df_raw = ticker.history(period=period, auto_adjust=False)
            
            if df_raw.empty:
                logger.warning(f"Ã§â€žÂ¡Ã¦Â­Â·Ã¥ÂÂ²Ã¨Â³â€¡Ã¦â€“â„¢: {symbol}")
                return None
            
            df_raw = df_raw.reset_index()
            
            # Ã¦Â¨â„¢Ã¦Âºâ€“Ã¥Å’â€“Ã¦â€”Â¥Ã¦Å“Å¸Ã¦Â¬â€žÃ¤Â½Â
            date_col = "Date" if "Date" in df_raw.columns else "Datetime"
            
            # Ã¥Â»ÂºÃ§Â«â€¹Ã§ÂµÂÃ¦Å¾Å“ DataFrame
            df = pd.DataFrame()
            df["date"] = pd.to_datetime(df_raw[date_col]).dt.date
            df["open"] = df_raw["Open"].values
            df["high"] = df_raw["High"].values
            df["low"] = df_raw["Low"].values
            df["close"] = df_raw["Close"].values
            df["volume"] = df_raw["Volume"].values if "Volume" in df_raw.columns else 0
            
            # Ã¥ÂÂµÃ¦Â¸Â¬Ã¤Â¸Â¦Ã¨ÂªÂ¿Ã¦â€¢Â´Ã¥Ë†â€ Ã¥â€°Â²Ã¯Â¼Ë†Ã¤Â¸ÂÃ¥ÂÂ«Ã©â€¦ÂÃ¦ÂÂ¯Ã¯Â¼â€°
            df = self._detect_and_adjust_splits(df, symbol)
            
            # Ã¥Å Â Ã¥â€¦Â¥Ã¨â€šÂ¡Ã§Â¥Â¨Ã¤Â»Â£Ã¨â„¢Å¸
            df["symbol"] = symbol.upper()
            
            return df
            
        except Exception as e:
            logger.error(f"Ã¥Ââ€“Ã¥Â¾â€”Ã¦Â­Â·Ã¥ÂÂ²Ã¨Â³â€¡Ã¦â€“â„¢Ã¥Â¤Â±Ã¦â€¢â€” {symbol}: {e}")
            return None
    
    def _detect_and_adjust_splits(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Ã¥ÂÂµÃ¦Â¸Â¬Ã¥Æ’Â¹Ã¦Â Â¼Ã¦â€“Â·Ã¥Â´â€“Ã¤Â¸Â¦Ã¨ÂªÂ¿Ã¦â€¢Â´Ã¦Â­Â·Ã¥ÂÂ²Ã¥Æ’Â¹Ã¦Â Â¼Ã¯Â¼Ë†Ã¥ÂÂªÃ¨â„¢â€¢Ã§Ââ€ Ã¥Ë†â€ Ã¥â€°Â²Ã¯Â¼Å’Ã¤Â¸ÂÃ¥ÂÂ«Ã©â€¦ÂÃ¦ÂÂ¯Ã¯Â¼â€°
        
        Ã§â€¢Â¶Ã¥ÂÂµÃ¦Â¸Â¬Ã¥Ë†Â°Ã¥Æ’Â¹Ã¦Â Â¼Ã§ÂªÂÃ§â€žÂ¶Ã¤Â¸â€¹Ã¨Â·Å’Ã¨Â¶â€¦Ã©ÂÅ½ 40%Ã¯Â¼Ë†Ã¥ÂÂ¯Ã¨Æ’Â½Ã¦ËœÂ¯Ã¥Ë†â€ Ã¥â€°Â²Ã¯Â¼â€°Ã¯Â¼Å’
        Ã¦Å“Æ’Ã¨â€¡ÂªÃ¥â€¹â€¢Ã¨ÂªÂ¿Ã¦â€¢Â´Ã¥Ë†â€ Ã¥â€°Â²Ã¥â€°ÂÃ§Å¡â€žÃ¥Æ’Â¹Ã¦Â Â¼Ã¯Â¼Å’Ã¤Â½Â¿Ã¦â€¢Â´Ã¥â‚¬â€¹Ã¥ÂºÂÃ¥Ë†â€”Ã©â‚¬Â£Ã§ÂºÅ’Ã£â‚¬â€š
        """
        if len(df) < 2:
            df['adj_close'] = df['close'].copy()
            return df
        
        df = df.copy()
        df = df.sort_values('date').reset_index(drop=True)
        
        # Ã¨Â¨Ë†Ã§Â®â€”Ã¦Â¯ÂÃ¦â€”Â¥Ã¦Â¼Â²Ã¨Â·Å’Ã¥Â¹â€¦
        df['pct_change'] = df['close'].pct_change()
        
        # Ã¥ÂÂµÃ¦Â¸Â¬Ã¥Ë†â€ Ã¥â€°Â²Ã©Â»Å¾Ã¯Â¼Ë†Ã¥Æ’Â¹Ã¦Â Â¼Ã¤Â¸â€¹Ã¨Â·Å’Ã¨Â¶â€¦Ã©ÂÅ½ 40%Ã¯Â¼â€°
        split_indices = []
        for i in range(1, len(df)):
            pct = df.loc[i, 'pct_change']
            if pd.notna(pct) and pct < -0.40:
                prev_close = float(df.loc[i-1, 'close'])
                curr_close = float(df.loc[i, 'close'])
                if curr_close > 0:
                    ratio = prev_close / curr_close
                    rounded_ratio = round(ratio)
                    # Ã¥ÂÂªÃ¦Å“â€°Ã¦Â¯â€Ã§Å½â€¡Ã¦Å½Â¥Ã¨Â¿â€˜Ã¦â€¢Â´Ã¦â€¢Â¸Ã¦â„¢â€šÃ¦â€°ÂÃ¨ÂªÂÃ§â€šÂºÃ¦ËœÂ¯Ã¥Ë†â€ Ã¥â€°Â²Ã¯Â¼Ë†2, 3, 4, 5, 10 Ã§Â­â€°Ã¯Â¼â€°
                    if rounded_ratio >= 2 and abs(ratio - rounded_ratio) < 0.3:
                        split_indices.append({
                            'index': i,
                            'date': df.loc[i, 'date'],
                            'ratio': rounded_ratio,
                            'prev_close': prev_close,
                            'curr_close': curr_close
                        })
                        logger.info(f"{symbol} Ã¥ÂÂµÃ¦Â¸Â¬Ã¥Ë†Â°Ã¥Ë†â€ Ã¥â€°Â²: {df.loc[i, 'date']}, Ã¦Â¯â€Ã§Å½â€¡ 1:{rounded_ratio}, Ã¥â€°ÂÃ¦â€Â¶ {prev_close:.2f} -> Ã§ÂÂ¾Ã¦â€Â¶ {curr_close:.2f}")
        
        # Ã¥Ë†ÂÃ¥Â§â€¹Ã¥Å’â€“Ã¨ÂªÂ¿Ã¦â€¢Â´Ã¥Â¾Å’Ã¥Æ’Â¹Ã¦Â Â¼
        df['adj_close'] = df['close'].astype(float)
        
        # Ã¥Â¾Å¾Ã¦Å“â‚¬Ã¨Â¿â€˜Ã§Å¡â€žÃ¥Ë†â€ Ã¥â€°Â²Ã©â€“â€¹Ã¥Â§â€¹Ã¥Â¾â‚¬Ã¥â€°ÂÃ¨ÂªÂ¿Ã¦â€¢Â´Ã¯Â¼Ë†Ã¤Â½Â¿Ã§â€Â¨Ã§Â´Â¯Ã§Â©ÂÃ¥â€ºÂ Ã¥Â­ÂÃ¯Â¼â€°
        if split_indices:
            cumulative_factor = 1.0
            
            for split in reversed(split_indices):
                idx = split['index']
                ratio = split['ratio']
                cumulative_factor *= ratio
                
                # Ã¨ÂªÂ¿Ã¦â€¢Â´Ã¥Ë†â€ Ã¥â€°Â²Ã©Â»Å¾Ã¤Â¹â€¹Ã¥â€°ÂÃ§Å¡â€žÃ¦â€°â‚¬Ã¦Å“â€°Ã¥Æ’Â¹Ã¦Â Â¼Ã¯Â¼Ë†Ã§â€Â¨Ã¥Å½Å¸Ã¥Â§â€¹ close Ã©â„¢Â¤Ã¤Â»Â¥Ã§Â´Â¯Ã§Â©ÂÃ¥â€ºÂ Ã¥Â­ÂÃ¯Â¼â€°
                df.loc[:idx-1, 'adj_close'] = df.loc[:idx-1, 'close'].astype(float) / cumulative_factor
            
            logger.info(f"{symbol} Ã¥Â·Â²Ã¨ÂªÂ¿Ã¦â€¢Â´ {len(split_indices)} Ã¦Â¬Â¡Ã¥Ë†â€ Ã¥â€°Â²Ã¯Â¼Å’Ã§Â¸Â½Ã¨ÂªÂ¿Ã¦â€¢Â´Ã¥â€ºÂ Ã¥Â­Â: {cumulative_factor}")
        
        # Ã§Â§Â»Ã©â„¢Â¤Ã¨â€¡Â¨Ã¦â„¢â€šÃ¦Â¬â€žÃ¤Â½Â
        df = df.drop(columns=['pct_change'], errors='ignore')
        
        return df
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Ã¥Ââ€“Ã¥Â¾â€”Ã¨â€šÂ¡Ã§Â¥Â¨Ã¥ÂÂ³Ã¦â„¢â€šÃ¯Â¼Ë†Ã¥Â»Â¶Ã©ÂÂ²Ã¯Â¼â€°Ã¥Â Â±Ã¥Æ’Â¹
        
        Args:
            symbol: Ã¨â€šÂ¡Ã§Â¥Â¨Ã¤Â»Â£Ã¨â„¢Å¸
            
        Returns:
            Ã¥Å’â€¦Ã¥ÂÂ«Ã§â€¢Â¶Ã¥â€°ÂÃ¥Æ’Â¹Ã¦Â Â¼Ã¥â€™Å’Ã¦Â¼Â²Ã¨Â·Å’Ã¨Â³â€¡Ã¨Â¨Å Ã§Å¡â€žÃ¥Â­â€”Ã¥â€¦Â¸
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            # Ã¥Ëœâ€”Ã¨Â©Â¦Ã¥Ââ€“Ã¥Â¾â€”Ã¥ÂÂ³Ã¦â„¢â€šÃ¥Æ’Â¹Ã¦Â Â¼
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
            
            if not current_price:
                # Ã¥Â¾Å¾Ã¦Â­Â·Ã¥ÂÂ²Ã¨Â³â€¡Ã¦â€“â„¢Ã¥Ââ€“Ã¥Â¾â€”Ã¦Å“â‚¬Ã¦â€“Â°Ã¦â€Â¶Ã§â€ºÂ¤Ã¥Æ’Â¹Ã¯Â¼Ë†Ã¤Â½Â¿Ã§â€Â¨Ã¥Å½Å¸Ã¥Â§â€¹Ã¥Æ’Â¹Ã¦Â Â¼Ã¯Â¼â€°
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
            logger.error(f"Ã¥Ââ€“Ã¥Â¾â€”Ã¥ÂÂ³Ã¦â„¢â€šÃ¥Â Â±Ã¥Æ’Â¹Ã¥Â¤Â±Ã¦â€¢â€” {symbol}: {e}")
            return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        å¿«é€Ÿé©—è­‰è‚¡ç¥¨ä»£è™Ÿæ˜¯å¦æœ‰æ•ˆ
        
        ä½¿ç”¨ history API è€Œéž infoï¼Œé€Ÿåº¦å¿« 5-10 å€
        
        Args:
            symbol: è‚¡ç¥¨ä»£è™Ÿ
            
        Returns:
            æ˜¯å¦ç‚ºæœ‰æ•ˆä»£è™Ÿ
        """
        try:
            ticker = yf.Ticker(symbol)
            # åªæŠ“ 1 å¤©è³‡æ–™ï¼Œæ¯” info å¿«å¾ˆå¤š
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
        Ã¥Ââ€“Ã¥Â¾â€”Ã¨â€šÂ¡Ã§Â¥Â¨Ã©â€¦ÂÃ¦ÂÂ¯Ã¦Â­Â·Ã¥ÂÂ²
        
        Args:
            symbol: Ã¨â€šÂ¡Ã§Â¥Â¨Ã¤Â»Â£Ã¨â„¢Å¸
            period: Ã¨Â³â€¡Ã¦â€“â„¢Ã¦Å“Å¸Ã©â€“â€œ (1y, 5y, 10y, max)
            
        Returns:
            Ã¥Å’â€¦Ã¥ÂÂ«Ã©â€¦ÂÃ¦ÂÂ¯Ã¨Â¨ËœÃ©Å’â€žÃ§Å¡â€ž DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends
            
            if dividends.empty:
                logger.info(f"{symbol} Ã§â€žÂ¡Ã©â€¦ÂÃ¦ÂÂ¯Ã¨Â¨ËœÃ©Å’â€ž")
                return None
            
            # Ã¨Â½â€°Ã¦Ââ€ºÃ¦Ë†Â DataFrame
            df = dividends.reset_index()
            df.columns = ["date", "amount"]
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["symbol"] = symbol.upper()
            
            # Ã¦Â Â¹Ã¦â€œÅ¡ period Ã©ÂÅ½Ã¦Â¿Â¾
            if period != "max":
                years = int(period.replace("y", ""))
                cutoff_date = datetime.now().date() - timedelta(days=years * 365)
                df = df[df["date"] >= cutoff_date]
            
            return df
            
        except Exception as e:
            logger.error(f"Ã¥Ââ€“Ã¥Â¾â€”Ã©â€¦ÂÃ¦ÂÂ¯Ã¨Â³â€¡Ã¦â€“â„¢Ã¥Â¤Â±Ã¦â€¢â€” {symbol}: {e}")
            return None
    
    def get_index_data(
        self,
        symbol: str,
        period: str = "10y",
    ) -> Optional[pd.DataFrame]:
        """
        Ã¥Ââ€“Ã¥Â¾â€”Ã¥Â¸â€šÃ¥Â Â´Ã¦Å’â€¡Ã¦â€¢Â¸Ã¦Â­Â·Ã¥ÂÂ²Ã¨Â³â€¡Ã¦â€“â„¢
        
        Args:
            symbol: Ã¦Å’â€¡Ã¦â€¢Â¸Ã¤Â»Â£Ã¨â„¢Å¸ (^GSPC, ^DJI, ^IXIC)
            period: Ã¨Â³â€¡Ã¦â€“â„¢Ã¦Å“Å¸Ã©â€“â€œ
            
        Returns:
            Ã¥Å’â€¦Ã¥ÂÂ« OHLCV Ã§Å¡â€ž DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, auto_adjust=False)
            
            if df.empty:
                logger.warning(f"Ã§â€žÂ¡Ã¦Å’â€¡Ã¦â€¢Â¸Ã¨Â³â€¡Ã¦â€“â„¢: {symbol}")
                return None
            
            # Ã©â€¡ÂÃ¨Â¨Â­Ã§Â´Â¢Ã¥Â¼â€¢
            df = df.reset_index()
            
            # Ã¦Â¨â„¢Ã¦Âºâ€“Ã¥Å’â€“Ã¦Â¬â€žÃ¤Â½ÂÃ¥ÂÂÃ§Â¨Â±
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
            
            # Ã§Â¢ÂºÃ¤Â¿ÂÃ¦â€”Â¥Ã¦Å“Å¸Ã¦ËœÂ¯ date Ã©Â¡Å¾Ã¥Å¾â€¹
            df["date"] = pd.to_datetime(df["date"]).dt.date
            
            # Ã¨Â¨Ë†Ã§Â®â€”Ã¦Â¼Â²Ã¨Â·Å’
            df["change"] = df["close"].diff()
            df["change_pct"] = df["close"].pct_change() * 100
            
            # Ã¥Å Â Ã¥â€¦Â¥Ã¤Â»Â£Ã¨â„¢Å¸
            df["symbol"] = symbol
            
            # Ã¥ÂÂªÃ¤Â¿ÂÃ§â€¢â„¢Ã©Å“â‚¬Ã¨Â¦ÂÃ§Å¡â€žÃ¦Â¬â€žÃ¤Â½Â
            keep_columns = ["symbol", "date", "open", "high", "low", "close", "volume", "change", "change_pct"]
            df = df[[c for c in keep_columns if c in df.columns]]
            
            return df
            
        except Exception as e:
            logger.error(f"Ã¥Ââ€“Ã¥Â¾â€”Ã¦Å’â€¡Ã¦â€¢Â¸Ã¨Â³â€¡Ã¦â€“â„¢Ã¥Â¤Â±Ã¦â€¢â€” {symbol}: {e}")
            return None
    
    def get_all_indices(self, period: str = "10y") -> Dict[str, pd.DataFrame]:
        """
        Ã¥Ââ€“Ã¥Â¾â€”Ã¦â€°â‚¬Ã¦Å“â€°Ã¤Â¸â€°Ã¥Â¤Â§Ã¦Å’â€¡Ã¦â€¢Â¸Ã¨Â³â€¡Ã¦â€“â„¢
        
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
        Ã¥Ââ€“Ã¥Â¾â€”Ã¨â€šÂ¡Ã§Â¥Â¨Ã¥Â»Â¶Ã¤Â¼Â¸Ã¦Â­Â·Ã¥ÂÂ²Ã¨Â³â€¡Ã¦â€“â„¢Ã¯Â¼Ë†Ã¦â€Â¯Ã¦ÂÂ´Ã¦â€ºÂ´Ã©â€¢Â·Ã¦â„¢â€šÃ©â€“â€œÃ¯Â¼â€°
        
        Args:
            symbol: Ã¨â€šÂ¡Ã§Â¥Â¨Ã¤Â»Â£Ã¨â„¢Å¸
            years: Ã¥Â¹Â´Ã¦â€¢Â¸ (1, 3, 5, 10)
            
        Returns:
            Ã¥Å’â€¦Ã¥ÂÂ« OHLCV Ã§Å¡â€ž DataFrame
        """
        period_map = {
            1: "1y",
            2: "2y",
            3: "3y",  # yfinance Ã¤Â¸ÂÃ¦â€Â¯Ã¦ÂÂ´ 3yÃ¯Â¼Å’Ã§â€Â¨ 5y Ã¤Â»Â£Ã¦â€ºÂ¿
            5: "5y",
            10: "10y",
        }
        
        period = period_map.get(years, "10y")
        if years == 3:
            period = "5y"  # Ã§â€žÂ¶Ã¥Â¾Å’Ã¥Å“Â¨Ã§Â¨â€¹Ã¥Â¼ÂÃ¤Â¸Â­Ã©ÂÅ½Ã¦Â¿Â¾
        
        df = self.get_stock_history(symbol, period=period)
        
        if df is None:
            return None
        
        # Ã¥Â¦â€šÃ¦Å¾Å“Ã¦ËœÂ¯ 3 Ã¥Â¹Â´Ã¯Â¼Å’Ã©Å“â‚¬Ã¨Â¦ÂÃ©ÂÅ½Ã¦Â¿Â¾
        if years == 3:
            cutoff_date = datetime.now().date() - timedelta(days=3 * 365)
            df = df[df["date"] >= cutoff_date]
        
        return df


# Ã¥Â»ÂºÃ§Â«â€¹Ã¥â€¦Â¨Ã¥Å¸Å¸Ã¥Â®Â¢Ã¦Ë†Â¶Ã§Â«Â¯Ã¥Â¯Â¦Ã¤Â¾â€¹
yahoo_finance = YahooFinanceClient()
