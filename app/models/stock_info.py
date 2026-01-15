"""
股票基本資訊種子表
==================
存儲股票的基本資訊，用於快速查詢和自動補全

P1 功能：stock_info 種子表
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Index, Text
from datetime import datetime

from app.database import Base


class StockInfo(Base):
    """股票基本資訊表"""
    
    __tablename__ = "stock_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本資訊
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100))                    # 股票名稱
    name_zh = Column(String(100))                 # 中文名稱
    
    # 市場分類
    market = Column(String(10), default="us")     # us, tw, crypto
    exchange = Column(String(20))                 # NYSE, NASDAQ, TWSE, TPEx
    sector = Column(String(50))                   # 產業類別
    industry = Column(String(50))                 # 產業細分
    
    # 基本數據
    market_cap = Column(Float)                    # 市值
    pe_ratio = Column(Float)                      # 本益比
    dividend_yield = Column(Float)                # 殖利率
    
    # 描述
    description = Column(Text)                    # 公司描述
    website = Column(String(200))                 # 官網
    logo_url = Column(String(300))                # Logo URL
    
    # 狀態
    is_active = Column(Boolean, default=True)     # 是否有效
    is_popular = Column(Boolean, default=False)   # 是否熱門
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_stock_info_market', 'market'),
        Index('idx_stock_info_sector', 'sector'),
        Index('idx_stock_info_popular', 'is_popular'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "name_zh": self.name_zh,
            "market": self.market,
            "exchange": self.exchange,
            "sector": self.sector,
            "industry": self.industry,
            "market_cap": self.market_cap,
            "pe_ratio": self.pe_ratio,
            "dividend_yield": self.dividend_yield,
            "description": self.description,
            "website": self.website,
            "logo_url": self.logo_url,
            "is_active": self.is_active,
            "is_popular": self.is_popular,
        }
    
    def __repr__(self):
        return f"<StockInfo {self.symbol}: {self.name}>"


# ============================================================
# 預設種子資料
# ============================================================

DEFAULT_STOCK_INFO = [
    # 美股 - 科技巨頭
    {"symbol": "AAPL", "name": "Apple Inc.", "name_zh": "蘋果", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "name_zh": "微軟", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "name_zh": "Google", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "name_zh": "亞馬遜", "market": "us", "exchange": "NASDAQ", "sector": "Consumer Cyclical", "is_popular": True},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "name_zh": "輝達", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "META", "name": "Meta Platforms Inc.", "name_zh": "Meta", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "TSLA", "name": "Tesla Inc.", "name_zh": "特斯拉", "market": "us", "exchange": "NASDAQ", "sector": "Consumer Cyclical", "is_popular": True},
    
    # 美股 - 金融
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "name_zh": "摩根大通", "market": "us", "exchange": "NYSE", "sector": "Financial Services", "is_popular": True},
    {"symbol": "V", "name": "Visa Inc.", "name_zh": "Visa", "market": "us", "exchange": "NYSE", "sector": "Financial Services", "is_popular": True},
    {"symbol": "MA", "name": "Mastercard Inc.", "name_zh": "萬事達卡", "market": "us", "exchange": "NYSE", "sector": "Financial Services", "is_popular": True},
    
    # 美股 - 半導體
    {"symbol": "AMD", "name": "Advanced Micro Devices", "name_zh": "超微", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "INTC", "name": "Intel Corporation", "name_zh": "英特爾", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "name_zh": "博通", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    
    # 台股 - 半導體
    {"symbol": "2330.TW", "name": "Taiwan Semiconductor", "name_zh": "台積電", "market": "tw", "exchange": "TWSE", "sector": "半導體", "is_popular": True},
    {"symbol": "2454.TW", "name": "MediaTek Inc.", "name_zh": "聯發科", "market": "tw", "exchange": "TWSE", "sector": "半導體", "is_popular": True},
    {"symbol": "2303.TW", "name": "United Microelectronics", "name_zh": "聯電", "market": "tw", "exchange": "TWSE", "sector": "半導體", "is_popular": True},
    {"symbol": "3711.TW", "name": "ASE Technology", "name_zh": "日月光投控", "market": "tw", "exchange": "TWSE", "sector": "半導體", "is_popular": True},
    
    # 台股 - 電子代工
    {"symbol": "2317.TW", "name": "Hon Hai Precision", "name_zh": "鴻海", "market": "tw", "exchange": "TWSE", "sector": "電子", "is_popular": True},
    {"symbol": "2382.TW", "name": "Quanta Computer", "name_zh": "廣達", "market": "tw", "exchange": "TWSE", "sector": "電子", "is_popular": True},
    {"symbol": "2357.TW", "name": "Asustek Computer", "name_zh": "華碩", "market": "tw", "exchange": "TWSE", "sector": "電子", "is_popular": True},
    
    # 台股 - 金融
    {"symbol": "2881.TW", "name": "Fubon Financial", "name_zh": "富邦金", "market": "tw", "exchange": "TWSE", "sector": "金融", "is_popular": True},
    {"symbol": "2882.TW", "name": "Cathay Financial", "name_zh": "國泰金", "market": "tw", "exchange": "TWSE", "sector": "金融", "is_popular": True},
    {"symbol": "2884.TW", "name": "E.Sun Financial", "name_zh": "玉山金", "market": "tw", "exchange": "TWSE", "sector": "金融", "is_popular": True},
    
    # 台股 - ETF
    {"symbol": "0050.TW", "name": "Yuanta Taiwan 50 ETF", "name_zh": "元大台灣50", "market": "tw", "exchange": "TWSE", "sector": "ETF", "is_popular": True},
    {"symbol": "0056.TW", "name": "Yuanta High Dividend ETF", "name_zh": "元大高股息", "market": "tw", "exchange": "TWSE", "sector": "ETF", "is_popular": True},
    {"symbol": "00878.TW", "name": "Cathay ESG High Dividend ETF", "name_zh": "國泰永續高股息", "market": "tw", "exchange": "TWSE", "sector": "ETF", "is_popular": True},
    
    # 加密貨幣
    {"symbol": "BTC", "name": "Bitcoin", "name_zh": "比特幣", "market": "crypto", "exchange": "CoinGecko", "sector": "Cryptocurrency", "is_popular": True},
    {"symbol": "ETH", "name": "Ethereum", "name_zh": "以太坊", "market": "crypto", "exchange": "CoinGecko", "sector": "Cryptocurrency", "is_popular": True},
    {"symbol": "SOL", "name": "Solana", "name_zh": "索拉納", "market": "crypto", "exchange": "CoinGecko", "sector": "Cryptocurrency", "is_popular": True},
    
    # 指數
    {"symbol": "^GSPC", "name": "S&P 500", "name_zh": "標普500", "market": "us", "exchange": "INDEX", "sector": "Index", "is_popular": True},
    {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "name_zh": "道瓊工業", "market": "us", "exchange": "INDEX", "sector": "Index", "is_popular": True},
    {"symbol": "^IXIC", "name": "NASDAQ Composite", "name_zh": "納斯達克", "market": "us", "exchange": "INDEX", "sector": "Index", "is_popular": True},
    {"symbol": "^TWII", "name": "Taiwan Weighted Index", "name_zh": "台灣加權", "market": "tw", "exchange": "INDEX", "sector": "Index", "is_popular": True},
]
