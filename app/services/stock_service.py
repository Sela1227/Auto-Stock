"""
股票服務
整合資料抓取、快取和技術指標計算
"""
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import logging

from app.models.stock_price import StockPrice
from app.data_sources.yahoo_finance import yahoo_finance
from app.services.indicator_service import indicator_service, TrendDirection
from app.config import settings

logger = logging.getLogger(__name__)


class StockService:
    """股票服務"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """
        檢查快取是否有效
        
        規則：
        1. 有今日資料
        2. 或是週末/假日時有最近交易日資料
        """
        today = date.today()
        
        # 查詢最新資料
        stmt = (
            select(StockPrice)
            .where(StockPrice.symbol == symbol.upper())
            .order_by(StockPrice.date.desc())
            .limit(1)
        )
        result = self.db.execute(stmt).scalar_one_or_none()
        
        if not result:
            return False
        
        # 如果有今日資料，快取有效
        if result.date == today:
            return True
        
        # 檢查是否為週末
        if today.weekday() >= 5:  # 週六=5, 週日=6
            # 週末時，只要有週五的資料就算有效
            friday = today - timedelta(days=(today.weekday() - 4))
            if result.date >= friday:
                return True
        
        # 檢查更新時間是否在快取時間內
        if result.updated_at:
            cache_hours = settings.STOCK_DATA_CACHE_HOURS
            cache_deadline = datetime.now() - timedelta(hours=cache_hours)
            if result.updated_at > cache_deadline:
                return True
        
        return False
    
    def _save_prices_to_db(self, df: pd.DataFrame) -> int:
        """
        儲存價格資料到資料庫
        
        Returns:
            儲存的筆數
        """
        if df is None or df.empty:
            return 0
        
        count = 0
        for _, row in df.iterrows():
            # 檢查是否已存在
            stmt = select(StockPrice).where(
                and_(
                    StockPrice.symbol == row["symbol"],
                    StockPrice.date == row["date"],
                )
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if existing:
                # 更新現有資料
                existing.open = row["open"]
                existing.high = row["high"]
                existing.low = row["low"]
                existing.close = row["close"]
                existing.volume = row["volume"]
            else:
                # 新增資料
                price = StockPrice(
                    symbol=row["symbol"],
                    date=row["date"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                )
                self.db.add(price)
                count += 1
        
        self.db.commit()
        return count
    
    def _load_prices_from_db(
        self,
        symbol: str,
        days: int = 365,
    ) -> Optional[pd.DataFrame]:
        """從資料庫載入價格資料"""
        start_date = date.today() - timedelta(days=days)
        
        stmt = (
            select(StockPrice)
            .where(
                and_(
                    StockPrice.symbol == symbol.upper(),
                    StockPrice.date >= start_date,
                )
            )
            .order_by(StockPrice.date)
        )
        results = self.db.execute(stmt).scalars().all()
        
        if not results:
            return None
        
        data = []
        for r in results:
            data.append({
                "symbol": r.symbol,
                "date": r.date,
                "open": float(r.open) if r.open else None,
                "high": float(r.high) if r.high else None,
                "low": float(r.low) if r.low else None,
                "close": float(r.close) if r.close else None,
                "volume": r.volume,
            })
        
        return pd.DataFrame(data)
    
    def fetch_and_cache_stock(self, symbol: str, period: str = "1y") -> bool:
        """
        抓取股票資料並快取
        
        Returns:
            是否成功
        """
        df = yahoo_finance.get_stock_history(symbol, period=period)
        if df is None:
            return False
        
        self._save_prices_to_db(df)
        return True
    
    def get_stock_data(
        self,
        symbol: str,
        force_refresh: bool = False,
    ) -> Optional[pd.DataFrame]:
        """
        取得股票資料（優先使用快取）
        
        Args:
            symbol: 股票代號
            force_refresh: 是否強制更新
            
        Returns:
            包含價格和技術指標的 DataFrame
        """
        symbol = symbol.upper()
        
        # 檢查快取
        if not force_refresh and self._is_cache_valid(symbol):
            logger.info(f"使用快取資料: {symbol}")
            df = self._load_prices_from_db(symbol)
        else:
            # 從 Yahoo Finance 抓取
            logger.info(f"從 Yahoo Finance 抓取: {symbol}")
            if not self.fetch_and_cache_stock(symbol):
                # 抓取失敗，嘗試使用舊的快取
                df = self._load_prices_from_db(symbol)
                if df is None:
                    return None
            else:
                df = self._load_prices_from_db(symbol)
        
        if df is None or df.empty:
            return None
        
        # 計算技術指標
        df = indicator_service.calculate_all_indicators(df)
        
        return df
    
    def get_stock_analysis(
        self,
        symbol: str,
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        取得股票完整分析報告
        
        Returns:
            分析報告字典
        """
        symbol = symbol.upper()
        
        # 取得資料
        df = self.get_stock_data(symbol, force_refresh)
        if df is None:
            return None
        
        # 取得股票基本資訊
        info = yahoo_finance.get_stock_info(symbol)
        
        # 最新價格資料
        latest = df.iloc[-1]
        price = float(latest["close"])
        
        # 計算漲跌幅
        changes = self._calculate_changes(df)
        
        # 技術指標
        indicators = self._get_indicators_summary(df, latest)
        
        # 訊號
        signals = indicator_service.get_all_signals(df)
        
        # 評分
        score = indicator_service.calculate_score(df)
        
        # 成交量
        volume_info = self._get_volume_info(df, latest)
        
        return {
            "symbol": symbol,
            "name": info.get("name", "N/A") if info else "N/A",
            "asset_type": "stock",
            "price": {
                "current": price,
                "high_52w": info.get("fifty_two_week_high") if info else None,
                "low_52w": info.get("fifty_two_week_low") if info else None,
                "from_high_pct": self._calc_pct_from_high(price, info),
                "from_low_pct": self._calc_pct_from_low(price, info),
            },
            "change": changes,
            "volume": volume_info,
            "indicators": indicators,
            "signals": [
                {
                    "type": s.type.value,
                    "indicator": s.indicator,
                    "description": s.description,
                }
                for s in signals
            ],
            "score": score,
            "updated_at": datetime.now().isoformat(),
        }
    
    def _calculate_changes(self, df: pd.DataFrame) -> Dict[str, float]:
        """計算各時間段漲跌幅"""
        latest_close = df["close"].iloc[-1]
        
        def calc_change(days: int) -> Optional[float]:
            if len(df) <= days:
                return None
            old_close = df["close"].iloc[-(days + 1)]
            return round((latest_close - old_close) / old_close * 100, 2)
        
        return {
            "day": calc_change(1),
            "week": calc_change(5),
            "month": calc_change(20),
            "quarter": calc_change(60),
            "year": calc_change(250) if len(df) > 250 else None,
        }
    
    def _get_indicators_summary(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
    ) -> Dict[str, Any]:
        """取得指標摘要"""
        price = float(latest["close"])
        
        # MA
        ma_short = latest.get(f"ma{settings.MA_SHORT}")
        ma_mid = latest.get(f"ma{settings.MA_MID}")
        ma_long = latest.get(f"ma{settings.MA_LONG}")
        
        alignment, _ = indicator_service.get_ma_alignment(df)
        
        ma_info = {
            f"ma{settings.MA_SHORT}": round(ma_short, 2) if not pd.isna(ma_short) else None,
            f"ma{settings.MA_MID}": round(ma_mid, 2) if not pd.isna(ma_mid) else None,
            f"ma{settings.MA_LONG}": round(ma_long, 2) if not pd.isna(ma_long) else None,
            "alignment": alignment.value,
            f"price_vs_ma{settings.MA_SHORT}": "above" if price > ma_short else "below" if not pd.isna(ma_short) else None,
            f"price_vs_ma{settings.MA_MID}": "above" if price > ma_mid else "below" if not pd.isna(ma_mid) else None,
            f"price_vs_ma{settings.MA_LONG}": "above" if price > ma_long else "below" if not pd.isna(ma_long) else None,
        }
        
        # RSI
        rsi = latest.get("rsi")
        rsi_status, _ = indicator_service.get_rsi_status(rsi)
        rsi_info = {
            "value": round(rsi, 2) if not pd.isna(rsi) else None,
            "status": rsi_status,
        }
        
        # MACD
        macd_dif = latest.get("macd_dif")
        macd_dea = latest.get("macd_dea")
        macd_hist = latest.get("macd_hist")
        macd_info = {
            "dif": round(macd_dif, 4) if not pd.isna(macd_dif) else None,
            "dea": round(macd_dea, 4) if not pd.isna(macd_dea) else None,
            "histogram": round(macd_hist, 4) if not pd.isna(macd_hist) else None,
            "status": "bullish" if macd_hist and macd_hist > 0 else "bearish",
        }
        
        # KD
        kd_k = latest.get("kd_k")
        kd_d = latest.get("kd_d")
        kd_info = {
            "k": round(kd_k, 2) if not pd.isna(kd_k) else None,
            "d": round(kd_d, 2) if not pd.isna(kd_d) else None,
            "status": self._get_kd_status(kd_k),
        }
        
        # Bollinger
        bb_upper = latest.get("bb_upper")
        bb_middle = latest.get("bb_middle")
        bb_lower = latest.get("bb_lower")
        bb_info = {
            "upper": round(bb_upper, 2) if not pd.isna(bb_upper) else None,
            "middle": round(bb_middle, 2) if not pd.isna(bb_middle) else None,
            "lower": round(bb_lower, 2) if not pd.isna(bb_lower) else None,
            "position": indicator_service.get_bollinger_position(price, bb_upper, bb_middle, bb_lower),
        }
        
        # OBV
        obv_trend = indicator_service.get_obv_trend(df)
        obv_info = {
            "trend": obv_trend,
        }
        
        return {
            "ma": ma_info,
            "rsi": rsi_info,
            "macd": macd_info,
            "kd": kd_info,
            "bollinger": bb_info,
            "obv": obv_info,
        }
    
    def _get_kd_status(self, k_value: float) -> str:
        """取得 KD 狀態"""
        if pd.isna(k_value):
            return "unknown"
        if k_value > 80:
            return "overbought"
        elif k_value < 20:
            return "oversold"
        elif k_value > 50:
            return "neutral_high"
        else:
            return "neutral_low"
    
    def _get_volume_info(
        self,
        df: pd.DataFrame,
        latest: pd.Series,
    ) -> Dict[str, Any]:
        """取得成交量資訊"""
        today_vol = latest.get("volume", 0)
        avg_vol = latest.get("volume_ma20")
        vol_ratio = latest.get("volume_ratio")
        
        return {
            "today": int(today_vol) if today_vol else 0,
            "avg_20d": int(avg_vol) if not pd.isna(avg_vol) else None,
            "ratio": round(vol_ratio, 2) if not pd.isna(vol_ratio) else None,
        }
    
    def _calc_pct_from_high(self, price: float, info: Optional[Dict]) -> Optional[float]:
        """計算距離 52 週高點的跌幅"""
        if not info or not info.get("fifty_two_week_high"):
            return None
        high = info["fifty_two_week_high"]
        return round((price - high) / high * 100, 2)
    
    def _calc_pct_from_low(self, price: float, info: Optional[Dict]) -> Optional[float]:
        """計算距離 52 週低點的漲幅"""
        if not info or not info.get("fifty_two_week_low"):
            return None
        low = info["fifty_two_week_low"]
        return round((price - low) / low * 100, 2)
    
    def search_stocks(self, query: str) -> List[Dict[str, str]]:
        """
        搜尋股票（簡單實作，直接驗證代號）
        
        Returns:
            符合的股票列表
        """
        symbol = query.upper().strip()
        
        if yahoo_finance.validate_symbol(symbol):
            info = yahoo_finance.get_stock_info(symbol)
            if info:
                return [{
                    "symbol": info["symbol"],
                    "name": info.get("name", "N/A"),
                }]
        
        return []
