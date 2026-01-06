"""
應用程式設定檔
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List


class Settings(BaseSettings):
    """應用程式設定"""
    
    # 應用程式
    APP_NAME: str = "SELA 自動選股系統"
    APP_VERSION: str = "0.5.0"  # 升級版本
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # 資料庫
    DATABASE_URL: str = "sqlite+aiosqlite:///./stock_analysis.db"
    
    # LINE Login (階段四)
    LINE_LOGIN_CHANNEL_ID: Optional[str] = None
    LINE_LOGIN_CHANNEL_SECRET: Optional[str] = None
    LINE_LOGIN_CALLBACK_URL: Optional[str] = None
    
    # LINE Messaging (階段六)
    LINE_MESSAGING_CHANNEL_ACCESS_TOKEN: Optional[str] = None
    
    # JWT (階段四)
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_EXPIRE_DAYS: int = 7
    
    # 管理員設定
    # 初始管理員的 LINE User ID（用逗號分隔多個）
    ADMIN_LINE_USER_IDS: str = "U0f094e89838337e64ba0ca2f68161f3a"
    
    # 資料更新設定
    STOCK_DATA_CACHE_HOURS: int = 4  # 股價資料快取時間（小時）
    CRYPTO_DATA_CACHE_MINUTES: int = 15  # 幣價資料快取時間（分鐘）
    
    # 技術指標預設參數
    MA_SHORT: int = 20
    MA_MID: int = 50
    MA_LONG: int = 200
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: int = 70
    RSI_OVERSOLD: int = 30
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    KD_PERIOD: int = 9
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD: float = 2.0
    
    # 通知設定
    BREAKOUT_THRESHOLD: float = 2.0  # 突破預警門檻 (%)
    VOLUME_ALERT_RATIO: float = 2.0  # 量比警戒倍數
    
    def get_admin_line_ids(self) -> List[str]:
        """取得管理員 LINE User ID 列表"""
        if not self.ADMIN_LINE_USER_IDS:
            return []
        return [x.strip() for x in self.ADMIN_LINE_USER_IDS.split(",") if x.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全域設定實例
settings = Settings()

# 專案路徑
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHARTS_DIR = BASE_DIR / "charts"

# 確保目錄存在
DATA_DIR.mkdir(exist_ok=True)
CHARTS_DIR.mkdir(exist_ok=True)
