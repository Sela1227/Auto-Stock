"""
æ‡‰ç”¨ç¨‹å¼è¨­å®šæª”
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List


class Settings(BaseSettings):
    """æ‡‰ç”¨ç¨‹å¼è¨­å®š"""
    
<<<<<<< HEAD
    # æ‡‰ç”¨ç¨‹å¼
    APP_NAME: str = "AutoStock è‡ªå‹•é¸è‚¡ç³»çµ±"
    APP_VERSION: str = "1.0.0"  # Phase 4 è¨Šè™Ÿåµæ¸¬ + LINE æŽ¨æ’­
=======
    # 應用程式
    APP_NAME: str = "AutoStock 自動選股系統"
    APP_VERSION: str = "1.0.0"  # Phase 4 訊號偵測 + LINE 推播
>>>>>>> develop
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # è³‡æ–™åº«
    DATABASE_URL: str = "sqlite+aiosqlite:///./stock_analysis.db"
    
    # LINE Login (éšŽæ®µå››)
    LINE_LOGIN_CHANNEL_ID: Optional[str] = None
    LINE_LOGIN_CHANNEL_SECRET: Optional[str] = None
    LINE_LOGIN_CALLBACK_URL: Optional[str] = None
    
    # LINE Messaging (éšŽæ®µå…­)
    LINE_MESSAGING_CHANNEL_ACCESS_TOKEN: Optional[str] = None
    
    # JWT (éšŽæ®µå››)
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_EXPIRE_DAYS: int = 7  # ä¿ç•™å‘å¾Œç›¸å®¹
    
    # ðŸ†• Token éŽæœŸæ™‚é–“ï¼ˆåˆ†é˜ï¼‰
    JWT_EXPIRE_MINUTES_USER: int = 10      # ä¸€èˆ¬ç”¨æˆ¶ 10 åˆ†é˜
    JWT_EXPIRE_MINUTES_ADMIN: int = 60     # ç®¡ç†å“¡ 1 å°æ™‚
    
    # ç®¡ç†å“¡è¨­å®š
    # åˆå§‹ç®¡ç†å“¡çš„ LINE User IDï¼ˆç”¨é€—è™Ÿåˆ†éš”å¤šå€‹ï¼‰
    ADMIN_LINE_USER_IDS: str = "U0f094e89838337e64ba0ca2f68161f3a"
    
    # è³‡æ–™æ›´æ–°è¨­å®š
    STOCK_DATA_CACHE_HOURS: int = 4  # è‚¡åƒ¹è³‡æ–™å¿«å–æ™‚é–“ï¼ˆå°æ™‚ï¼‰
    CRYPTO_DATA_CACHE_MINUTES: int = 15  # å¹£åƒ¹è³‡æ–™å¿«å–æ™‚é–“ï¼ˆåˆ†é˜ï¼‰
    HISTORY_DEFAULT_YEARS: int = 10  # æ­·å²è³‡æ–™é è¨­å¹´æ•¸
    
    # æŠ€è¡“æŒ‡æ¨™é è¨­åƒæ•¸
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
    
    # é€šçŸ¥è¨­å®š
    BREAKOUT_THRESHOLD: float = 2.0  # çªç ´é è­¦é–€æª» (%)
    VOLUME_ALERT_RATIO: float = 2.0  # é‡æ¯”è­¦æˆ’å€æ•¸
    
    def get_admin_line_ids(self) -> List[str]:
        """å–å¾—ç®¡ç†å“¡ LINE User ID åˆ—è¡¨"""
        if not self.ADMIN_LINE_USER_IDS:
            return []
        return [x.strip() for x in self.ADMIN_LINE_USER_IDS.split(",") if x.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# å…¨åŸŸè¨­å®šå¯¦ä¾‹
settings = Settings()

# å°ˆæ¡ˆè·¯å¾‘
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHARTS_DIR = BASE_DIR / "charts"

# ç¢ºä¿ç›®éŒ„å­˜åœ¨
DATA_DIR.mkdir(exist_ok=True)
CHARTS_DIR.mkdir(exist_ok=True)