"""
è‡ªè¨‚ç•°å¸¸é¡žåˆ¥
============
çµ±ä¸€çš„éŒ¯èª¤è™•ç†æ©Ÿåˆ¶
"""


class SELAException(Exception):
    """SELA åŸºç¤Žç•°å¸¸"""
    status_code: int = 400
    error_code: str = "SELA_ERROR"
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        if error_code:
            self.error_code = error_code
        super().__init__(message)


class StockNotFoundError(SELAException):
    """æ‰¾ä¸åˆ°è‚¡ç¥¨"""
    status_code = 404
    error_code = "STOCK_NOT_FOUND"
    
    def __init__(self, symbol: str):
        super().__init__(f"æ‰¾ä¸åˆ°è‚¡ç¥¨: {symbol}")
        self.symbol = symbol


class CryptoNotFoundError(SELAException):
    """æ‰¾ä¸åˆ°åŠ å¯†è²¨å¹£"""
    status_code = 404
    error_code = "CRYPTO_NOT_FOUND"
    
    def __init__(self, symbol: str):
        super().__init__(f"æ‰¾ä¸åˆ°åŠ å¯†è²¨å¹£: {symbol}")
        self.symbol = symbol


class AuthenticationError(SELAException):
    """èªè­‰å¤±æ•—"""
    status_code = 401
    error_code = "AUTH_FAILED"
    
    def __init__(self, message: str = "èªè­‰å¤±æ•—"):
        super().__init__(message)


class AuthorizationError(SELAException):
    """æ¬Šé™ä¸è¶³"""
    status_code = 403
    error_code = "FORBIDDEN"
    
    def __init__(self, message: str = "æ¬Šé™ä¸è¶³"):
        super().__init__(message)


class RateLimitError(SELAException):
    """è«‹æ±‚éŽæ–¼é »ç¹"""
    status_code = 429
    error_code = "RATE_LIMITED"
    
    def __init__(self, message: str = "è«‹æ±‚éŽæ–¼é »ç¹ï¼Œè«‹ç¨å¾Œå†è©¦"):
        super().__init__(message)


class DataSourceError(SELAException):
    """å¤–éƒ¨è³‡æ–™ä¾†æºéŒ¯èª¤"""
    status_code = 502
    error_code = "DATA_SOURCE_ERROR"
    
    def __init__(self, source: str, message: str = None):
        msg = f"{source} è³‡æ–™ä¾†æºéŒ¯èª¤"
        if message:
            msg += f": {message}"
        super().__init__(msg)
        self.source = source


class ValidationError(SELAException):
    """è³‡æ–™é©—è­‰éŒ¯èª¤"""
    status_code = 422
    error_code = "VALIDATION_ERROR"


class CacheError(SELAException):
    """å¿«å–éŒ¯èª¤"""
    status_code = 500
    error_code = "CACHE_ERROR"
    
    def __init__(self, message: str = "å¿«å–æ“ä½œå¤±æ•—"):
        super().__init__(message)


class DatabaseError(SELAException):
    """è³‡æ–™åº«éŒ¯èª¤"""
    status_code = 500
    error_code = "DATABASE_ERROR"
    
    def __init__(self, message: str = "è³‡æ–™åº«æ“ä½œå¤±æ•—"):
        super().__init__(message)