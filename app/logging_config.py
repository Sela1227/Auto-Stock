"""
日誌設定
確保所有重要操作都有記錄
"""
import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_to_file: bool = True):
    """
    設定日誌系統
    
    Args:
        log_level: 日誌等級 (DEBUG, INFO, WARNING, ERROR)
        log_to_file: 是否寫入檔案
    """
    # 建立 logs 目錄
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 日誌格式
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 建立 formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # 取得 root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # 清除現有的 handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    if log_to_file:
        # 主要日誌檔（所有日誌）
        today = datetime.now().strftime("%Y-%m-%d")
        main_log_file = log_dir / f"app_{today}.log"
        file_handler = logging.FileHandler(main_log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        
        # 認證日誌檔（登入/登出）
        auth_logger = logging.getLogger("app.services.auth_service")
        auth_log_file = log_dir / f"auth_{today}.log"
        auth_handler = logging.FileHandler(auth_log_file, encoding="utf-8")
        auth_handler.setFormatter(formatter)
        auth_handler.setLevel(logging.INFO)
        auth_logger.addHandler(auth_handler)
        
        # Watchlist 日誌檔
        watchlist_logger = logging.getLogger("app.services.watchlist_service")
        watchlist_log_file = log_dir / f"watchlist_{today}.log"
        watchlist_handler = logging.FileHandler(watchlist_log_file, encoding="utf-8")
        watchlist_handler.setFormatter(formatter)
        watchlist_handler.setLevel(logging.INFO)
        watchlist_logger.addHandler(watchlist_handler)
    
    # 設定第三方套件的日誌等級
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    root_logger.info("日誌系統初始化完成")
    if log_to_file:
        root_logger.info(f"日誌檔案: {log_dir.absolute()}")


def get_logger(name: str) -> logging.Logger:
    """取得 logger"""
    return logging.getLogger(name)
