"""
分析快取 Model
用於快取耗時的計算結果

V1.05 新增：
1. StockDetailCache - 股票詳情快取（減少 Yahoo API 調用）
2. IndicatorCache - 技術指標快取（預計算）
3. ChartCache - 圖表快取（減少 matplotlib CPU）
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, Numeric, JSON, LargeBinary
from sqlalchemy.sql import func
from app.database import Base


class StockDetailCache(Base):
    """
    股票詳情快取
    - 快取 Yahoo Finance 的股票資訊
    - 有效期：交易時段 5 分鐘，非交易時段 1 小時
    """
    __tablename__ = "stock_detail_cache"
    
    symbol = Column(String(20), primary_key=True)
    name = Column(String(100))
    
    # 價格資訊
    price = Column(Numeric(12, 4))
    prev_close = Column(Numeric(12, 4))
    open_price = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    volume = Column(String(50))
    
    # 公司資訊
    market_cap = Column(String(50))
    pe_ratio = Column(Numeric(12, 4))
    dividend_yield = Column(Numeric(8, 4))
    fifty_two_week_high = Column(Numeric(12, 4))
    fifty_two_week_low = Column(Numeric(12, 4))
    
    # 完整 JSON（備用）
    raw_data = Column(JSON)
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": float(self.price) if self.price else None,
            "prev_close": float(self.prev_close) if self.prev_close else None,
            "open": float(self.open_price) if self.open_price else None,
            "high": float(self.high) if self.high else None,
            "low": float(self.low) if self.low else None,
            "volume": self.volume,
            "market_cap": self.market_cap,
            "pe_ratio": float(self.pe_ratio) if self.pe_ratio else None,
            "dividend_yield": float(self.dividend_yield) if self.dividend_yield else None,
            "52_week_high": float(self.fifty_two_week_high) if self.fifty_two_week_high else None,
            "52_week_low": float(self.fifty_two_week_low) if self.fifty_two_week_low else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class IndicatorCache(Base):
    """
    技術指標快取
    - 預計算追蹤清單股票的技術指標
    - 排程每日更新
    """
    __tablename__ = "indicator_cache"
    
    symbol = Column(String(20), primary_key=True)
    
    # 價格
    price = Column(Numeric(12, 4))
    change_pct = Column(Numeric(8, 4))
    
    # MA 指標
    ma5 = Column(Numeric(12, 4))
    ma10 = Column(Numeric(12, 4))
    ma20 = Column(Numeric(12, 4))
    ma60 = Column(Numeric(12, 4))
    ma120 = Column(Numeric(12, 4))
    ma240 = Column(Numeric(12, 4))
    
    # RSI
    rsi = Column(Numeric(8, 4))
    
    # MACD
    macd_dif = Column(Numeric(12, 6))
    macd_dem = Column(Numeric(12, 6))
    macd_histogram = Column(Numeric(12, 6))
    
    # KD
    k_value = Column(Numeric(8, 4))
    d_value = Column(Numeric(8, 4))
    
    # 布林通道
    bb_upper = Column(Numeric(12, 4))
    bb_middle = Column(Numeric(12, 4))
    bb_lower = Column(Numeric(12, 4))
    
    # OBV
    obv = Column(Numeric(20, 0))
    
    # 綜合評分
    score = Column(Integer)
    trend = Column(String(20))  # bullish/bearish/neutral
    
    # 訊號 JSON
    signals = Column(JSON)
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            "symbol": self.symbol,
            "price": float(self.price) if self.price else None,
            "change_pct": float(self.change_pct) if self.change_pct else None,
            "ma5": float(self.ma5) if self.ma5 else None,
            "ma10": float(self.ma10) if self.ma10 else None,
            "ma20": float(self.ma20) if self.ma20 else None,
            "ma60": float(self.ma60) if self.ma60 else None,
            "ma120": float(self.ma120) if self.ma120 else None,
            "ma240": float(self.ma240) if self.ma240 else None,
            "rsi": float(self.rsi) if self.rsi else None,
            "macd_dif": float(self.macd_dif) if self.macd_dif else None,
            "macd_dem": float(self.macd_dem) if self.macd_dem else None,
            "macd_histogram": float(self.macd_histogram) if self.macd_histogram else None,
            "k_value": float(self.k_value) if self.k_value else None,
            "d_value": float(self.d_value) if self.d_value else None,
            "bb_upper": float(self.bb_upper) if self.bb_upper else None,
            "bb_middle": float(self.bb_middle) if self.bb_middle else None,
            "bb_lower": float(self.bb_lower) if self.bb_lower else None,
            "obv": int(self.obv) if self.obv else None,
            "score": self.score,
            "trend": self.trend,
            "signals": self.signals or [],
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChartCache(Base):
    """
    圖表快取
    - 儲存生成的 PNG 圖表
    - 有效期：1 小時
    """
    __tablename__ = "chart_cache"
    
    # 主鍵：symbol_days（如 AAPL_120）
    cache_key = Column(String(50), primary_key=True)
    symbol = Column(String(20), index=True)
    days = Column(Integer)
    
    # 圖表二進位資料
    chart_data = Column(LargeBinary)
    
    # 圖表資訊
    content_type = Column(String(50), default="image/png")
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
