"""
股票價格快取 Model
用於追蹤清單的即時價格顯示（全系統共用）

更新：加入 MA20 欄位支援排序功能
"""
from sqlalchemy import Column, String, Numeric, BigInteger, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class StockPriceCache(Base):
    """
    股票即時價格快取
    
    - 全系統共用，不分用戶
    - 每 10 分鐘由排程批次更新
    - 追蹤清單頁面直接從這裡讀取
    """
    
    __tablename__ = "stock_price_cache"
    
    # 主鍵：股票代號（如 0050.TW, AAPL）
    symbol = Column(String(20), primary_key=True)
    
    # 股票名稱
    name = Column(String(100))
    
    # 價格資訊
    price = Column(Numeric(12, 4))           # 最新價格
    prev_close = Column(Numeric(12, 4))      # 前收盤價（用於計算漲跌）
    change = Column(Numeric(12, 4))          # 漲跌金額
    change_pct = Column(Numeric(8, 4))       # 漲跌幅 %
    
    # 🆕 技術指標（用於排序）
    ma20 = Column(Numeric(12, 4))            # 20日均線
    
    # 成交量
    volume = Column(BigInteger)
    
    # 資產類型：stock / crypto
    asset_type = Column(String(10), default="stock")
    
    # 更新時間
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_cache_asset_type', 'asset_type'),
        Index('idx_cache_updated', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<StockPriceCache(symbol={self.symbol}, price={self.price}, change_pct={self.change_pct}%)>"
    
    def to_dict(self):
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": float(self.price) if self.price else None,
            "prev_close": float(self.prev_close) if self.prev_close else None,
            "change": float(self.change) if self.change else None,
            "change_pct": float(self.change_pct) if self.change_pct else None,
            "ma20": float(self.ma20) if self.ma20 else None,
            "volume": self.volume,
            "asset_type": self.asset_type,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
