"""
compare_service.py 台股名稱修復補丁

問題位置: _fetch_price_data 方法中的名稱取得邏輯
問題代碼 (約第 7529-7542 行):
    if info:
        info_dict = {
            "name": info.get("name", symbol),  # ⚠️ 這裡直接用 info，會有亂碼
            ...
        }

修復: 台股優先使用 TAIWAN_STOCK_NAMES 字典
"""

# ============================================================
# 步驟 1: 在 compare_service.py 開頭加入導入
# ============================================================
# 找到現有的 import 區塊，在最後加入：

# from app.data_sources.taiwan_stocks import TAIWAN_STOCK_NAMES, is_taiwan_stock


# ============================================================
# 步驟 2: 修改 _fetch_price_data 方法
# ============================================================
# 找到這段代碼 (約在 7529-7542 行):

"""
原始代碼:
                if info:
                    info_dict = {
                        "name": info.get("name", symbol),
                        "type": asset_type,
                        "current_price": current_price or info.get("current_price"),
                        "symbol": symbol,
                    }
                else:
                    info_dict = {
                        "name": symbol, 
                        "type": asset_type, 
                        "current_price": current_price,
                        "symbol": symbol,
                    }
"""

# 替換為:

"""
修復後代碼:
                # ========== 修復: 台股優先使用本地名稱字典 ==========
                name = symbol
                if is_taiwan_stock(symbol):
                    stock_code = symbol.replace('.TW', '').replace('.TWO', '')
                    name = TAIWAN_STOCK_NAMES.get(stock_code, symbol)
                elif info:
                    name = info.get("name", symbol)
                # ================================================
                
                if info:
                    info_dict = {
                        "name": name,  # 使用修復後的名稱
                        "type": asset_type,
                        "current_price": current_price or info.get("current_price"),
                        "symbol": symbol,
                    }
                else:
                    info_dict = {
                        "name": name,  # 使用修復後的名稱
                        "type": asset_type, 
                        "current_price": current_price,
                        "symbol": symbol,
                    }
"""


# ============================================================
# 完整的修復後 _fetch_price_data 方法 (可直接複製替換)
# ============================================================

async def _fetch_price_data(
    self,
    symbol: str,
    days: int = 3650,
):
    """
    抓取價格資料 (修復版 - 解決台股名稱亂碼)
    
    Returns:
        (DataFrame, info_dict) 或 (None, None)
    """
    asset_type = self._get_asset_type(symbol)
    
    try:
        if asset_type == "crypto":
            # 加密貨幣用 CoinGecko
            df = coingecko.get_crypto_history(symbol, days=days)
            info = coingecko.get_crypto_info(symbol)
            if info:
                info_dict = {
                    "name": info.get("name", symbol),
                    "type": "crypto",
                    "current_price": info.get("current_price"),
                }
            else:
                info_dict = {"name": symbol, "type": "crypto", "current_price": None}
            return df, info_dict
        else:
            # 股票/指數/ETF 用 Yahoo Finance
            period = "10y" if days >= 3650 else ("5y" if days >= 1825 else "1y")
            df = yahoo_finance.get_stock_history(symbol, period=period)
            
            # 如果 .TW 找不到，嘗試 .TWO (上櫃股票)
            if (df is None or df.empty) and symbol.endswith('.TW'):
                two_symbol = symbol.replace('.TW', '.TWO')
                logger.info(f"{symbol} 找不到，嘗試上櫃股票: {two_symbol}")
                df = yahoo_finance.get_stock_history(two_symbol, period=period)
                if df is not None and not df.empty:
                    symbol = two_symbol
                    logger.info(f"成功找到上櫃股票: {two_symbol}")
            
            info = yahoo_finance.get_stock_info(symbol)
            
            # 取得現價（用原始收盤價）
            current_price = None
            if df is not None and not df.empty:
                current_price = float(df['close'].iloc[-1])
            
            # ========== 修復: 台股優先使用本地名稱字典 ==========
            name = symbol
            if is_taiwan_stock(symbol):
                stock_code = symbol.replace('.TW', '').replace('.TWO', '')
                name = TAIWAN_STOCK_NAMES.get(stock_code, symbol)
                logger.debug(f"台股名稱修復: {symbol} -> {name}")
            elif info:
                name = info.get("name", symbol)
            # ================================================
            
            if info:
                info_dict = {
                    "name": name,  # 使用修復後的名稱
                    "type": asset_type,
                    "current_price": current_price or info.get("current_price"),
                    "symbol": symbol,
                }
            else:
                info_dict = {
                    "name": name,  # 使用修復後的名稱
                    "type": asset_type, 
                    "current_price": current_price,
                    "symbol": symbol,
                }
            
            return df, info_dict
        
    except Exception as e:
        logger.error(f"抓取 {symbol} 資料失敗: {e}")
        return None, None
