"""
Yahoo Finance 資料來源
使用 yfinance 套件抓取美股資料
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# 常用台股中文名稱對照表
TAIWAN_STOCK_NAMES = {
    # 權值股
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
    # 金融股
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
    # 電子股
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
    "2049": "上銀",
    "3045": "台灣大",
    "4904": "遠傳",
    "3231": "緯創",
    "2356": "英業達",
    "2324": "仁寶",
    "2353": "宏碁",
    "2377": "微星",
    "2376": "技嘉",
    "2388": "威盛",
    "2409": "友達",
    "3481": "群創",
    "2404": "漢唐",
    # 傳產股
    "5871": "中租-KY",
    "1216": "統一",
    "2207": "和泰車",
    "2105": "正新",
    "9910": "豐泰",
    "2603": "長榮",
    "2609": "陽明",
    "2615": "萬海",
    "2618": "長榮航",
    "2610": "華航",
    "1402": "遠東新",
    "1590": "亞德客-KY",
    "4938": "和碩",
    "2014": "中鴻",
    "2006": "東和鋼鐵",
    "2015": "豐興",
    # AI 概念股
    "3443": "創意",
    "5274": "信驊",
    "6669": "緯穎",
    "3661": "世芯-KY",
    "6415": "矽力-KY",
    "3533": "嘉澤",
    "2368": "金像電",
    "6176": "瑞儀",
    "3037": "欣興",
    "5347": "世界",
    "8046": "南電",
    "6239": "力成",
    # 其他熱門股
    "2498": "宏達電",
    "3706": "神達",
    "2354": "鴻準",
    "2360": "致茂",
    "2393": "億光",
    "2383": "台光電",
    "3036": "文曄",
    "6446": "藥華藥",
    "4743": "合一",
    "6547": "高端疫苗",
    "2344": "華邦電",
    "2449": "京元電子",
    "6531": "愛普",
    "3017": "奇鋐",
    "2059": "川湖",
    "2385": "群光",
    "6770": "力積電",
    "8299": "群聯",
    "6285": "啟碁",
    "2347": "聯強",
    "2458": "義隆",
    "3023": "信邦",
    "2492": "華新科",
    "3044": "健鼎",
    "5483": "中美晶",
    "6488": "環球晶",
    "3529": "力旺",
    "2542": "興富發",
    "2545": "皇翔",
    "2504": "國產",
    "2520": "冠德",
    "2534": "宏盛",
    "9921": "巨大",
    "9914": "美利達",
    "1227": "佳格",
    "1229": "聯華",
    "1234": "黑松",
    "2912": "統一超",
    "2915": "潤泰全",
    "9904": "寶成",
    "9945": "潤泰新",
}


class YahooFinanceClient:
    """Yahoo Finance 資料擷取客戶端"""
    
    def __init__(self):
        pass
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        取得股票基本資訊
        
        Args:
            symbol: 股票代號 (如 AAPL, TSLA, 2330.TW)
            
        Returns:
            股票資訊字典，包含名稱、市值等
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or "symbol" not in info:
                logger.warning(f"無法取得股票資訊: {symbol}")
                return None
            
            # 取得名稱：優先使用 longName，然後 shortName
            name = info.get("longName") or info.get("shortName", "N/A")
            
            # 對於台股，優先使用本地映射表的中文名稱
            if symbol.endswith(".TW") or symbol.endswith(".TWO"):
                # 提取股票代號 (去掉 .TW 或 .TWO)
                stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                # 優先使用本地映射表
                if stock_code in TAIWAN_STOCK_NAMES:
                    name = TAIWAN_STOCK_NAMES[stock_code]
                else:
                    # 嘗試從 Yahoo Finance 取得中文名
                    display_name = info.get("displayName")
                    if display_name:
                        name = display_name
            
            return {
                "symbol": info.get("symbol", symbol),
                "name": name,
                "shortName": info.get("shortName", ""),
                "longName": info.get("longName", ""),
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            }
        except Exception as e:
            logger.error(f"取得股票資訊失敗 {symbol}: {e}")
            return None
    
    def get_stock_history(
        self,
        symbol: str,
        period: str = "1y",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Optional[pd.DataFrame]:
        """
        取得股票歷史價格資料
        
        Args:
            symbol: 股票代號
            period: 資料期間 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: 開始日期（與 end 搭配使用時，period 會被忽略）
            end: 結束日期
            
        Returns:
            包含 OHLCV 的 DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            
            if start and end:
                df = ticker.history(start=start, end=end)
            else:
                df = ticker.history(period=period)
            
            if df.empty:
                logger.warning(f"無歷史資料: {symbol}")
                return None
            
            # 重設索引，將日期變成欄位
            df = df.reset_index()
            
            # 標準化欄位名稱
            column_mapping = {
                "Date": "date",
                "Datetime": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
            
            # 只重命名存在的欄位
            existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=existing_columns)
            
            # 確保必要欄位存在
            required_columns = ["date", "open", "high", "low", "close"]
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"缺少必要欄位: {col}")
                    return None
            
            # volume 可選，如果沒有就填 0
            if "volume" not in df.columns:
                df["volume"] = 0
                logger.warning(f"{symbol} 沒有 volume 資料，已填入 0")
            
            # 只保留需要的欄位
            keep_columns = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in df.columns]
            df = df[keep_columns]
            
            # 確保日期是 date 類型
            df["date"] = pd.to_datetime(df["date"]).dt.date
            
            # 加入股票代號
            df["symbol"] = symbol.upper()
            
            return df
            
        except Exception as e:
            logger.error(f"取得歷史資料失敗 {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        取得股票即時（延遲）報價
        
        Args:
            symbol: 股票代號
            
        Returns:
            包含當前價格和漲跌資訊的字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            # 嘗試取得即時價格
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
            
            if not current_price:
                # 從歷史資料取得最新收盤價
                hist = ticker.history(period="5d")
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
            logger.error(f"取得即時報價失敗 {symbol}: {e}")
            return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        驗證股票代號是否有效
        
        Args:
            symbol: 股票代號
            
        Returns:
            是否為有效代號
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info is not None and "symbol" in info
        except Exception:
            return False


# 建立全域客戶端實例
yahoo_finance = YahooFinanceClient()
