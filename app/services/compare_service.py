"""
報酬率比較服務
計算並比較多個標的的年化報酬率 (CAGR)

修復：
1. 台股代號自動加 .TW / .TWO
2. 使用調整後價格(adj_close)計算，避免分割影響
3. 加入配息還原，反映真實報酬
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


# 預設比較組合
PRESET_GROUPS = {
    "us_tech": {
        "name": "美國科技股",
        "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
        "description": "美國五大科技巨頭"
    },
    "crypto_major": {
        "name": "主流加密貨幣",
        "symbols": ["BTC", "ETH", "SOL", "BNB", "XRP"],
        "description": "市值前五大加密貨幣"
    },
    "index": {
        "name": "大盤指數",
        "symbols": ["^GSPC", "^IXIC", "^DJI"],
        "description": "美國三大指數"
    },
    "etf_popular": {
        "name": "熱門 ETF",
        "symbols": ["SPY", "QQQ", "VOO", "VTI", "IWM"],
        "description": "最受歡迎的 ETF"
    },
    "dividend": {
        "name": "高股息股票",
        "symbols": ["JNJ", "PG", "KO", "PEP", "VZ"],
        "description": "穩定配息的藍籌股"
    },
    "tw_etf": {
        "name": "台股 ETF",
        "symbols": ["0050", "0056", "00878", "00919", "006208"],
        "description": "台灣熱門 ETF"
    },
    "tw_tech": {
        "name": "台灣科技股",
        "symbols": ["2330", "2454", "2317", "3711", "2308"],
        "description": "台灣科技權值股"
    }
}

# 基準指數選項
BENCHMARK_OPTIONS = {
    "^GSPC": "S&P 500",
    "^IXIC": "納斯達克",
    "^DJI": "道瓊工業",
    "": "無"
}

# 支援的加密貨幣
SUPPORTED_CRYPTO = set(k for k in CRYPTO_MAP.keys() if k not in ("BITCOIN", "ETHEREUM"))


class CompareService:
    """報酬率比較服務"""
    
    def __init__(self):
        self.max_symbols = 5  # 最多比較 5 個
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        標準化股票代號
        - 台股代號（純數字 4-6 位）自動加 .TW
        - 其他保持原樣
        """
        symbol = symbol.strip().upper()
        
        # 如果已經有後綴，不處理
        if '.' in symbol or symbol.startswith('^'):
            return symbol
        
        # 檢查是否為加密貨幣
        if symbol in SUPPORTED_CRYPTO:
            return symbol
        
        # 台股代號：4-6 位純數字
        if symbol.isdigit() and 4 <= len(symbol) <= 6:
            return f"{symbol}.TW"
        
        return symbol
    
    def _get_asset_type(self, symbol: str) -> str:
        """判斷資產類型"""
        symbol_upper = symbol.upper()
        
        # 先檢查原始代號是否為加密貨幣
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
        """取得時間週期對應的天數"""
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
        days: int = 3650,  # 預設抓 10 年
    ) -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
        """
        抓取價格資料
        
        Returns:
            (DataFrame, info_dict) 或 (None, None)
        """
        asset_type = self._get_asset_type(symbol)
        
        try:
            if asset_type == "crypto":
                # 加密貨幣用 CoinGecko
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
                # 股票/指數/ETF 用 Yahoo Finance
                period = "10y" if days >= 3650 else ("5y" if days >= 1825 else "1y")
                df = yahoo_finance.get_stock_history(symbol, period=period)
                
                # 如果 .TW 找不到，嘗試 .TWO (上櫃股票)
                if (df is None or df.empty) and symbol.endswith('.TW'):
                    two_symbol = symbol.replace('.TW', '.TWO')
                    logger.info(f"{symbol} 找不到，嘗試上櫃股票: {two_symbol}")
                    df = yahoo_finance.get_stock_history(two_symbol, period=period)
                    if df is not None and not df.empty:
                        symbol = two_symbol
                        logger.info(f"成功找到上櫃股票: {two_symbol}")
                
                info = yahoo_finance.get_stock_info(symbol)
                
                # 取得現價（用原始收盤價）
                current_price = None
                if df is not None and not df.empty:
                    current_price = float(df['close'].iloc[-1])
                
                if info:
                    info_dict = {
                        "name": info.get("name", symbol),
                        "type": asset_type,
                        "current_price": current_price or info.get("current_price"),
                        "symbol": symbol,  # 可能已經改成 .TWO
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
            logger.error(f"抓取 {symbol} 資料失敗: {e}")
            return None, None
    
    def _calculate_cagr_with_dividends(
        self,
        symbol: str,
        df: pd.DataFrame,
        years: int,
    ) -> Optional[float]:
        """
        計算含配息調整的 CAGR
        
        使用 adj_close（分割調整）+ 配息還原
        這和股票查詢頁面的計算方式一致
        """
        if df is None or df.empty:
            return None
        
        try:
            # 確保有 date 欄位
            if 'date' not in df.columns:
                df = df.reset_index()
                if 'Date' in df.columns:
                    df = df.rename(columns={'Date': 'date'})
            
            df['date'] = pd.to_datetime(df['date']).dt.date
            df = df.sort_values('date').reset_index(drop=True)
            
            current_date = df['date'].iloc[-1]
            target_date = current_date - timedelta(days=years * 365)
            
            # 找到目標日期之前的資料
            past_df = df[df['date'] <= target_date]
            
            if past_df.empty or len(past_df) < 10:
                return None
            
            # 優先使用 adj_close，沒有則用 close
            price_col = 'adj_close' if 'adj_close' in df.columns else 'close'
            
            start_row = past_df.iloc[-1]
            start_price = float(start_row[price_col])
            start_date = start_row['date']
            
            current_price = float(df.iloc[-1][price_col])
            
            if start_price <= 0:
                return None
            
            # 取得配息資料並調整
            try:
                dividends_df = yahoo_finance.get_dividends(symbol, period=f"{years + 1}y")
                
                if dividends_df is not None and not dividends_df.empty:
                    # 建立含配息調整的價格序列
                    df_adj = df.copy()
                    df_adj['adj_with_div'] = df_adj[price_col].astype(float)
                    
                    date_to_idx = {row['date']: idx for idx, row in df_adj.iterrows()}
                    
                    # 篩選在計算範圍內的配息
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
                    
                    # 從最新到最舊處理配息（配息還原調整）
                    for div_date, div_amount in sorted(dividends.items(), reverse=True):
                        if div_date in date_to_idx:
                            ex_idx = date_to_idx[div_date]
                            if ex_idx > 0:
                                prev_price = df_adj.loc[ex_idx - 1, 'adj_with_div']
                                if prev_price > div_amount and div_amount > 0:
                                    adjustment_factor = prev_price / (prev_price - div_amount)
                                    df_adj.loc[:ex_idx-1, 'adj_with_div'] = df_adj.loc[:ex_idx-1, 'adj_with_div'] / adjustment_factor
                    
                    # 使用調整後的價格計算
                    start_price = float(df_adj[df_adj['date'] <= target_date].iloc[-1]['adj_with_div'])
                    current_price = float(df_adj.iloc[-1]['adj_with_div'])
                    
                    logger.debug(f"{symbol} 配息調整: 找到 {len(dividends)} 筆配息")
                    
            except Exception as e:
                logger.warning(f"{symbol} 配息調整失敗，使用基本計算: {e}")
            
            # 實際年數（更精確）
            actual_days = (current_date - start_date).days
            actual_years = actual_days / 365.25
            
            if actual_years < 0.5:
                return None
            
            # CAGR 公式
            cagr = (current_price / start_price) ** (1 / actual_years) - 1
            
            # 檢查有效性
            if math.isnan(cagr) or math.isinf(cagr):
                return None
            
            return round(cagr * 100, 2)
            
        except Exception as e:
            logger.error(f"計算 {symbol} CAGR 失敗: {e}")
            return None
    
    def _calculate_custom_cagr(
        self,
        df: pd.DataFrame,
        start_date: date,
        end_date: date,
    ) -> Optional[float]:
        """計算自訂區間的 CAGR"""
        if df is None or df.empty:
            return None
        
        try:
            # 確保日期欄位
            if 'date' in df.columns:
                df = df.set_index('date')
            
            # 篩選日期範圍
            mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
            filtered_df = df[mask]
            
            if len(filtered_df) < 2:
                return None
            
            # 優先使用 adj_close
            price_col = 'adj_close' if 'adj_close' in filtered_df.columns else 'close'
            
            start_price = float(filtered_df[price_col].iloc[0])
            end_price = float(filtered_df[price_col].iloc[-1])
            
            # 計算年數
            days = (end_date - start_date).days
            years = days / 365.0
            
            if years <= 0 or start_price <= 0:
                return None
            
            # CAGR 公式
            cagr = (end_price / start_price) ** (1 / years) - 1
            return round(cagr * 100, 2)
            
        except Exception as e:
            logger.error(f"計算自訂 CAGR 失敗: {e}")
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
        比較多個標的的年化報酬率
        
        Args:
            symbols: 標的代號列表 (最多 5 個)
            periods: 時間週期 ["1y", "3y", "5y", "10y"]
            custom_range: 自訂區間 {"start": "2020-01-01", "end": "2024-12-31"}
            benchmark: 基準指數
            sort_by: 排序依據
            sort_order: 排序方向 "asc" / "desc"
            
        Returns:
            比較結果
        """
        # 驗證
        if not symbols:
            return {"success": False, "error": "請至少選擇一個標的"}
        
        if len(symbols) > self.max_symbols:
            return {"success": False, "error": f"最多只能比較 {self.max_symbols} 個標的"}
        
        if periods is None:
            periods = ["1y", "3y", "5y"]
        
        # 正規化代號（處理台股等）
        symbols = [self._normalize_symbol(s) for s in symbols]
        logger.info(f"標準化後的代號: {symbols}")
        
        # 計算需要的天數
        max_days = 3650  # 10 年
        if custom_range:
            try:
                start_date = datetime.strptime(custom_range["start"], "%Y-%m-%d").date()
                end_date = datetime.strptime(custom_range["end"], "%Y-%m-%d").date()
                custom_days = (date.today() - start_date).days
                max_days = max(max_days, custom_days)
            except (ValueError, KeyError):
                custom_range = None
        
        results = []
        
        # 處理每個標的
        for symbol in symbols:
            df, info = await self._fetch_price_data(symbol, max_days)
            
            # 如果有 symbol 更新（例如 .TW -> .TWO），使用更新後的
            actual_symbol = info.get("symbol", symbol) if info else symbol
            
            if df is None or info is None:
                results.append({
                    "symbol": actual_symbol,
                    "name": actual_symbol,
                    "type": self._get_asset_type(actual_symbol),
                    "current_price": None,
                    "cagr": {p: None for p in periods},
                    "error": "無法取得資料"
                })
                continue
            
            # 計算各週期 CAGR（使用含配息的計算）
            cagr_results = {}
            for period in periods:
                period_years = {"1y": 1, "3y": 3, "5y": 5, "10y": 10}.get(period)
                if period_years:
                    cagr_results[period] = self._calculate_cagr_with_dividends(
                        actual_symbol, df, period_years
                    )
            
            # 自訂區間
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
        
        # 計算基準指數
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
                
                # 計算 vs benchmark
                for result in results:
                    result["vs_benchmark"] = {}
                    for period in periods:
                        result_cagr = result["cagr"].get(period)
                        bench_cagr = benchmark_cagr.get(period)
                        if result_cagr is not None and bench_cagr is not None:
                            result["vs_benchmark"][period] = round(result_cagr - bench_cagr, 2)
                        else:
                            result["vs_benchmark"][period] = None
        
        # 排序
        def get_sort_value(item):
            val = item.get("cagr", {}).get(sort_by)
            return val if val is not None else float('-inf')
        
        results.sort(key=get_sort_value, reverse=(sort_order == "desc"))
        
        # 加入排名
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
            "note": "CAGR 已包含分割調整及配息再投入效果"
        }
    
    def get_presets(self) -> List[Dict[str, Any]]:
        """取得預設組合列表"""
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
        """取得預設組合詳情"""
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
    """比較組合 CRUD 操作"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_comparisons(self, user_id: int) -> List[Comparison]:
        """取得用戶的比較組合"""
        result = await self.db.execute(
            select(Comparison)
            .where(Comparison.user_id == user_id)
            .order_by(Comparison.updated_at.desc())
        )
        return result.scalars().all()
    
    async def get_comparison_by_id(self, comparison_id: int, user_id: int) -> Optional[Comparison]:
        """取得單一比較組合"""
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
        """建立比較組合"""
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
        """更新比較組合"""
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
        """刪除比較組合"""
        await self.db.delete(comparison)
        await self.db.commit()
        return True
    
    async def count_user_comparisons(self, user_id: int) -> int:
        """計算用戶的比較組合數量"""
        result = await self.db.execute(
            select(Comparison)
            .where(Comparison.user_id == user_id)
        )
        return len(result.scalars().all())


# 單例
compare_service = CompareService()
