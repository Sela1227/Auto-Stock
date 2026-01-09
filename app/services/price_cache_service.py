"""
價格快取服務
負責批次更新追蹤股票的即時價格

排程邏輯：
- 台股開盤 (09:00-13:30)：每 10 分鐘更新台股
- 美股開盤 (21:30-05:00)：每 10 分鐘更新美股
- 收盤後：不更新（使用收盤價）
- 加密貨幣：24 小時每 10 分鐘更新
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


# 台股名稱對照（常見的）
TAIWAN_STOCK_NAMES = {
    "0050": "元大台灣50",
    "0051": "元大中型100",
    "0052": "富邦科技",
    "0053": "元大電子",
    "0055": "元大MSCI金融",
    "0056": "元大高股息",
    "0057": "富邦摩台",
    "006205": "富邦上証",
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
    "00682U": "元大美債20",
    "00683L": "元大美債反1",
    "00685L": "群益臺灣加權正2",
    "00686R": "群益臺灣加權反1",
    "00688L": "國泰20年美債正2",
    "00689R": "國泰20年美債反1",
    "00690": "兆豐藍籌30",
    "00692": "富邦公司治理",
    "00693U": "街口S&P黃金",
    "00696": "富邦游戲娛樂",
    "00700": "富邦恒生國企",
    "00701": "國泰股利精選30",
    "00703": "台新MSCI中國",
    "00706L": "元大美元指數正2",
    "00707R": "元大美元指數反1",
    "00708L": "元大歐洲50正2",
    "00709": "富邦歐洲",
    "00710B": "復華彭博非投等債",
    "00711B": "復華中國5年債",
    "00712": "復華富時不動產",
    "00713": "元大台灣高息低波",
    "00714": "群益道瓊美國地產",
    "00715L": "街口投信布蘭特正2",
    "00717": "富邦美國特別股",
    "00720B": "元大投資級公司債",
    "00721B": "元大中國債3-5",
    "00730": "富邦臺灣優質高息",
    "00731": "復華富時高息低波",
    "00733": "富邦臺灣中小",
    "00735": "國泰臺韓科技",
    "00736": "國泰新興市場",
    "00737": "國泰AI+Robo",
    "00738U": "元大道瓊白銀",
    "00739": "元大MSCI A股",
    "00752": "中信中國高股息",
    "00753L": "中信中國50正2",
    "00757": "統一FANG+",
    "00762": "元大全球AI",
    "00763U": "街口道瓊銅",
    "00770": "國泰北美科技",
    "00771": "元大US高息特別股",
    "00772B": "中信高評級公司債",
    "00773B": "中信優先金融債",
    "00774B": "新光投等債15+",
    "00775B": "新光美債1-3",
    "00850": "元大臺灣ESG永續",
    "00851": "台新全球AI",
    "00852L": "國泰美國費半正2",
    "00853": "統一MSCI韓國",
    "00861": "元大全球未來關鍵科技",
    "00865B": "國泰US短期公債",
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
    "00897": "富邦基因免疫生技",
    "00898": "國泰基因免疫革命",
    "00899": "富邦美債20年",
    "00900": "富邦特選高股息30",
    "00901": "永豐智能車供應鏈",
    "00902": "中信電池及儲能",
    "00903": "富邦元宇宙",
    "00904": "新光臺灣半導體30",
    "00905": "FT臺灣Smart",
    "00907": "永豐優息存股",
    "00908": "富邦入息REITs+",
    "00909": "國泰數位支付服務",
    "00910": "第一金太空衛星",
    "00911": "兆豐洲際半導體",
    "00912": "中信臺灣智慧50",
    "00913": "兆豐台灣晶圓製造",
    "00915": "凱基優選高股息30",
    "00916": "國泰全球品牌50",
    "00917": "中信特選金融",
    "00918": "大華優利高填息30",
    "00919": "群益台灣精選高息",
    "00920": "富邦全球非投等債",
    "00921": "兆豐龍頭等權重",
    "00922": "國泰台灣領袖50",
    "00923": "群益半導體收益",
    "00924B": "復華新興主權債",
    "00925B": "國泰投資級電信債",
    "00926": "凱基半導體",
    "00927": "群益半導體收益",
    "00928": "中信上櫃ESG30",
    "00929": "復華台灣科技優息",
    "00930": "永豐ESG低碳高息",
    "00931": "統一台灣高息動能",
    "00932": "兆豐永續高息等權",
    "00933": "國泰10Y+金融債",
    "00934": "中信成長高股息",
    "00935": "野村台灣新科技50",
    "00936": "台新臺灣IC設計",
    "00937B": "群益ESG投等債20+",
    "00939": "統一台灣高息優選",
    "00940": "元大台灣價值高息",
    "2301": "光寶科",
    "2303": "聯電",
    "2308": "台達電",
    "2317": "鴻海",
    "2324": "仁寶",
    "2327": "國巨",
    "2330": "台積電",
    "2337": "旺宏",
    "2344": "華邦電",
    "2345": "智邦",
    "2351": "順德",
    "2353": "宏碁",
    "2354": "鴻準",
    "2356": "英業達",
    "2357": "華碩",
    "2360": "致茂",
    "2376": "技嘉",
    "2377": "微星",
    "2379": "瑞昱",
    "2382": "廣達",
    "2383": "台光電",
    "2385": "群光",
    "2388": "威盛",
    "2392": "正崴",
    "2395": "研華",
    "2401": "凌陽",
    "2402": "毅嘉",
    "2408": "南亞科",
    "2409": "友達",
    "2412": "中華電",
    "2454": "聯發科",
    "2474": "可成",
    "2492": "華新科",
    "2498": "宏達電",
    "2603": "長榮",
    "2609": "陽明",
    "2610": "華航",
    "2615": "萬海",
    "2618": "長榮航",
    "2633": "台灣高鐵",
    "2801": "彰銀",
    "2809": "京城銀",
    "2812": "台中銀",
    "2816": "旺旺保",
    "2823": "中壽",
    "2834": "臺企銀",
    "2838": "聯邦銀",
    "2845": "遠東銀",
    "2867": "三商壽",
    "2880": "華南金",
    "2881": "富邦金",
    "2882": "國泰金",
    "2883": "開發金",
    "2884": "玉山金",
    "2885": "元大金",
    "2886": "兆豐金",
    "2887": "台新金",
    "2888": "新光金",
    "2889": "國票金",
    "2890": "永豐金",
    "2891": "中信金",
    "2892": "第一金",
    "2903": "遠百",
    "2912": "統一超",
    "3008": "大立光",
    "3017": "奇鋐",
    "3034": "聯詠",
    "3037": "欣興",
    "3044": "健鼎",
    "3045": "台灣大",
    "3231": "緯創",
    "3443": "創意",
    "3481": "群創",
    "3533": "嘉澤",
    "3661": "世芯-KY",
    "3665": "貿聯-KY",
    "3711": "日月光投控",
    "4904": "遠傳",
    "4938": "和碩",
    "5269": "祥碩",
    "5347": "世界",
    "5871": "中租-KY",
    "5876": "上海商銀",
    "5880": "合庫金",
    "6005": "群益證",
    "6116": "彩晶",
    "6176": "瑞儀",
    "6239": "力成",
    "6269": "台郡",
    "6285": "啟碁",
    "6409": "旭隼",
    "6415": "矽力-KY",
    "6446": "藥華藥",
    "6488": "環球晶",
    "6505": "台塑化",
    "6515": "穎崴",
    "6531": "愛普",
    "6533": "晶心科",
    "6547": "高端疫苗",
    "6552": "易華電",
    "6558": "興能高",
    "6669": "緯穎",
    "6670": "復盛應用",
    "6789": "采鈺",
    "8046": "南電",
    "8454": "富邦媒",
    "9910": "豐泰",
    "9921": "巨大",
    "9941": "裕融",
    "9945": "潤泰新",
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


# ============================================================
# 價格快取服務
# ============================================================

class PriceCacheService:
    """價格快取服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tracked_symbols(self) -> Dict[str, List[str]]:
        """取得所有被追蹤的 symbol（去重，按市場分類）"""
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
        
        logger.info(f"追蹤: 台股 {len(tw_stocks)}, 美股 {len(us_stocks)}, 加密貨幣 {len(crypto)}")
        return {"tw_stocks": tw_stocks, "us_stocks": us_stocks, "crypto": crypto}
    
    def batch_update_stock_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """批次更新股票價格"""
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
                    
                    info = ticker.info
                    if not info:
                        result["failed"].append(symbol)
                        continue
                    
                    # 取得價格
                    price = info.get("regularMarketPrice") or info.get("currentPrice")
                    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")
                    
                    if price is None:
                        # 嘗試從歷史資料取得
                        hist = ticker.history(period="2d")
                        if not hist.empty:
                            price = float(hist['Close'].iloc[-1])
                            if len(hist) > 1:
                                prev_close = float(hist['Close'].iloc[-2])
                    
                    if price is None:
                        result["failed"].append(symbol)
                        continue
                    
                    # 計算漲跌
                    change = None
                    change_pct = None
                    if prev_close and prev_close > 0:
                        change = price - prev_close
                        change_pct = (change / prev_close) * 100
                    
                    # 取得名稱
                    name = info.get("shortName") or info.get("longName") or ""
                    if not name and symbol.endswith((".TW", ".TWO")):
                        stock_code = symbol.replace(".TW", "").replace(".TWO", "")
                        name = TAIWAN_STOCK_NAMES.get(stock_code, "")
                    
                    # 取得成交量
                    volume = info.get("regularMarketVolume") or info.get("volume")
                    
                    # 更新快取
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
                    logger.error(f"更新 {symbol} 失敗: {e}")
                    result["failed"].append(symbol)
            
            self.db.commit()
            logger.info(f"股票更新完成: 成功 {result['updated']}, 失敗 {len(result['failed'])}")
            
        except Exception as e:
            logger.error(f"批次更新失敗: {e}")
        
        return result
    
    def batch_update_crypto_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """批次更新加密貨幣價格"""
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
                    logger.error(f"更新 {symbol} 失敗: {e}")
                    result["failed"].append(symbol)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"加密貨幣更新失敗: {e}")
        
        return result
    
    def _upsert_cache(self, symbol, name, price, prev_close, change, change_pct, volume, asset_type):
        """更新或新增快取"""
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
            result["crypto"] = self.batch_update_crypto_prices(tracked["crypto"])
        
        result["total_updated"] = (
            result["tw_stocks"].get("updated", 0) +
            result["us_stocks"].get("updated", 0) +
            result["crypto"].get("updated", 0)
        )
        
        logger.info(f"更新完成: 共 {result['total_updated']} 筆")
        return result
