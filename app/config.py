"""
應用程式設定檔
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List


class Settings(BaseSettings):
    """應用程式設定"""

    # 應用程式
    APP_NAME: str = "AutoStock 自動選股系統"
    APP_VERSION: str = "1.14.0"  # 排程簡化：每日 06:00 單一批次，移除登入觸發與訂閱排程
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
    JWT_EXPIRE_DAYS: int = 7  # 保留向後相容

    # 🆕 Token 過期時間（分鐘）
    JWT_EXPIRE_MINUTES_USER: int = 10      # 一般用戶 10 分鐘
    JWT_EXPIRE_MINUTES_ADMIN: int = 60     # 管理員 1 小時

    # 管理員設定
    ADMIN_LINE_USER_IDS: str = "U0f094e89838337e64ba0ca2f68161f3a"

    # 資料更新設定
    STOCK_DATA_CACHE_HOURS: int = 4
    CRYPTO_DATA_CACHE_MINUTES: int = 15
    HISTORY_DEFAULT_YEARS: int = 10

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
    BREAKOUT_THRESHOLD: float = 2.0
    VOLUME_ALERT_RATIO: float = 2.0

    def get_admin_line_ids(self) -> List[str]:
        """取得管理員 LINE User ID 列表"""
        if not self.ADMIN_LINE_USER_IDS:
            return []
        return [x.strip() for x in self.ADMIN_LINE_USER_IDS.split(",") if x.strip()]

    def validate_production(self) -> None:
        """
        Production fail-fast：若 Railway 環境漏設關鍵變數，直接拒絕啟動。
        比在 README 寫「必填」可靠很多。
        """
        if self.APP_ENV != "production":
            return

        errors = []

        if self.JWT_SECRET_KEY == "your-secret-key-change-in-production":
            errors.append("JWT_SECRET_KEY 尚未設定（仍是預設值）")

        if "sqlite" in self.DATABASE_URL.lower():
            errors.append("DATABASE_URL 不能是 SQLite（production 應使用 PostgreSQL）")

        if not self.LINE_LOGIN_CHANNEL_ID:
            errors.append("LINE_LOGIN_CHANNEL_ID 未設定")

        if not self.LINE_LOGIN_CHANNEL_SECRET:
            errors.append("LINE_LOGIN_CHANNEL_SECRET 未設定")

        if not self.LINE_LOGIN_CALLBACK_URL:
            errors.append("LINE_LOGIN_CALLBACK_URL 未設定")

        if errors:
            error_list = "\n  - ".join(errors)
            raise RuntimeError(
                f"Production 環境設定不完整，拒絕啟動：\n  - {error_list}"
            )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全域設定實例
settings = Settings()

# Production fail-fast（啟動時立即驗證）
settings.validate_production()

# 專案路徑
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHARTS_DIR = BASE_DIR / "charts"

# 確保目錄存在
DATA_DIR.mkdir(exist_ok=True)
CHARTS_DIR.mkdir(exist_ok=True)
