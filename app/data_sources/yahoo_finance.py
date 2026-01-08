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
    # 上櫃股票 (.TWO)
    "8069": "元太",
    "6547": "高端疫苗",
    "4743": "合一",
    "6446": "藥華藥",
    "5765": "永信醫藥",
    "8086": "宏捷科",
    "3105": "穩懋",
    "5269": "祥碩",
    "6409": "旭隼",
    "6510": "精測",
    "3293": "鑫喬",
    "6533": "晶心科",
    "6477": "安集",
    "6568": "宏觀",
    "3163": "波若威",
    "6197": "佳必琪",
    "5388": "中磊",
    "6781": "AES-KY",
    "3152": "璟德",
    "5289": "宜鼎",
    "6223": "旺矽",
    "8150": "南茂",
    "5484": "慧友",
    "6442": "光聖",
    "6472": "保瑞",
    "4966": "譜瑞-KY",
    "6789": "采鈺",
    "6640": "均華",
    "3260": "威剛",
    "4763": "材料-KY",
    "5299": "杰力",
    "8016": "矽創",
    "6719": "力智",
    "6456": "GIS-KY",
    "6451": "訊芯-KY",
    "3707": "漢磊",
    "4968": "立積",
    "6679": "鈺太",
    "6592": "和潤企業",
    "6591": "動力-KY",
    "5425": "台半",
    "6803": "崇越電",
    "3527": "聚積",
    "6449": "鈺邦",
    # ETF
    "0050": "元大台灣50",
    "0056": "元大高股息",
    "00878": "國泰永續高股息",
    "00919": "群益台灣精選高息",
    "00929": "復華台灣科技優息",
    "006208": "富邦台50",
    "00713": "元大台灣高息低波",
    "00692": "富邦公司治理",
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
            info = ticker.info or {}
            
            # 取得名稱：優先使用 longName，然後 shortName
            name = info.get("longName") or info.get("shortName") or symbol
            
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
            
            # 即使 info 不完整，也返回基本資訊
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
            logger.error(f"取得股票資訊失敗 {symbol}: {e}")
            # 即使出錯，對於台股也嘗試返回本地名稱
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
        取得股票歷史價格資料
        
        Args:
            symbol: 股票代號
            period: 資料期間 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            start: 開始日期（與 end 搭配使用時，period 會被忽略）
            end: 結束日期
            
        Returns:
            包含 OHLCV 的 DataFrame，其中：
            - close: 原始收盤價（用於顯示）
            - adj_close: 分割調整後價格（用於圖表，不含配息）
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # 取得原始價格
            if start and end:
                df_raw = ticker.history(start=start, end=end, auto_adjust=False)
            else:
                df_raw = ticker.history(period=period, auto_adjust=False)
            
            if df_raw.empty:
                logger.warning(f"無歷史資料: {symbol}")
                return None
            
            df_raw = df_raw.reset_index()
            
            # 標準化日期欄位
            date_col = "Date" if "Date" in df_raw.columns else "Datetime"
            
            # 建立結果 DataFrame
            df = pd.DataFrame()
            df["date"] = pd.to_datetime(df_raw[date_col]).dt.date
            df["open"] = df_raw["Open"].values
            df["high"] = df_raw["High"].values
            df["low"] = df_raw["Low"].values
            df["close"] = df_raw["Close"].values
            df["volume"] = df_raw["Volume"].values if "Volume" in df_raw.columns else 0
            
            # 偵測並調整分割（不含配息）
            df = self._detect_and_adjust_splits(df, symbol)
            
            # 加入股票代號
            df["symbol"] = symbol.upper()
            
            return df
            
        except Exception as e:
            logger.error(f"取得歷史資料失敗 {symbol}: {e}")
            return None
    
    def _detect_and_adjust_splits(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        偵測價格斷崖並調整歷史價格（只處理分割，不含配息）
        
        當偵測到價格突然下跌超過 40%（可能是分割），
        會自動調整分割前的價格，使整個序列連續。
        """
        if len(df) < 2:
            df['adj_close'] = df['close'].copy()
            return df
        
        df = df.copy()
        df = df.sort_values('date').reset_index(drop=True)
        
        # 計算每日漲跌幅
        df['pct_change'] = df['close'].pct_change()
        
        # 偵測分割點（價格下跌超過 40%）
        split_indices = []
        for i in range(1, len(df)):
            pct = df.loc[i, 'pct_change']
            if pd.notna(pct) and pct < -0.40:
                prev_close = float(df.loc[i-1, 'close'])
                curr_close = float(df.loc[i, 'close'])
                if curr_close > 0:
                    ratio = prev_close / curr_close
                    rounded_ratio = round(ratio)
                    # 只有比率接近整數時才認為是分割（2, 3, 4, 5, 10 等）
                    if rounded_ratio >= 2 and abs(ratio - rounded_ratio) < 0.3:
                        split_indices.append({
                            'index': i,
                            'date': df.loc[i, 'date'],
                            'ratio': rounded_ratio,
                            'prev_close': prev_close,
                            'curr_close': curr_close
                        })
                        logger.info(f"{symbol} 偵測到分割: {df.loc[i, 'date']}, 比率 1:{rounded_ratio}, 前收 {prev_close:.2f} -> 現收 {curr_close:.2f}")
        
        # 初始化調整後價格
        df['adj_close'] = df['close'].astype(float)
        
        # 從最近的分割開始往前調整（使用累積因子）
        if split_indices:
            cumulative_factor = 1.0
            
            for split in reversed(split_indices):
                idx = split['index']
                ratio = split['ratio']
                cumulative_factor *= ratio
                
                # 調整分割點之前的所有價格（用原始 close 除以累積因子）
                df.loc[:idx-1, 'adj_close'] = df.loc[:idx-1, 'close'].astype(float) / cumulative_factor
            
            logger.info(f"{symbol} 已調整 {len(split_indices)} 次分割，總調整因子: {cumulative_factor}")
        
        # 移除臨時欄位
        df = df.drop(columns=['pct_change'], errors='ignore')
        
        return df
    
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
                # 從歷史資料取得最新收盤價（使用原始價格）
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
    
    def get_dividends(
        self,
        symbol: str,
        period: str = "10y",
    ) -> Optional[pd.DataFrame]:
        """
        取得股票配息歷史
        
        Args:
            symbol: 股票代號
            period: 資料期間 (1y, 5y, 10y, max)
            
        Returns:
            包含配息記錄的 DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends
            
            if dividends.empty:
                logger.info(f"{symbol} 無配息記錄")
                return None
            
            # 轉換成 DataFrame
            df = dividends.reset_index()
            df.columns = ["date", "amount"]
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["symbol"] = symbol.upper()
            
            # 根據 period 過濾
            if period != "max":
                years = int(period.replace("y", ""))
                cutoff_date = datetime.now().date() - timedelta(days=years * 365)
                df = df[df["date"] >= cutoff_date]
            
            return df
            
        except Exception as e:
            logger.error(f"取得配息資料失敗 {symbol}: {e}")
            return None
    
    def get_index_data(
        self,
        symbol: str,
        period: str = "10y",
    ) -> Optional[pd.DataFrame]:
        """
        取得市場指數歷史資料
        
        Args:
            symbol: 指數代號 (^GSPC, ^DJI, ^IXIC)
            period: 資料期間
            
        Returns:
            包含 OHLCV 的 DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, auto_adjust=False)
            
            if df.empty:
                logger.warning(f"無指數資料: {symbol}")
                return None
            
            # 重設索引
            df = df.reset_index()
            
            # 標準化欄位名稱
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
            
            # 確保日期是 date 類型
            df["date"] = pd.to_datetime(df["date"]).dt.date
            
            # 計算漲跌
            df["change"] = df["close"].diff()
            df["change_pct"] = df["close"].pct_change() * 100
            
            # 加入代號
            df["symbol"] = symbol
            
            # 只保留需要的欄位
            keep_columns = ["symbol", "date", "open", "high", "low", "close", "volume", "change", "change_pct"]
            df = df[[c for c in keep_columns if c in df.columns]]
            
            return df
            
        except Exception as e:
            logger.error(f"取得指數資料失敗 {symbol}: {e}")
            return None
    
    def get_all_indices(self, period: str = "10y") -> Dict[str, pd.DataFrame]:
        """
        取得所有三大指數資料
        
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
        取得股票延伸歷史資料（支援更長時間）
        
        Args:
            symbol: 股票代號
            years: 年數 (1, 3, 5, 10)
            
        Returns:
            包含 OHLCV 的 DataFrame
        """
        period_map = {
            1: "1y",
            2: "2y",
            3: "3y",  # yfinance 不支援 3y，用 5y 代替
            5: "5y",
            10: "10y",
        }
        
        period = period_map.get(years, "10y")
        if years == 3:
            period = "5y"  # 然後在程式中過濾
        
        df = self.get_stock_history(symbol, period=period)
        
        if df is None:
            return None
        
        # 如果是 3 年，需要過濾
        if years == 3:
            cutoff_date = datetime.now().date() - timedelta(days=3 * 365)
            df = df[df["date"] >= cutoff_date]
        
        return df


# 建立全域客戶端實例
yahoo_finance = YahooFinanceClient()
