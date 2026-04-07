"""
報酬率比較組合 Model
儲存用戶的自訂比較組合
"""
from datetime import datetime
from typing import List, Optional
import json

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Comparison(Base):
    """用戶儲存的比較組合"""
    __tablename__ = "comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # 組合名稱
    symbols_json = Column(Text, nullable=False)  # JSON 格式儲存 ["AAPL","MSFT"]
    benchmark = Column(String(20), nullable=True, default="^GSPC")  # 基準指數
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯
    user = relationship("User", backref="comparisons")
    
    @property
    def symbols(self) -> List[str]:
        """取得標的列表"""
        try:
            return json.loads(self.symbols_json)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @symbols.setter
    def symbols(self, value: List[str]):
        """設定標的列表"""
        self.symbols_json = json.dumps(value)
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "symbols": self.symbols,
            "benchmark": self.benchmark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Comparison(id={self.id}, name='{self.name}', symbols={self.symbols})>"
