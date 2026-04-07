"""
å ±é…¬çŽ‡æ¯”è¼ƒæœå‹™
è¨ˆç®—ä¸¦æ¯”è¼ƒå¤šå€‹æ¨™çš„çš„å¹´åŒ–å ±é…¬çŽ‡ (CAGR)

ä¿®å¾©ï¼š
1. å°è‚¡ä»£è™Ÿè‡ªå‹•åŠ  .TW / .TWO
2. ä½¿ç”¨èª¿æ•´å¾Œåƒ¹æ ¼(adj_close)è¨ˆç®—ï¼Œé¿å…åˆ†å‰²å½±éŸ¿
3. åŠ å…¥é…æ¯é‚„åŽŸï¼Œåæ˜ çœŸå¯¦å ±é…¬
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import pandas as pd

from app.models.comparison import Comparison
from app.data_sources.yahoo_finance import yahoo_finance
from app.data_sources.coingecko import coingecko, CRYPTO_MAP

logger = logging.getLogger(__name__)


# é è¨­æ¯”è¼ƒçµ„åˆ
PRESET_GROUPS = {
    "us_tech": {
        "name": "ç¾Žåœ‹ç§‘æŠ€è‚¡",
        "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
        "description": "ç¾Žåœ‹äº”å¤§ç§‘æŠ€å·¨é ­"
    },
    "crypto_major": {
        "name": "ä¸»æµåŠ å¯†è²¨å¹£",
        "symbols": ["BTC", "ETH", "SOL", "BNB", "XRP"],
        "description": "å¸‚å€¼å‰äº”å¤§åŠ å¯†è²¨å¹£"
    },
    "index": {
        "name": "å¤§ç›¤æŒ‡æ•¸",
        "symbols": ["^GSPC", "^IXIC", "^DJI"],
        "description": "ç¾Žåœ‹ä¸‰å¤§æŒ‡æ•¸"
    },
    "etf_popular": {
        "name": "ç†±é–€ ETF",
        "symbols": ["SPY", "QQQ", "VOO", "VTI", "IWM"],
        "description": "æœ€å—æ­¡è¿Žçš„ ETF"
    },
    "dividend": {
        "name": "é«˜è‚¡æ¯è‚¡ç¥¨",
        "symbols": ["JNJ", "PG", "KO", "PEP", "VZ"],
        "description": "ç©©å®šé…æ¯çš„è—ç±Œè‚¡"
    },
    "tw_etf": {
        "name": "å°è‚¡ ETF",
        "symbols": ["0050", "0056", "00878", "00919", "006208"],
        "description": "å°ç£ç†±é–€ ETF"
    },
    "tw_tech": {
        "name": "å°ç£ç§‘æŠ€è‚¡",
        "symbols": ["2330", "2454", "2317", "3711", "2308"],
        "description": "å°ç£ç§‘æŠ€æ¬Šå€¼è‚¡"
    }
}

# åŸºæº–æŒ‡æ•¸é¸é …
BENCHMARK_OPTIONS = {
    "^GSPC": "S&P 500",
    "^IXIC": "ç´æ–¯é”å…‹",
    "^DJI": "é“ç“Šå·¥æ¥­",
    "": "ç„¡"
}

# æ”¯æ´çš„åŠ å¯†è²¨å¹£
SUPPORTED_CRYPTO = set(k for k in CRYPTO_MAP.keys() if k not in ("BITCOIN", "ETHEREUM"))


class CompareService:
    """å ±é…¬çŽ‡æ¯”è¼ƒæœå‹™"""
    
    def __init__(self):
        self.max_symbols = 5  # æœ€å¤šæ¯”è¼ƒ 5 å€‹
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        æ¨™æº–åŒ–è‚¡ç¥¨ä»£è™Ÿ
        - å°è‚¡ä»£è™Ÿï¼ˆç´”æ•¸å­— 4-6 ä½ï¼‰è‡ªå‹•åŠ  .TW
        - å…¶ä»–ä¿æŒåŽŸæ¨£
        """
        symbol = symbol.strip().upper()
        
        # å¦‚æžœå·²ç¶“æœ‰å¾Œç¶´ï¼Œä¸è™•ç†
        if '.' in symbol or symbol.startswith('^'):
            return symbol
        
        # æª¢æŸ¥æ˜¯å¦ç‚ºåŠ å¯†è²¨å¹£
        if symbol in SUPPORTED_CRYPTO:
            return symbol
        
        # å°è‚¡ä»£è™Ÿï¼š4-6 ä½ç´”æ•¸å­—
        if symbol.isdigit() and 4 <= len(symbol) <= 6:
            return f"{symbol}.TW"
        
        return symbol
    
    def _get_asset_type(self, symbol: str) -> str:
        """åˆ¤æ–·è³‡ç”¢é¡žåž‹"""
        symbol_upper = symbol.upper()
        
        # å…ˆæª¢æŸ¥åŽŸå§‹ä»£è™Ÿæ˜¯å¦ç‚ºåŠ å¯†è²¨å¹£
        base_symbol = symbol_upper.replace('.TW', '').replace('.TWO', '')
        if base_symbol in SUPPORTED_CRYPTO:
            return "crypto"
        
        if symbol_upper.startswith("^"):
            return "index"
        elif symbol_upper.endswith(".TW") or symbol_upper.endswith(".TWO"):
            return "tw_stock"
        else:
            return "stock"
    
    def _get_period_days(self, period: str) -> int:
        """å–å¾—æ™‚é–“é€±æœŸå°æ‡‰çš„å¤©æ•¸"""
        period_map = {
            "1y": 365,
            "3y": 365 * 3,
            "5y": 365 * 5,
            "10y": 365 * 10,
        }
        return period_map.get(period, 365)
    
    async def _fetch_price_data(
        self,
        symbol: str,
        days: int = 3650,  # é è¨­æŠ“ 10 å¹´
    ) -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
        """
        æŠ“å–åƒ¹æ ¼è³‡æ–™
        
        Returns:
            (DataFrame, info_dict) æˆ– (None, None)
        """
        asset_type = self._get_asset_type(symbol)
        
        try:
            if asset_type == "crypto":
                # åŠ å¯†è²¨å¹£ç”¨ CoinGecko
                df = coingecko.get_crypto_history(symbol, days=days)
                info = coingecko.get_crypto_info(symbol)
                if info:
                    info_dict = {
                        "name": info.get("name", symbol),
                        "type": "crypto",
                        "current_price": info.get("current_price"),
                    }
                else:
                    info_dict = {"name": symbol, "type": "crypto", "current_price": None}
                return df, info_dict
            else:
                # è‚¡ç¥¨/æŒ‡æ•¸/ETF ç”¨ Yahoo Finance
                period = "10y" if days >= 3650 else ("5y" if days >= 1825 else "1y")
                df = yahoo_finance.get_stock_history(symbol, period=period)
                
                # å¦‚æžœ .TW æ‰¾ä¸åˆ°ï¼Œå˜—è©¦ .TWO (ä¸Šæ«ƒè‚¡ç¥¨)
                if (df is None or df.empty) and symbol.endswith('.TW'):
                    two_symbol = symbol.replace('.TW', '.TWO')
                    logger.info(f"{symbol} æ‰¾ä¸åˆ°ï¼Œå˜—è©¦ä¸Šæ«ƒè‚¡ç¥¨: {two_symbol}")
                    df = yahoo_finance.get_stock_history(two_symbol, period=period)
                    if df is not None and not df.empty:
                        symbol = two_symbol
                        logger.info(f"æˆåŠŸæ‰¾åˆ°ä¸Šæ«ƒè‚¡ç¥¨: {two_symbol}")
                
                info = yahoo_finance.get_stock_info(symbol)
                
                # å–å¾—ç¾åƒ¹ï¼ˆç”¨åŽŸå§‹æ”¶ç›¤åƒ¹ï¼‰
                current_price = None
                if df is not None and not df.empty:
                    current_price = float(df['close'].iloc[-1])
                
                if info:
                    info_dict = {
                        "name": info.get("name", symbol),
                        "type": asset_type,
                        "current_price": current_price or info.get("current_price"),
                        "symbol": symbol,  # å¯èƒ½å·²ç¶“æ”¹æˆ .TWO
                    }
                else:
                    info_dict = {
                        "name": symbol, 
                        "type": asset_type, 
                        "current_price": current_price,
                        "symbol": symbol,
                    }
                
                return df, info_dict
            
        except Exception as e:
            logger.error(f"æŠ“å– {symbol} è³‡æ–™å¤±æ•—: {e}")
            return None, None
    
    def _calculate_cagr_with_dividends(
        self,
        symbol: str,
        df: pd.DataFrame,
        years: int,
    ) -> Optional[float]:
        """
        è¨ˆç®—å«é…æ¯èª¿æ•´çš„ CAGR
        
        ä½¿ç”¨ adj_closeï¼ˆåˆ†å‰²èª¿æ•´ï¼‰+ é…æ¯é‚„åŽŸ
        é€™å’Œè‚¡ç¥¨æŸ¥è©¢é é¢çš„è¨ˆç®—æ–¹å¼ä¸€è‡´
        """
        if df is None or df.empty:
            return None
        
        try:
            # ç¢ºä¿æœ‰ date æ¬„ä½
            if 'date' not in df.columns:
                df = df.reset_index()
                if 'Date' in df.columns:
                    df = df.rename(columns={'Date': 'date'})
            
            df['date'] = pd.to_datetime(df['date']).dt.date
            df = df.sort_values('date').reset_index(drop=True)
            
            current_date = df['date'].iloc[-1]
            target_date = current_date - timedelta(days=years * 365)
            
            # æ‰¾åˆ°ç›®æ¨™æ—¥æœŸä¹‹å‰çš„è³‡æ–™
            past_df = df[df['date'] <= target_date]
            
            if past_df.empty or len(past_df) < 10:
                return None
            
            # å„ªå…ˆä½¿ç”¨ adj_closeï¼Œæ²’æœ‰å‰‡ç”¨ close
            price_col = 'adj_close' if 'adj_close' in df.columns else 'close'
            
            start_row = past_df.iloc[-1]
            start_price = float(start_row[price_col])
            start_date = start_row['date']
            
            current_price = float(df.iloc[-1][price_col])
            
            if start_price <= 0:
                return None
            
            # å–å¾—é…æ¯è³‡æ–™ä¸¦èª¿æ•´
            try:
                dividends_df = yahoo_finance.get_dividends(symbol, period=f"{years + 1}y")
                
                if dividends_df is not None and not dividends_df.empty:
                    # å»ºç«‹å«é…æ¯èª¿æ•´çš„åƒ¹æ ¼åºåˆ—
                    df_adj = df.copy()
                    df_adj['adj_with_div'] = df_adj[price_col].astype(float)
                    
                    date_to_idx = {row['date']: idx for idx, row in df_adj.iterrows()}
                    
                    # ç¯©é¸åœ¨è¨ˆç®—ç¯„åœå…§çš„é…æ¯
                    min_date = df_adj['date'].min()
                    max_date = df_adj['date'].max()
                    
                    dividends = {}
                    for _, row in dividends_df.iterrows():
                        div_date = row['date']
                        if isinstance(div_date, str):
                            div_date = datetime.strptime(div_date, '%Y-%m-%d').date()
                        elif hasattr(div_date, 'date'):
                            div_date = div_date.date()
                        if min_date < div_date <= max_date:
                            dividends[div_date] = float(row['amount'])
                    
                    # å¾žæœ€æ–°åˆ°æœ€èˆŠè™•ç†é…æ¯ï¼ˆé…æ¯é‚„åŽŸèª¿æ•´ï¼‰
                    for div_date, div_amount in sorted(dividends.items(), reverse=True):
                        if div_date in date_to_idx:
                            ex_idx = date_to_idx[div_date]
                            if ex_idx > 0:
                                prev_price = df_adj.loc[ex_idx - 1, 'adj_with_div']
                                if prev_price > div_amount and div_amount > 0:
                                    adjustment_factor = prev_price / (prev_price - div_amount)
                                    df_adj.loc[:ex_idx-1, 'adj_with_div'] = df_adj.loc[:ex_idx-1, 'adj_with_div'] / adjustment_factor
                    
                    # ä½¿ç”¨èª¿æ•´å¾Œçš„åƒ¹æ ¼è¨ˆç®—
                    start_price = float(df_adj[df_adj['date'] <= target_date].iloc[-1]['adj_with_div'])
                    current_price = float(df_adj.iloc[-1]['adj_with_div'])
                    
                    logger.debug(f"{symbol} é…æ¯èª¿æ•´: æ‰¾åˆ° {len(dividends)} ç­†é…æ¯")
                    
            except Exception as e:
                logger.warning(f"{symbol} é…æ¯èª¿æ•´å¤±æ•—ï¼Œä½¿ç”¨åŸºæœ¬è¨ˆç®—: {e}")
            
            # å¯¦éš›å¹´æ•¸ï¼ˆæ›´ç²¾ç¢ºï¼‰
            actual_days = (current_date - start_date).days
            actual_years = actual_days / 365.25
            
            if actual_years < 0.5:
                return None
            
            # CAGR å…¬å¼
            cagr = (current_price / start_price) ** (1 / actual_years) - 1
            
            # æª¢æŸ¥æœ‰æ•ˆæ€§
            if math.isnan(cagr) or math.isinf(cagr):
                return None
            
            return round(cagr * 100, 2)
            
        except Exception as e:
            logger.error(f"è¨ˆç®— {symbol} CAGR å¤±æ•—: {e}")
            return None
    
    def _calculate_custom_cagr(
        self,
        df: pd.DataFrame,
        start_date: date,
        end_date: date,
    ) -> Optional[float]:
        """è¨ˆç®—è‡ªè¨‚å€é–“çš„ CAGR"""
        if df is None or df.empty:
            return None
        
        try:
            # ç¢ºä¿æ—¥æœŸæ¬„ä½
            if 'date' in df.columns:
                df = df.set_index('date')
            
            # ç¯©é¸æ—¥æœŸç¯„åœ
            mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
            filtered_df = df[mask]
            
            if len(filtered_df) < 2:
                return None
            
            # å„ªå…ˆä½¿ç”¨ adj_close
            price_col = 'adj_close' if 'adj_close' in filtered_df.columns else 'close'
            
            start_price = float(filtered_df[price_col].iloc[0])
            end_price = float(filtered_df[price_col].iloc[-1])
            
            # è¨ˆç®—å¹´æ•¸
            days = (end_date - start_date).days
            years = days / 365.0
            
            if years <= 0 or start_price <= 0:
                return None
            
            # CAGR å…¬å¼
            cagr = (end_price / start_price) ** (1 / years) - 1
            return round(cagr * 100, 2)
            
        except Exception as e:
            logger.error(f"è¨ˆç®—è‡ªè¨‚ CAGR å¤±æ•—: {e}")
            return None
    
    async def compare_cagr(
        self,
        symbols: List[str],
        periods: List[str] = None,
        custom_range: Dict[str, str] = None,
        benchmark: str = "^GSPC",
        sort_by: str = "5y",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """
        æ¯”è¼ƒå¤šå€‹æ¨™çš„çš„å¹´åŒ–å ±é…¬çŽ‡
        
        Args:
            symbols: æ¨™çš„ä»£è™Ÿåˆ—è¡¨ (æœ€å¤š 5 å€‹)
            periods: æ™‚é–“é€±æœŸ ["1y", "3y", "5y", "10y"]
            custom_range: è‡ªè¨‚å€é–“ {"start": "2020-01-01", "end": "2024-12-31"}
            benchmark: åŸºæº–æŒ‡æ•¸
            sort_by: æŽ’åºä¾æ“š
            sort_order: æŽ’åºæ–¹å‘ "asc" / "desc"
            
        Returns:
            æ¯”è¼ƒçµæžœ
        """
        # é©—è­‰
        if not symbols:
            return {"success": False, "error": "è«‹è‡³å°‘é¸æ“‡ä¸€å€‹æ¨™çš„"}
        
        if len(symbols) > self.max_symbols:
            return {"success": False, "error": f"æœ€å¤šåªèƒ½æ¯”è¼ƒ {self.max_symbols} å€‹æ¨™çš„"}
        
        if periods is None:
            periods = ["1y", "3y", "5y"]
        
        # æ­£è¦åŒ–ä»£è™Ÿï¼ˆè™•ç†å°è‚¡ç­‰ï¼‰
        symbols = [self._normalize_symbol(s) for s in symbols]
        logger.info(f"æ¨™æº–åŒ–å¾Œçš„ä»£è™Ÿ: {symbols}")
        
        # è¨ˆç®—éœ€è¦çš„å¤©æ•¸
        max_days = 3650  # 10 å¹´
        if custom_range:
            try:
                start_date = datetime.strptime(custom_range["start"], "%Y-%m-%d").date()
                end_date = datetime.strptime(custom_range["end"], "%Y-%m-%d").date()
                custom_days = (date.today() - start_date).days
                max_days = max(max_days, custom_days)
            except (ValueError, KeyError):
                custom_range = None
        
        results = []
        
        # è™•ç†æ¯å€‹æ¨™çš„
        for symbol in symbols:
            df, info = await self._fetch_price_data(symbol, max_days)
            
            # å¦‚æžœæœ‰ symbol æ›´æ–°ï¼ˆä¾‹å¦‚ .TW -> .TWOï¼‰ï¼Œä½¿ç”¨æ›´æ–°å¾Œçš„
            actual_symbol = info.get("symbol", symbol) if info else symbol
            
            if df is None or info is None:
                results.append({
                    "symbol": actual_symbol,
                    "name": actual_symbol,
                    "type": self._get_asset_type(actual_symbol),
                    "current_price": None,
                    "cagr": {p: None for p in periods},
                    "error": "ç„¡æ³•å–å¾—è³‡æ–™"
                })
                continue
            
            # è¨ˆç®—å„é€±æœŸ CAGRï¼ˆä½¿ç”¨å«é…æ¯çš„è¨ˆç®—ï¼‰
            cagr_results = {}
            for period in periods:
                period_years = {"1y": 1, "3y": 3, "5y": 5, "10y": 10}.get(period)
                if period_years:
                    cagr_results[period] = self._calculate_cagr_with_dividends(
                        actual_symbol, df, period_years
                    )
            
            # è‡ªè¨‚å€é–“
            if custom_range:
                cagr_results["custom"] = self._calculate_custom_cagr(
                    df, start_date, end_date
                )
            
            results.append({
                "symbol": actual_symbol,
                "name": info.get("name", actual_symbol),
                "type": info.get("type", "stock"),
                "current_price": info.get("current_price"),
                "cagr": cagr_results,
            })
        
        # è¨ˆç®—åŸºæº–æŒ‡æ•¸
        benchmark_data = None
        if benchmark:
            benchmark_df, benchmark_info = await self._fetch_price_data(benchmark, max_days)
            if benchmark_df is not None:
                benchmark_cagr = {}
                for period in periods:
                    period_years = {"1y": 1, "3y": 3, "5y": 5, "10y": 10}.get(period)
                    if period_years:
                        benchmark_cagr[period] = self._calculate_cagr_with_dividends(
                            benchmark, benchmark_df, period_years
                        )
                
                benchmark_data = {
                    "symbol": benchmark,
                    "name": BENCHMARK_OPTIONS.get(benchmark, benchmark),
                    "cagr": benchmark_cagr,
                }
                
                # è¨ˆç®— vs benchmark
                for result in results:
                    result["vs_benchmark"] = {}
                    for period in periods:
                        result_cagr = result["cagr"].get(period)
                        bench_cagr = benchmark_cagr.get(period)
                        if result_cagr is not None and bench_cagr is not None:
                            result["vs_benchmark"][period] = round(result_cagr - bench_cagr, 2)
                        else:
                            result["vs_benchmark"][period] = None
        
        # æŽ’åº
        def get_sort_value(item):
            val = item.get("cagr", {}).get(sort_by)
            return val if val is not None else float('-inf')
        
        results.sort(key=get_sort_value, reverse=(sort_order == "desc"))
        
        # åŠ å…¥æŽ’å
        for i, result in enumerate(results):
            result["rank"] = i + 1
        
        return {
            "success": True,
            "comparison": results,
            "benchmark": benchmark_data,
            "periods": periods + (["custom"] if custom_range else []),
            "custom_range": custom_range,
            "sort_by": sort_by,
            "generated_at": datetime.now().isoformat(),
            "note": "CAGR å·²åŒ…å«åˆ†å‰²èª¿æ•´åŠé…æ¯å†æŠ•å…¥æ•ˆæžœ"
        }
    
    def get_presets(self) -> List[Dict[str, Any]]:
        """å–å¾—é è¨­çµ„åˆåˆ—è¡¨"""
        return [
            {
                "id": key,
                "name": value["name"],
                "description": value["description"],
                "symbols": value["symbols"],
                "count": len(value["symbols"]),
            }
            for key, value in PRESET_GROUPS.items()
        ]
    
    def get_preset_detail(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """å–å¾—é è¨­çµ„åˆè©³æƒ…"""
        if preset_id not in PRESET_GROUPS:
            return None
        
        preset = PRESET_GROUPS[preset_id]
        return {
            "id": preset_id,
            "name": preset["name"],
            "description": preset["description"],
            "symbols": preset["symbols"],
        }


class ComparisonCRUD:
    """æ¯”è¼ƒçµ„åˆ CRUD æ“ä½œ"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_comparisons(self, user_id: int) -> List[Comparison]:
        """å–å¾—ç”¨æˆ¶çš„æ¯”è¼ƒçµ„åˆ"""
        result = await self.db.execute(
            select(Comparison)
            .where(Comparison.user_id == user_id)
            .order_by(Comparison.updated_at.desc())
        )
        return result.scalars().all()
    
    async def get_comparison_by_id(self, comparison_id: int, user_id: int) -> Optional[Comparison]:
        """å–å¾—å–®ä¸€æ¯”è¼ƒçµ„åˆ"""
        result = await self.db.execute(
            select(Comparison)
            .where(and_(Comparison.id == comparison_id, Comparison.user_id == user_id))
        )
        return result.scalar_one_or_none()
    
    async def create_comparison(
        self,
        user_id: int,
        name: str,
        symbols: List[str],
        benchmark: str = None,
    ) -> Comparison:
        """å»ºç«‹æ¯”è¼ƒçµ„åˆ"""
        comparison = Comparison(
            user_id=user_id,
            name=name,
            _symbols=json.dumps(symbols),
            benchmark=benchmark,
        )
        self.db.add(comparison)
        await self.db.commit()
        await self.db.refresh(comparison)
        return comparison
    
    async def update_comparison(
        self,
        comparison: Comparison,
        name: str = None,
        symbols: List[str] = None,
        benchmark: str = None,
    ) -> Comparison:
        """æ›´æ–°æ¯”è¼ƒçµ„åˆ"""
        if name is not None:
            comparison.name = name
        if symbols is not None:
            comparison._symbols = json.dumps(symbols)
        if benchmark is not None:
            comparison.benchmark = benchmark
        
        await self.db.commit()
        await self.db.refresh(comparison)
        return comparison
    
    async def delete_comparison(self, comparison: Comparison) -> bool:
        """åˆªé™¤æ¯”è¼ƒçµ„åˆ"""
        await self.db.delete(comparison)
        await self.db.commit()
        return True
    
    async def count_user_comparisons(self, user_id: int) -> int:
        """è¨ˆç®—ç”¨æˆ¶çš„æ¯”è¼ƒçµ„åˆæ•¸é‡"""
        result = await self.db.execute(
            select(Comparison)
            .where(Comparison.user_id == user_id)
        )
        return len(result.scalars().all())


# å–®ä¾‹
compare_service = CompareService()