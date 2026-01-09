"""
報酬率比較服務
計算並比較多個標的的年化報酬率 (CAGR)
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import pandas as pd

from app.models.comparison import Comparison
from app.data_sources.yahoo_finance import yahoo_finance
from app.data_sources.coingecko import coingecko, CRYPTO_MAP
from app.services.indicator_service import indicator_service

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
        if symbol_upper in SUPPORTED_CRYPTO:
            return "crypto"
        elif symbol_upper.startswith("^"):
            return "index"
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
            else:
                # 股票/指數/ETF 用 Yahoo Finance
                period = "10y" if days >= 3650 else ("5y" if days >= 1825 else "1y")
                df = yahoo_finance.get_stock_history(symbol, period=period)
                info = yahoo_finance.get_stock_info(symbol)
                if info:
                    info_dict = {
                        "name": info.get("name", symbol),
                        "type": asset_type,
                        "current_price": info.get("current_price"),
                    }
                else:
                    info_dict = {"name": symbol, "type": asset_type, "current_price": None}
            
            return df, info_dict
            
        except Exception as e:
            logger.error(f"抓取 {symbol} 資料失敗: {e}")
            return None, None
    
    def _calculate_cagr_for_period(
        self,
        df: pd.DataFrame,
        period: str,
    ) -> Optional[float]:
        """計算特定時間週期的 CAGR"""
        if df is None or df.empty:
            return None
        
        period_years = {
            "1y": 1,
            "3y": 3,
            "5y": 5,
            "10y": 10,
        }
        
        years = period_years.get(period)
        if years is None:
            return None
        
        return indicator_service.calculate_cagr(df, years)
    
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
            
            start_price = float(filtered_df['close'].iloc[0])
            end_price = float(filtered_df['close'].iloc[-1])
            
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
            periods = ["1y", "3y", "5y", "10y"]
        
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
            
            if df is None or info is None:
                results.append({
                    "symbol": symbol,
                    "name": symbol,
                    "type": self._get_asset_type(symbol),
                    "current_price": None,
                    "cagr": {p: None for p in periods},
                    "error": "無法取得資料"
                })
                continue
            
            # 計算各週期 CAGR
            cagr_values = {}
            for period in periods:
                cagr_values[period] = self._calculate_cagr_for_period(df, period)
            
            # 自訂區間
            if custom_range:
                cagr_values["custom"] = self._calculate_custom_cagr(df, start_date, end_date)
            
            results.append({
                "symbol": symbol,
                "name": info.get("name", symbol),
                "type": info.get("type", "stock"),
                "current_price": info.get("current_price"),
                "cagr": cagr_values,
            })
        
        # 取得基準指數資料
        benchmark_data = None
        if benchmark and benchmark.strip():
            bench_df, bench_info = await self._fetch_price_data(benchmark, max_days)
            if bench_df is not None:
                bench_cagr = {}
                for period in periods:
                    bench_cagr[period] = self._calculate_cagr_for_period(bench_df, period)
                if custom_range:
                    bench_cagr["custom"] = self._calculate_custom_cagr(bench_df, start_date, end_date)
                
                benchmark_data = {
                    "symbol": benchmark,
                    "name": bench_info.get("name", benchmark) if bench_info else benchmark,
                    "cagr": bench_cagr,
                }
                
                # 計算 vs benchmark
                for result in results:
                    vs_benchmark = {}
                    for period in periods:
                        result_cagr = result["cagr"].get(period)
                        bench_cagr_val = bench_cagr.get(period)
                        if result_cagr is not None and bench_cagr_val is not None:
                            diff = result_cagr - bench_cagr_val
                            vs_benchmark[period] = round(diff, 2)
                        else:
                            vs_benchmark[period] = None
                    if custom_range and "custom" in result["cagr"]:
                        result_custom = result["cagr"].get("custom")
                        bench_custom = bench_cagr.get("custom")
                        if result_custom is not None and bench_custom is not None:
                            vs_benchmark["custom"] = round(result_custom - bench_custom, 2)
                    result["vs_benchmark"] = vs_benchmark
        
        # 排序
        def sort_key(item):
            val = item["cagr"].get(sort_by)
            if val is None:
                return float('-inf') if sort_order == "desc" else float('inf')
            return val
        
        results.sort(key=sort_key, reverse=(sort_order == "desc"))
        
        # 加上排名
        for i, result in enumerate(results, 1):
            result["rank"] = i
        
        return {
            "success": True,
            "comparison": results,
            "benchmark": benchmark_data,
            "periods": periods,
            "custom_range": custom_range,
            "sort_by": sort_by,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
    
    def get_presets(self) -> List[Dict[str, Any]]:
        """取得所有預設組合"""
        return [
            {
                "id": key,
                "name": value["name"],
                "description": value.get("description", ""),
                "count": len(value["symbols"]),
            }
            for key, value in PRESET_GROUPS.items()
        ]
    
    def get_preset_detail(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """取得預設組合詳情"""
        preset = PRESET_GROUPS.get(preset_id)
        if not preset:
            return None
        
        return {
            "id": preset_id,
            "name": preset["name"],
            "description": preset.get("description", ""),
            "symbols": preset["symbols"],
        }
    
    def get_benchmark_options(self) -> Dict[str, str]:
        """取得基準指數選項"""
        return BENCHMARK_OPTIONS


class ComparisonCRUD:
    """儲存的比較組合 CRUD 操作"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_comparisons(self, user_id: int) -> List[Comparison]:
        """取得用戶的所有比較組合"""
        stmt = select(Comparison).where(
            Comparison.user_id == user_id
        ).order_by(Comparison.updated_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_comparison(self, comparison_id: int, user_id: int) -> Optional[Comparison]:
        """取得單一比較組合"""
        stmt = select(Comparison).where(
            and_(
                Comparison.id == comparison_id,
                Comparison.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_comparison(
        self,
        user_id: int,
        name: str,
        symbols: List[str],
        benchmark: str = "^GSPC",
    ) -> Comparison:
        """建立新的比較組合"""
        comparison = Comparison(
            user_id=user_id,
            name=name,
            benchmark=benchmark,
        )
        comparison.symbols = symbols  # 使用 property setter
        
        self.db.add(comparison)
        await self.db.commit()
        await self.db.refresh(comparison)
        
        logger.info(f"建立比較組合: user_id={user_id}, name={name}, symbols={symbols}")
        return comparison
    
    async def update_comparison(
        self,
        comparison_id: int,
        user_id: int,
        name: str = None,
        symbols: List[str] = None,
        benchmark: str = None,
    ) -> Optional[Comparison]:
        """更新比較組合"""
        comparison = await self.get_comparison(comparison_id, user_id)
        if not comparison:
            return None
        
        if name is not None:
            comparison.name = name
        if symbols is not None:
            comparison.symbols = symbols
        if benchmark is not None:
            comparison.benchmark = benchmark
        
        await self.db.commit()
        await self.db.refresh(comparison)
        
        logger.info(f"更新比較組合: id={comparison_id}")
        return comparison
    
    async def delete_comparison(self, comparison_id: int, user_id: int) -> bool:
        """刪除比較組合"""
        comparison = await self.get_comparison(comparison_id, user_id)
        if not comparison:
            return False
        
        await self.db.delete(comparison)
        await self.db.commit()
        
        logger.info(f"刪除比較組合: id={comparison_id}")
        return True


# 建立預設實例
compare_service = CompareService()
