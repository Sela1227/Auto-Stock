"""
自訂異常類別
============
統一的錯誤處理機制
"""


class SELAException(Exception):
    """SELA 基礎異常"""
    status_code: int = 400
    error_code: str = "SELA_ERROR"
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        if error_code:
            self.error_code = error_code
        super().__init__(message)


class StockNotFoundError(SELAException):
    """找不到股票"""
    status_code = 404
    error_code = "STOCK_NOT_FOUND"
    
    def __init__(self, symbol: str):
        super().__init__(f"找不到股票: {symbol}")
        self.symbol = symbol


class CryptoNotFoundError(SELAException):
    """找不到加密貨幣"""
    status_code = 404
    error_code = "CRYPTO_NOT_FOUND"
    
    def __init__(self, symbol: str):
        super().__init__(f"找不到加密貨幣: {symbol}")
        self.symbol = symbol


class AuthenticationError(SELAException):
    """認證失敗"""
    status_code = 401
    error_code = "AUTH_FAILED"
    
    def __init__(self, message: str = "認證失敗"):
        super().__init__(message)


class AuthorizationError(SELAException):
    """權限不足"""
    status_code = 403
    error_code = "FORBIDDEN"
    
    def __init__(self, message: str = "權限不足"):
        super().__init__(message)


class RateLimitError(SELAException):
    """請求過於頻繁"""
    status_code = 429
    error_code = "RATE_LIMITED"
    
    def __init__(self, message: str = "請求過於頻繁，請稍後再試"):
        super().__init__(message)


class DataSourceError(SELAException):
    """外部資料來源錯誤"""
    status_code = 502
    error_code = "DATA_SOURCE_ERROR"
    
    def __init__(self, source: str, message: str = None):
        msg = f"{source} 資料來源錯誤"
        if message:
            msg += f": {message}"
        super().__init__(msg)
        self.source = source


class ValidationError(SELAException):
    """資料驗證錯誤"""
    status_code = 422
    error_code = "VALIDATION_ERROR"


class CacheError(SELAException):
    """快取錯誤"""
    status_code = 500
    error_code = "CACHE_ERROR"
    
    def __init__(self, message: str = "快取操作失敗"):
        super().__init__(message)


class DatabaseError(SELAException):
    """資料庫錯誤"""
    status_code = 500
    error_code = "DATABASE_ERROR"
    
    def __init__(self, message: str = "資料庫操作失敗"):
        super().__init__(message)
