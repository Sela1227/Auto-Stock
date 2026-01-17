"""
價格快取服務

🚀 效能優化版 - 2026-01-17
- 非開盤時間直接使用快取（不再呼叫 API）
- 優先返回舊資料，標記是否需要更新
- 智慧快取判斷：根據市場狀態決定快取有效期

排程邏輯：
- 台股開盤 (09:00-13:30)：每 10 分鐘更新台股
- 美股開盤 (21:30-05:00)：每 10 分鐘更新美股
- 收盤後：不更新（使用收盤價）
- 加密貨幣：24 小時每 10 分鐘更新
"""
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
import yfinance as yf

from app.models.price_cache import StockPriceCache
from app.models.watchlist import Watchlist

logger = logging.getLogger(__name__)


# 台股名稱對照（常見的）
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



# ============================================================
# 開盤時間判斷（台灣時間）
# ============================================================

def is_tw_market_open() -> bool:
    """判斷台股是否開盤（週一到週五 09:00-13:30）"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return time(9, 0) <= now.time() <= time(13, 30)


def is_us_market_open() -> bool:
    """判斷美股是否開盤（台灣時間 21:30-05:00）"""
    now = datetime.now()
    weekday = now.weekday()
    current_time = now.time()
    
    # 晚上 21:30 後（週一到週五）
    if weekday < 5 and current_time >= time(21, 30):
        return True
    # 凌晨 05:00 前（週二到週六）
    if weekday > 0 and current_time <= time(5, 0):
        return True
    # 週六凌晨
    if weekday == 5 and current_time <= time(5, 0):
        return True
    return False


def get_market_status() -> Dict[str, bool]:
    """取得各市場開盤狀態"""
    return {
        "tw_open": is_tw_market_open(),
        "us_open": is_us_market_open(),
        "crypto_open": True,
    }


def get_symbol_market(symbol: str) -> str:
    """
    判斷 symbol 屬於哪個市場
    
    Returns:
        "tw" | "us" | "crypto"
    """
    symbol = symbol.upper()
    
    # 加密貨幣
    if symbol in ("BTC", "ETH", "BITCOIN", "ETHEREUM") or symbol.endswith("-USD"):
        return "crypto"
    
    # 台股
    if symbol.endswith((".TW", ".TWO")):
        return "tw"
    
    # 預設美股
    return "us"


def is_market_open_for_symbol(symbol: str) -> bool:
    """判斷該 symbol 的市場是否開盤"""
    market = get_symbol_market(symbol)
    
    if market == "crypto":
        return False  # 🆕 加密貨幣改為定時更新（3小時），不需即時查詢
    elif market == "tw":
        return is_tw_market_open()
    else:
        return is_us_market_open()


# ============================================================
# 價格快取服務
# ============================================================

class PriceCacheService:
    """價格快取服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tracked_symbols(self) -> Dict[str, List[str]]:
        """取得所有被追蹤的 symbol（去重，按市場分類）"""
        stmt = select(distinct(Watchlist.symbol))
        result = self.db.execute(stmt)
        symbols = [row[0] for row in result.all()]
        
        tw_stocks = []
        us_stocks = []
        crypto = []
        
        for symbol in symbols:
            if symbol.upper() in ("BTC", "ETH"):
                crypto.append(symbol)
            elif symbol.endswith((".TW", ".TWO")):
                tw_stocks.append(symbol)
            else:
                us_stocks.append(symbol)
        
        logger.info(f"追蹤: 台股 {len(tw_stocks)}, 美股 {len(us_stocks)}, 加密貨幣 {len(crypto)}")
        return {"tw_stocks": tw_stocks, "us_stocks": us_stocks, "crypto": crypto}
    
    def batch_update_stock_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """批次更新股票價格（含 MA20）"""
        if not symbols:
            return {"updated": 0, "failed": []}
        
        result = {"updated": 0, "failed": []}
        logger.info(f"開始更新 {len(symbols)} 支股票...")
        
        try:
            # 使用 yfinance 批次取得
            tickers = yf.Tickers(" ".join(symbols))
            
            for symbol in symbols:
                try:
                    ticker = tickers.tickers.get(symbol)
                    if not ticker:
                        result["failed"].append(symbol)
                        continue
                    
                    # 🆕 取得歷史數據（用於計算 MA20）
                    hist = ticker.history(period="1mo")
                    
                    if hist.empty:
                        # 嘗試用 info
                        info = ticker.info
                        if not info:
                            result["failed"].append(symbol)
                            continue
                        
                        price = info.get("regularMarketPrice") or info.get("currentPrice")
                        prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
                        volume = info.get("regularMarketVolume") or info.get("volume")
                        name = info.get("shortName") or info.get("longName") or ""
                        ma20 = None
                    else:
                        # 從歷史數據取得
                        price = float(hist['Close'].iloc[-1])
                        prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else None
                        volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else None
                        
                        # 🆕 計算 MA20
                        ma20 = None
                        if len(hist) >= 20:
                            ma20 = float(hist['Close'].tail(20).mean())
                        
                        # 取得名稱
                        info = ticker.info
                        name = ""
                        if info:
                            name = info.get("shortName") or info.get("longName") or ""
                    
                    if price is None:
                        result["failed"].append(symbol)
                        continue
                    
                    # 台股名稱
                    if not name and symbol.endswith((".TW", ".TWO")):
                        stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                        name = TAIWAN_STOCK_NAMES.get(stock_code, "")
                    
                    # 計算漲跌
                    change = None
                    change_pct = None
                    if prev_close and prev_close > 0:
                        change = price - prev_close
                        change_pct = (change / prev_close) * 100
                    
                    # 更新快取（含 MA20）
                    self._upsert_cache(
                        symbol=symbol,
                        name=name,
                        price=price,
                        prev_close=prev_close,
                        change=change,
                        change_pct=change_pct,
                        volume=volume,
                        asset_type="stock",
                        ma20=ma20,
                    )
                    result["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"更新 {symbol} 失敗: {e}")
                    result["failed"].append(symbol)
            
            self.db.commit()
            logger.info(f"股票更新完成: 成功 {result['updated']}, 失敗 {len(result['failed'])}")
            
        except Exception as e:
            logger.error(f"批次更新失敗: {e}")
        
        return result
    
    def batch_update_crypto_prices(self, symbols: List[str], force: bool = False) -> Dict[str, Any]:
        """批次更新加密貨幣價格（🆕 3小時快取）"""
        if not symbols:
            return {"updated": 0, "failed": [], "skipped": 0}
        
        # 🆕 檢查快取時間（3小時 = 180分鐘）
        CRYPTO_CACHE_MINUTES = 180
        
        if not force:
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(minutes=CRYPTO_CACHE_MINUTES)
            
            # 檢查是否有任何需要更新的
            needs_update = []
            for symbol in symbols:
                cache = self.db.query(StockPriceCache).filter(
                    StockPriceCache.symbol == symbol
                ).first()
                if not cache or cache.updated_at < cutoff:
                    needs_update.append(symbol)
            
            if not needs_update:
                logger.info(f"💤 加密貨幣快取未過期（{CRYPTO_CACHE_MINUTES}分鐘內），跳過 {len(symbols)} 個")
                return {"updated": 0, "failed": [], "skipped": len(symbols)}
            
            symbols = needs_update
            logger.info(f"🔄 加密貨幣需更新: {len(symbols)} 個")
        
        result = {"updated": 0, "failed": []}
        
        try:
            from app.data_sources.coingecko import coingecko
            
            for symbol in symbols:
                try:
                    data = coingecko.get_price(symbol)
                    if not data or data.get("price") is None:
                        result["failed"].append(symbol)
                        continue
                    
                    self._upsert_cache(
                        symbol=symbol,
                        name=data.get("name", symbol),
                        price=data["price"],
                        prev_close=None,
                        change=None,
                        change_pct=data.get("change_24h"),
                        volume=data.get("volume_24h"),
                        asset_type="crypto",
                        ma20=None,  # 加密貨幣不計算 MA20
                    )
                    result["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"更新 {symbol} 失敗: {e}")
                    result["failed"].append(symbol)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"加密貨幣更新失敗: {e}")
        
        return result
    
    def _upsert_cache(self, symbol, name, price, prev_close, change, change_pct, volume, asset_type, ma20=None):
        """更新或新增快取（含 MA20）"""
        cache = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol
        ).first()
        
        if cache:
            cache.name = name or cache.name
            cache.price = price
            cache.prev_close = prev_close
            cache.change = change
            cache.change_pct = change_pct
            cache.volume = volume
            if ma20 is not None:
                cache.ma20 = ma20
            cache.updated_at = datetime.now()
        else:
            cache = StockPriceCache(
                symbol=symbol,
                name=name,
                price=price,
                prev_close=prev_close,
                change=change,
                change_pct=change_pct,
                ma20=ma20,
                volume=volume,
                asset_type=asset_type,
            )
            self.db.add(cache)
    
    # ============================================================
    # 🆕 智慧快取查詢（效能優化核心）
    # ============================================================
    
    def get_cached_price(self, symbol: str, max_age_minutes: int = 5) -> Optional[dict]:
        """
        從快取取得股票價格（舊版本，保持相容性）
        
        Args:
            symbol: 股票代號
            max_age_minutes: 快取有效期（分鐘），預設 5 分鐘
            
        Returns:
            快取資料 dict 或 None（無快取或已過期）
        """
        cache = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol.upper()
        ).first()
        
        if not cache:
            logger.debug(f"快取未命中: {symbol}")
            return None
        
        # 檢查是否過期
        if cache.updated_at:
            age = datetime.now() - cache.updated_at
            if age > timedelta(minutes=max_age_minutes):
                logger.info(f"快取過期: {symbol} (已 {age.total_seconds()/60:.1f} 分鐘)")
                return None
        
        logger.info(f"📦 快取命中: {symbol}")
        return self._cache_to_dict(cache)
    
    def get_cached_price_smart(self, symbol: str) -> Tuple[Optional[dict], bool]:
        """
        🆕 智慧取得快取價格（效能優化版）
        
        邏輯：
        1. 無資料 → (None, True) 需要從 API 取得
        2. 有資料 + 非開盤 → (資料, False) 直接用，不需更新
        3. 有資料 + 開盤中 + < 5分鐘 → (資料, False) 直接用
        4. 有資料 + 開盤中 + > 5分鐘 → (資料, True) 返回舊資料，標記需要更新
        
        Args:
            symbol: 股票代號
            
        Returns:
            (快取資料 dict 或 None, 是否需要更新)
        """
        symbol = symbol.upper()
        
        cache = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol == symbol
        ).first()
        
        # 情況 1: 無資料
        if not cache:
            logger.debug(f"⚡ 快取未命中: {symbol}")
            return None, True
        
        cache_data = self._cache_to_dict(cache)
        
        # 判斷市場是否開盤
        market_open = is_market_open_for_symbol(symbol)
        
        # 情況 2: 非開盤時間 → 直接使用快取
        if not market_open:
            logger.info(f"⚡ 非開盤時間，直接使用快取: {symbol}")
            return cache_data, False
        
        # 開盤時間，檢查快取年齡
        if cache.updated_at:
            age = datetime.now() - cache.updated_at
            age_minutes = age.total_seconds() / 60
            
            # 情況 3: 開盤中 + 快取 < 5 分鐘
            if age_minutes < 5:
                logger.info(f"⚡ 快取有效 ({age_minutes:.1f}分鐘): {symbol}")
                return cache_data, False
            
            # 情況 4: 開盤中 + 快取過期
            logger.info(f"⚡ 快取過期但先返回 ({age_minutes:.1f}分鐘): {symbol}")
            return cache_data, True
        
        # 無更新時間記錄，標記需要更新
        return cache_data, True
    
    def get_cached_prices_batch(self, symbols: List[str]) -> Dict[str, dict]:
        """
        🆕 批量取得快取價格
        
        Args:
            symbols: 股票代號列表
            
        Returns:
            {symbol: cache_data} 字典
        """
        if not symbols:
            return {}
        
        # 批量查詢
        caches = self.db.query(StockPriceCache).filter(
            StockPriceCache.symbol.in_([s.upper() for s in symbols])
        ).all()
        
        return {
            cache.symbol: self._cache_to_dict(cache)
            for cache in caches
        }
    
    def _cache_to_dict(self, cache: StockPriceCache) -> dict:
        """將快取物件轉換為 dict"""
        return {
            "symbol": cache.symbol,
            "name": cache.name,
            "price": float(cache.price) if cache.price else None,
            "prev_close": float(cache.prev_close) if cache.prev_close else None,
            "change": float(cache.change) if cache.change else None,
            "change_pct": float(cache.change_pct) if cache.change_pct else None,
            "volume": int(cache.volume) if cache.volume else None,
            "ma20": float(cache.ma20) if cache.ma20 else None,
            "updated_at": cache.updated_at.isoformat() if cache.updated_at else None,
            "asset_type": cache.asset_type,
        }
    
    def update_all(self, force: bool = False) -> Dict[str, Any]:
        """
        更新所有追蹤的價格
        
        - force=True: 強制更新所有
        - force=False: 只更新開盤中的市場
        """
        logger.info("=" * 40)
        logger.info(f"開始更新價格快取 (force={force})")
        logger.info(f"時間: {datetime.now()}")
        
        tw_open = is_tw_market_open()
        us_open = is_us_market_open()
        logger.info(f"台股: {'開盤' if tw_open else '收盤'}, 美股: {'開盤' if us_open else '收盤'}")
        logger.info("=" * 40)
        
        tracked = self.get_all_tracked_symbols()
        
        result = {
            "tw_stocks": {"updated": 0, "failed": [], "skipped": False},
            "us_stocks": {"updated": 0, "failed": [], "skipped": False},
            "crypto": {"updated": 0, "failed": []},
            "timestamp": datetime.now().isoformat(),
        }
        
        # 台股
        if force or tw_open:
            if tracked["tw_stocks"]:
                result["tw_stocks"] = self.batch_update_stock_prices(tracked["tw_stocks"])
        else:
            result["tw_stocks"]["skipped"] = True
        
        # 美股
        if force or us_open:
            if tracked["us_stocks"]:
                result["us_stocks"] = self.batch_update_stock_prices(tracked["us_stocks"])
        else:
            result["us_stocks"]["skipped"] = True
        
        # 加密貨幣（24小時）
        if tracked["crypto"]:
            result["crypto"] = self.batch_update_crypto_prices(tracked["crypto"], force=force)
        
        result["total_updated"] = (
            result["tw_stocks"].get("updated", 0) +
            result["us_stocks"].get("updated", 0) +
            result["crypto"].get("updated", 0)
        )
        
        logger.info(f"更新完成: 共 {result['total_updated']} 筆")
        return result
