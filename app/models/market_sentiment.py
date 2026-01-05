"""
市場情緒指數資料模型
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class MarketSentiment(Base):
    """市場情緒指數"""
    
    __tablename__ = "market_sentiment"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    market = Column(String(10), nullable=False)  # stock / crypto
    value = Column(Integer)  # 0-100
    classification = Column(String(20))  # extreme_fear, fear, neutral, greed, extreme_greed
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_sentiment_market_date', 'market', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<MarketSentiment(market={self.market}, date={self.date}, value={self.value})>"
    
    @staticmethod
    def get_classification(value: int) -> str:
        """根據數值取得分類"""
        if value <= 25:
            return "extreme_fear"
        elif value <= 45:
            return "fear"
        elif value <= 55:
            return "neutral"
        elif value <= 75:
            return "greed"
        else:
            return "extreme_greed"
    
    @staticmethod
    def get_classification_zh(value: int) -> str:
        """根據數值取得中文分類"""
        if value <= 25:
            return "極度恐懼"
        elif value <= 45:
            return "恐懼"
        elif value <= 55:
            return "中性"
        elif value <= 75:
            return "貪婪"
        else:
            return "極度貪婪"
    
    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "market": self.market,
            "value": self.value,
            "classification": self.classification,
            "classification_zh": self.get_classification_zh(self.value) if self.value else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
