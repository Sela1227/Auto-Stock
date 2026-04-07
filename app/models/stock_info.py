"""
è‚¡ç¥¨åŸºæœ¬è³‡è¨Šè¡¨
=============
å„²å­˜è‚¡ç¥¨çš„åŸºæœ¬è³‡è¨Šï¼Œç”¨æ–¼æœå°‹å’Œé¡¯ç¤º

P1 åŠŸèƒ½ï¼šstock_info ç¨®å­è¡¨
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Index, Text
from datetime import datetime

from app.database import Base


class StockInfo(Base):
    """è‚¡ç¥¨åŸºæœ¬è³‡è¨Šè¡¨"""
    
    __tablename__ = "stock_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # åŸºæœ¬è³‡è¨Š
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100))                    # è‚¡ç¥¨åç¨±
    name_zh = Column(String(100))                 # ä¸­æ–‡åç¨±
    
    # å¸‚å ´åˆ†é¡ž
    market = Column(String(10), default="us")     # us, tw, crypto
    exchange = Column(String(20))                 # NYSE, NASDAQ, TWSE, TPEx
    sector = Column(String(50))                   # ç”¢æ¥­é¡žåˆ¥
    industry = Column(String(50))                 # ç”¢æ¥­ç´°åˆ†
    
    # åŸºæœ¬æ•¸æ“š
    market_cap = Column(Float)                    # å¸‚å€¼
    pe_ratio = Column(Float)                      # æœ¬ç›Šæ¯”
    dividend_yield = Column(Float)                # æ®–åˆ©çŽ‡
    
    # æè¿°
    description = Column(Text)                    # å…¬å¸æè¿°
    website = Column(String(200))                 # å®˜ç¶²
    logo_url = Column(String(300))                # Logo URL
    
    # ç‹€æ…‹
    is_active = Column(Boolean, default=True)     # æ˜¯å¦æœ‰æ•ˆ
    is_popular = Column(Boolean, default=False)   # æ˜¯å¦ç†±é–€
    
    # æ™‚é–“æˆ³
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ç´¢å¼•
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
# é è¨­ç¨®å­è³‡æ–™
# ============================================================

DEFAULT_STOCK_INFO = [
    # ç¾Žè‚¡ - ç§‘æŠ€å·¨é ­
    {"symbol": "AAPL", "name": "Apple Inc.", "name_zh": "è˜‹æžœ", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "name_zh": "å¾®è»Ÿ", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "name_zh": "Google", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "name_zh": "äºžé¦¬éœ", "market": "us", "exchange": "NASDAQ", "sector": "Consumer Cyclical", "is_popular": True},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "name_zh": "è¼é”", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "META", "name": "Meta Platforms Inc.", "name_zh": "Meta", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "TSLA", "name": "Tesla Inc.", "name_zh": "ç‰¹æ–¯æ‹‰", "market": "us", "exchange": "NASDAQ", "sector": "Consumer Cyclical", "is_popular": True},
    
    # ç¾Žè‚¡ - é‡‘èž
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "name_zh": "æ‘©æ ¹å¤§é€š", "market": "us", "exchange": "NYSE", "sector": "Financial Services", "is_popular": True},
    {"symbol": "V", "name": "Visa Inc.", "name_zh": "Visa", "market": "us", "exchange": "NYSE", "sector": "Financial Services", "is_popular": True},
    {"symbol": "MA", "name": "Mastercard Inc.", "name_zh": "è¬äº‹é”å¡", "market": "us", "exchange": "NYSE", "sector": "Financial Services", "is_popular": True},
    
    # ç¾Žè‚¡ - åŠå°Žé«”
    {"symbol": "AMD", "name": "Advanced Micro Devices", "name_zh": "è¶…å¾®", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "INTC", "name": "Intel Corporation", "name_zh": "è‹±ç‰¹çˆ¾", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "name_zh": "åšé€š", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    
    # å°è‚¡ - åŠå°Žé«”
    {"symbol": "2330.TW", "name": "Taiwan Semiconductor", "name_zh": "å°ç©é›»", "market": "tw", "exchange": "TWSE", "sector": "åŠå°Žé«”", "is_popular": True},
    {"symbol": "2454.TW", "name": "MediaTek Inc.", "name_zh": "è¯ç™¼ç§‘", "market": "tw", "exchange": "TWSE", "sector": "åŠå°Žé«”", "is_popular": True},
    {"symbol": "2303.TW", "name": "United Microelectronics", "name_zh": "è¯é›»", "market": "tw", "exchange": "TWSE", "sector": "åŠå°Žé«”", "is_popular": True},
    {"symbol": "3711.TW", "name": "ASE Technology", "name_zh": "æ—¥æœˆå…‰æŠ•æŽ§", "market": "tw", "exchange": "TWSE", "sector": "åŠå°Žé«”", "is_popular": True},
    
    # å°è‚¡ - é›»å­ä»£å·¥
    {"symbol": "2317.TW", "name": "Hon Hai Precision", "name_zh": "é´»æµ·", "market": "tw", "exchange": "TWSE", "sector": "é›»å­", "is_popular": True},
    {"symbol": "2382.TW", "name": "Quanta Computer", "name_zh": "å»£é”", "market": "tw", "exchange": "TWSE", "sector": "é›»å­", "is_popular": True},
    {"symbol": "2357.TW", "name": "Asustek Computer", "name_zh": "è¯ç¢©", "market": "tw", "exchange": "TWSE", "sector": "é›»å­", "is_popular": True},
    
    # å°è‚¡ - é‡‘èž
    {"symbol": "2881.TW", "name": "Fubon Financial", "name_zh": "å¯Œé‚¦é‡‘", "market": "tw", "exchange": "TWSE", "sector": "é‡‘èž", "is_popular": True},
    {"symbol": "2882.TW", "name": "Cathay Financial", "name_zh": "åœ‹æ³°é‡‘", "market": "tw", "exchange": "TWSE", "sector": "é‡‘èž", "is_popular": True},
    {"symbol": "2884.TW", "name": "E.Sun Financial", "name_zh": "çŽ‰å±±é‡‘", "market": "tw", "exchange": "TWSE", "sector": "é‡‘èž", "is_popular": True},
    
    # å°è‚¡ - ETF
    {"symbol": "0050.TW", "name": "Yuanta Taiwan 50 ETF", "name_zh": "å…ƒå¤§å°ç£50", "market": "tw", "exchange": "TWSE", "sector": "ETF", "is_popular": True},
    {"symbol": "0056.TW", "name": "Yuanta High Dividend ETF", "name_zh": "å…ƒå¤§é«˜è‚¡æ¯", "market": "tw", "exchange": "TWSE", "sector": "ETF", "is_popular": True},
    {"symbol": "00878.TW", "name": "Cathay ESG High Dividend ETF", "name_zh": "åœ‹æ³°æ°¸çºŒé«˜è‚¡æ¯", "market": "tw", "exchange": "TWSE", "sector": "ETF", "is_popular": True},
    
    # åŠ å¯†è²¨å¹£
    {"symbol": "BTC", "name": "Bitcoin", "name_zh": "æ¯”ç‰¹å¹£", "market": "crypto", "exchange": "CoinGecko", "sector": "Cryptocurrency", "is_popular": True},
    {"symbol": "ETH", "name": "Ethereum", "name_zh": "ä»¥å¤ªåŠ", "market": "crypto", "exchange": "CoinGecko", "sector": "Cryptocurrency", "is_popular": True},
    {"symbol": "SOL", "name": "Solana", "name_zh": "ç´¢æ‹‰ç´", "market": "crypto", "exchange": "CoinGecko", "sector": "Cryptocurrency", "is_popular": True},
    
    # æŒ‡æ•¸
    {"symbol": "^GSPC", "name": "S&P 500", "name_zh": "æ¨™æ™®500", "market": "us", "exchange": "INDEX", "sector": "Index", "is_popular": True},
    {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "name_zh": "é“ç“Šå·¥æ¥­", "market": "us", "exchange": "INDEX", "sector": "Index", "is_popular": True},
    {"symbol": "^IXIC", "name": "NASDAQ Composite", "name_zh": "ç´æ–¯é”å…‹", "market": "us", "exchange": "INDEX", "sector": "Index", "is_popular": True},
    {"symbol": "^TWII", "name": "Taiwan Weighted Index", "name_zh": "å°ç£åŠ æ¬Š", "market": "tw", "exchange": "INDEX", "sector": "Index", "is_popular": True},
]