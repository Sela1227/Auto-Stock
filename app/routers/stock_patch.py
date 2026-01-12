"""
stock.py 修復補丁
解決 BRK.B、FIG 等股票搜尋失敗問題

問題：
1. BRK.B 等含 `.` 的股票代碼在 URL 中被錯誤解析
2. FIG 等新 IPO 股票因歷史數據不足而失敗
3. Yahoo Finance 對某些股票使用 `-` 而非 `.`（如 BRK-B）
"""

# ============================================================
# 修復 1: 路由定義（約第 3706 行）
# ============================================================

# 原本:
# @router.get("/{symbol}", summary="查詢股票")

# 改為:
# @router.get("/{symbol:path}", summary="查詢股票")


# ============================================================
# 修復 2: 新增股票代碼標準化函數（在 normalize_tw_symbol 後面加）
# ============================================================

def normalize_us_symbol(symbol: str) -> str:
    """
    標準化美股代碼
    - BRK.B -> 嘗試 BRK.B 和 BRK-B
    - 處理其他特殊格式
    """
    symbol = symbol.strip().upper()
    return symbol


def get_symbol_variants(symbol: str) -> list:
    """
    產生股票代碼的變體列表，用於嘗試不同格式
    例如 BRK.B -> ["BRK.B", "BRK-B"]
    """
    variants = [symbol]
    
    # 如果包含 `.`，也嘗試 `-` 格式
    if '.' in symbol and not symbol.endswith('.TW') and not symbol.endswith('.TWO'):
        variants.append(symbol.replace('.', '-'))
    
    # 如果包含 `-`，也嘗試 `.` 格式
    if '-' in symbol:
        variants.append(symbol.replace('-', '.'))
    
    return variants


# ============================================================
# 修復 3: 修改 get_stock_analysis 函數
# ============================================================

# 找到這段代碼（約第 3722-3741 行）:
"""
原始代碼:
    try:
        # 取得股票資料 (抓取 10 年以計算長期 CAGR)
        logger.info(f"正在從 Yahoo Finance 取得 {symbol} 資料...")
        df = yahoo_finance.get_stock_history(symbol, period="10y")
        
        # 如果 .TW 找不到，嘗試 .TWO (上櫃股票)
        if (df is None or df.empty) and symbol.endswith('.TW'):
            ...
        
        if df is None or df.empty:
            logger.warning(f"找不到股票資料: {original_symbol}")
            raise HTTPException(
                status_code=404,
                detail=f"找不到股票: {original_symbol}（已嘗試上市 .TW 和上櫃 .TWO）"
            )
"""

# 替換為:
"""
修復後代碼:
    try:
        # 取得股票資料
        logger.info(f"正在從 Yahoo Finance 取得 {symbol} 資料...")
        
        df = None
        used_period = None
        actual_symbol = symbol
        
        # 產生股票代碼變體（處理 BRK.B / BRK-B 等情況）
        symbol_variants = get_symbol_variants(symbol)
        
        # 嘗試不同期間（解決新股歷史數據不足問題）
        periods = ["10y", "5y", "2y", "1y", "6mo", "3mo"]
        
        for try_symbol in symbol_variants:
            if df is not None and not df.empty:
                break
                
            for period in periods:
                logger.info(f"嘗試 {try_symbol} 期間 {period}...")
                df = yahoo_finance.get_stock_history(try_symbol, period=period)
                
                if df is not None and len(df) >= 20:
                    used_period = period
                    actual_symbol = try_symbol
                    logger.info(f"成功: {try_symbol} 使用 {period}，共 {len(df)} 筆")
                    break
        
        # 如果 .TW 找不到，嘗試 .TWO (上櫃股票)
        if (df is None or df.empty) and symbol.endswith('.TW'):
            two_symbol = symbol.replace('.TW', '.TWO')
            logger.info(f"{symbol} 找不到，嘗試上櫃股票: {two_symbol}")
            for period in periods:
                df = yahoo_finance.get_stock_history(two_symbol, period=period)
                if df is not None and len(df) >= 20:
                    actual_symbol = two_symbol
                    used_period = period
                    logger.info(f"成功找到上櫃股票: {two_symbol}")
                    break
        
        if df is None or df.empty:
            # 提供更詳細的錯誤訊息
            tried = ", ".join(symbol_variants)
            logger.warning(f"找不到股票資料: {original_symbol} (已嘗試: {tried})")
            raise HTTPException(
                status_code=404,
                detail=f"找不到股票: {original_symbol}（已嘗試: {tried}）"
            )
        
        # 使用實際找到的 symbol
        symbol = actual_symbol
        logger.info(f"取得 {len(df)} 筆資料（{used_period}），正在計算技術指標...")
"""


# ============================================================
# 完整的修復後函數（可直接複製替換）
# ============================================================

@router.get("/{symbol:path}", summary="查詢股票")
async def get_stock_analysis(
    symbol: str,
    refresh: bool = Query(False, description="是否強制更新資料"),
):
    """
    查詢單一股票的技術分析報告
    支援: 美股(AAPL)、台股(2330)、特殊格式(BRK.B, BRK-B)
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.indicator_service import indicator_service
    
    # 台股代號自動轉換
    symbol = normalize_tw_symbol(symbol)
    original_symbol = symbol
    logger.info(f"開始查詢股票: {symbol}")
    
    try:
        df = None
        used_period = None
        actual_symbol = symbol
        
        # 產生股票代碼變體（處理 BRK.B / BRK-B）
        symbol_variants = [symbol]
        if '.' in symbol and not symbol.endswith('.TW') and not symbol.endswith('.TWO'):
            symbol_variants.append(symbol.replace('.', '-'))
        if '-' in symbol:
            symbol_variants.append(symbol.replace('-', '.'))
        
        # 嘗試不同期間
        periods = ["10y", "5y", "2y", "1y", "6mo", "3mo"]
        
        for try_symbol in symbol_variants:
            if df is not None and len(df) >= 20:
                break
            for period in periods:
                logger.info(f"嘗試 {try_symbol} 期間 {period}...")
                df = yahoo_finance.get_stock_history(try_symbol, period=period)
                if df is not None and len(df) >= 20:
                    used_period = period
                    actual_symbol = try_symbol
                    logger.info(f"成功: {try_symbol} 使用 {period}，共 {len(df)} 筆")
                    break
        
        # 台股 .TW -> .TWO 嘗試
        if (df is None or len(df) < 20) and symbol.endswith('.TW'):
            two_symbol = symbol.replace('.TW', '.TWO')
            for period in periods:
                df = yahoo_finance.get_stock_history(two_symbol, period=period)
                if df is not None and len(df) >= 20:
                    actual_symbol = two_symbol
                    used_period = period
                    break
        
        if df is None or len(df) < 20:
            tried = ", ".join(set(symbol_variants))
            raise HTTPException(
                status_code=404,
                detail=f"找不到股票: {original_symbol}（已嘗試: {tried}）"
            )
        
        symbol = actual_symbol
        logger.info(f"取得 {len(df)} 筆資料，正在計算技術指標...")
        
        # ... 後續代碼保持不變 ...
