"""
æ—¥èªŒè¨­å®š
ç¢ºä¿æ‰€æœ‰é‡è¦æ“ä½œéƒ½æœ‰è¨˜éŒ„
"""
import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_to_file: bool = True):
    """
    è¨­å®šæ—¥èªŒç³»çµ±
    
    Args:
        log_level: æ—¥èªŒç­‰ç´š (DEBUG, INFO, WARNING, ERROR)
        log_to_file: æ˜¯å¦å¯«å…¥æª”æ¡ˆ
    """
    # å»ºç«‹ logs ç›®éŒ„
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # æ—¥èªŒæ ¼å¼
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # å»ºç«‹ formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # å–å¾— root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # æ¸…é™¤ç¾æœ‰çš„ handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    if log_to_file:
        # ä¸»è¦æ—¥èªŒæª”ï¼ˆæ‰€æœ‰æ—¥èªŒï¼‰
        today = datetime.now().strftime("%Y-%m-%d")
        main_log_file = log_dir / f"app_{today}.log"
        file_handler = logging.FileHandler(main_log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        
        # èªè­‰æ—¥èªŒæª”ï¼ˆç™»å…¥/ç™»å‡ºï¼‰
        auth_logger = logging.getLogger("app.services.auth_service")
        auth_log_file = log_dir / f"auth_{today}.log"
        auth_handler = logging.FileHandler(auth_log_file, encoding="utf-8")
        auth_handler.setFormatter(formatter)
        auth_handler.setLevel(logging.INFO)
        auth_logger.addHandler(auth_handler)
        
        # Watchlist æ—¥èªŒæª”
        watchlist_logger = logging.getLogger("app.services.watchlist_service")
        watchlist_log_file = log_dir / f"watchlist_{today}.log"
        watchlist_handler = logging.FileHandler(watchlist_log_file, encoding="utf-8")
        watchlist_handler.setFormatter(formatter)
        watchlist_handler.setLevel(logging.INFO)
        watchlist_logger.addHandler(watchlist_handler)
    
    # è¨­å®šç¬¬ä¸‰æ–¹å¥—ä»¶çš„æ—¥èªŒç­‰ç´š
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    root_logger.info("æ—¥èªŒç³»çµ±åˆå§‹åŒ–å®Œæˆ")
    if log_to_file:
        root_logger.info(f"æ—¥èªŒæª”æ¡ˆ: {log_dir.absolute()}")


def get_logger(name: str) -> logging.Logger:
    """å–å¾— logger"""
    return logging.getLogger(name)