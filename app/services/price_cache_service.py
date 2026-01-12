"""
åƒ¹æ ¼å¿«å–æœå‹™
è² è²¬æ‰¹æ¬¡æ›´æ–°è¿½è¹¤è‚¡ç¥¨çš„å³æ™‚åƒ¹æ ¼

æŽ’ç¨‹é‚è¼¯ï¼š
- å°è‚¡é–‹ç›¤ (09:00-13:30)ï¼šæ¯ 10 åˆ†é˜æ›´æ–°å°è‚¡
- ç¾Žè‚¡é–‹ç›¤ (21:30-05:00)ï¼šæ¯ 10 åˆ†é˜æ›´æ–°ç¾Žè‚¡
- æ”¶ç›¤å¾Œï¼šä¸æ›´æ–°ï¼ˆä½¿ç”¨æ”¶ç›¤åƒ¹ï¼‰
- åŠ å¯†è²¨å¹£ï¼š24 å°æ™‚æ¯ 10 åˆ†é˜æ›´æ–°
"""
import logging
from datetime import datetime, time
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
import yfinance as yf

from app.models.price_cache import StockPriceCache
from app.models.watchlist import Watchlist

logger = logging.getLogger(__name__)


# å°è‚¡åç¨±å°ç…§ï¼ˆå¸¸è¦‹çš„ï¼‰
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
# é–‹ç›¤æ™‚é–“åˆ¤æ–·ï¼ˆå°ç£æ™‚é–“ï¼‰
# ============================================================

def is_tw_market_open() -> bool:
    """åˆ¤æ–·å°è‚¡æ˜¯å¦é–‹ç›¤ï¼ˆé€±ä¸€åˆ°é€±äº” 09:00-13:30ï¼‰"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    return time(9, 0) <= now.time() <= time(13, 30)


def is_us_market_open() -> bool:
    """åˆ¤æ–·ç¾Žè‚¡æ˜¯å¦é–‹ç›¤ï¼ˆå°ç£æ™‚é–“ 21:30-05:00ï¼‰"""
    now = datetime.now()
    weekday = now.weekday()
    current_time = now.time()
    
    # æ™šä¸Š 21:30 å¾Œï¼ˆé€±ä¸€åˆ°é€±äº”ï¼‰
    if weekday < 5 and current_time >= time(21, 30):
        return True
    # å‡Œæ™¨ 05:00 å‰ï¼ˆé€±äºŒåˆ°é€±å…­ï¼‰
    if weekday > 0 and current_time <= time(5, 0):
        return True
    # é€±å…­å‡Œæ™¨
    if weekday == 5 and current_time <= time(5, 0):
        return True
    return False


def get_market_status() -> Dict[str, bool]:
    """å–å¾—å„å¸‚å ´é–‹ç›¤ç‹€æ…‹"""
    return {
        "tw_open": is_tw_market_open(),
        "us_open": is_us_market_open(),
        "crypto_open": True,
    }


# ============================================================
# åƒ¹æ ¼å¿«å–æœå‹™
# ============================================================

class PriceCacheService:
    """åƒ¹æ ¼å¿«å–æœå‹™"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tracked_symbols(self) -> Dict[str, List[str]]:
        """å–å¾—æ‰€æœ‰è¢«è¿½è¹¤çš„ symbolï¼ˆåŽ»é‡ï¼ŒæŒ‰å¸‚å ´åˆ†é¡žï¼‰"""
        stmt = select(distinct(Watchlist.symbol), Watchlist.asset_type)
        results = self.db.execute(stmt).all()
        
        tw_stocks = []
        us_stocks = []
        crypto = []
        
        for symbol, asset_type in results:
            if asset_type == "crypto":
                crypto.append(symbol)
            elif symbol.endswith((".TW", ".TWO")):
                tw_stocks.append(symbol)
            else:
                us_stocks.append(symbol)
        
        logger.info(f"è¿½è¹¤: å°è‚¡ {len(tw_stocks)}, ç¾Žè‚¡ {len(us_stocks)}, åŠ å¯†è²¨å¹£ {len(crypto)}")
        return {"tw_stocks": tw_stocks, "us_stocks": us_stocks, "crypto": crypto}
    
    def batch_update_stock_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """æ‰¹æ¬¡æ›´æ–°è‚¡ç¥¨åƒ¹æ ¼"""
        if not symbols:
            return {"updated": 0, "failed": []}
        
        result = {"updated": 0, "failed": []}
        logger.info(f"é–‹å§‹æ›´æ–° {len(symbols)} æ”¯è‚¡ç¥¨...")
        
        try:
            # ä½¿ç”¨ yfinance æ‰¹æ¬¡å–å¾—
            tickers = yf.Tickers(" ".join(symbols))
            
            for symbol in symbols:
                try:
                    ticker = tickers.tickers.get(symbol)
                    if not ticker:
                        result["failed"].append(symbol)
                        continue
                    
                    info = ticker.info
                    if not info:
                        result["failed"].append(symbol)
                        continue
                    
                    # å–å¾—åƒ¹æ ¼
                    price = info.get("regularMarketPrice") or info.get("currentPrice")
                    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
                    
                    if price is None:
                        # å˜—è©¦å¾žæ­·å²è³‡æ–™å–å¾—
                        hist = ticker.history(period="2d")
                        if not hist.empty:
                            price = float(hist['Close'].iloc[-1])
                            if len(hist) > 1:
                                prev_close = float(hist['Close'].iloc[-2])
                    
                    if price is None:
                        result["failed"].append(symbol)
                        continue
                    
                    # è¨ˆç®—æ¼²è·Œ
                    change = None
                    change_pct = None
                    if prev_close and prev_close > 0:
                        change = price - prev_close
                        change_pct = (change / prev_close) * 100
                    
                    # å–å¾—åç¨±
                    name = info.get("shortName") or info.get("longName") or ""
                    if not name and symbol.endswith((".TW", ".TWO")):
                        stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                        name = TAIWAN_STOCK_NAMES.get(stock_code, "")
                    
                    # å–å¾—æˆäº¤é‡
                    volume = info.get("regularMarketVolume") or info.get("volume")
                    
                    # æ›´æ–°å¿«å–
                    self._upsert_cache(
                        symbol=symbol,
                        name=name,
                        price=price,
                        prev_close=prev_close,
                        change=change,
                        change_pct=change_pct,
                        volume=volume,
                        asset_type="stock",
                    )
                    result["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"æ›´æ–° {symbol} å¤±æ•—: {e}")
                    result["failed"].append(symbol)
            
            self.db.commit()
            logger.info(f"è‚¡ç¥¨æ›´æ–°å®Œæˆ: æˆåŠŸ {result['updated']}, å¤±æ•— {len(result['failed'])}")
            
        except Exception as e:
            logger.error(f"æ‰¹æ¬¡æ›´æ–°å¤±æ•—: {e}")
        
        return result
    
    def batch_update_crypto_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """æ‰¹æ¬¡æ›´æ–°åŠ å¯†è²¨å¹£åƒ¹æ ¼"""
        if not symbols:
            return {"updated": 0, "failed": []}
        
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
                    )
                    result["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"æ›´æ–° {symbol} å¤±æ•—: {e}")
                    result["failed"].append(symbol)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"åŠ å¯†è²¨å¹£æ›´æ–°å¤±æ•—: {e}")
        
        return result
    
    def _upsert_cache(self, symbol, name, price, prev_close, change, change_pct, volume, asset_type):
        """æ›´æ–°æˆ–æ–°å¢žå¿«å–"""
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
            cache.updated_at = datetime.now()
        else:
            cache = StockPriceCache(
                symbol=symbol,
                name=name,
                price=price,
                prev_close=prev_close,
                change=change,
                change_pct=change_pct,
                volume=volume,
                asset_type=asset_type,
            )
            self.db.add(cache)
    
    def update_all(self, force: bool = False) -> Dict[str, Any]:
        """
        æ›´æ–°æ‰€æœ‰è¿½è¹¤çš„åƒ¹æ ¼
        
        - force=True: å¼·åˆ¶æ›´æ–°æ‰€æœ‰
        - force=False: åªæ›´æ–°é–‹ç›¤ä¸­çš„å¸‚å ´
        """
        logger.info("=" * 40)
        logger.info(f"é–‹å§‹æ›´æ–°åƒ¹æ ¼å¿«å– (force={force})")
        logger.info(f"æ™‚é–“: {datetime.now()}")
        
        tw_open = is_tw_market_open()
        us_open = is_us_market_open()
        logger.info(f"å°è‚¡: {'é–‹ç›¤' if tw_open else 'æ”¶ç›¤'}, ç¾Žè‚¡: {'é–‹ç›¤' if us_open else 'æ”¶ç›¤'}")
        logger.info("=" * 40)
        
        tracked = self.get_all_tracked_symbols()
        
        result = {
            "tw_stocks": {"updated": 0, "failed": [], "skipped": False},
            "us_stocks": {"updated": 0, "failed": [], "skipped": False},
            "crypto": {"updated": 0, "failed": []},
            "timestamp": datetime.now().isoformat(),
        }
        
        # å°è‚¡
        if force or tw_open:
            if tracked["tw_stocks"]:
                result["tw_stocks"] = self.batch_update_stock_prices(tracked["tw_stocks"])
        else:
            result["tw_stocks"]["skipped"] = True
        
        # ç¾Žè‚¡
        if force or us_open:
            if tracked["us_stocks"]:
                result["us_stocks"] = self.batch_update_stock_prices(tracked["us_stocks"])
        else:
            result["us_stocks"]["skipped"] = True
        
        # åŠ å¯†è²¨å¹£ï¼ˆ24å°æ™‚ï¼‰
        if tracked["crypto"]:
            result["crypto"] = self.batch_update_crypto_prices(tracked["crypto"])
        
        result["total_updated"] = (
            result["tw_stocks"].get("updated", 0) +
            result["us_stocks"].get("updated", 0) +
            result["crypto"].get("updated", 0)
        )
        
        logger.info(f"æ›´æ–°å®Œæˆ: å…± {result['total_updated']} ç­†")
        return result
