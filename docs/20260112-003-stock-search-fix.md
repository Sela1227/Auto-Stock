# 🔧 股票搜尋修復：BRK.B、FIG 等問題

> 文件編號: 20260112-003  
> 更新日期: 2026-01-12  
> 類型: Bug 修復

---

## 🐛 問題描述

### 問題 1: BRK.B 搜尋失敗

**現象：** 搜尋 `BRK.B` (波克夏 B 股) 時返回 404 或錯誤

**原因：** FastAPI 路由 `/{symbol}` 中，`.B` 可能被解析為檔案副檔名

**解決：** 使用 `:path` 路徑轉換器

### 問題 2: FIG 搜尋失敗

**現象：** 搜尋 `FIG` (Figma) 時返回「找不到股票」

**原因：** FIG 是 2024 年 IPO 的新股，系統預設抓取 10 年歷史數據，但 FIG 只有約 1 年數據

**解決：** 改用動態期間，若 10 年數據不足則嘗試較短期間

---

## 📁 修改檔案

`app/routers/stock.py`

---

## 🚀 修復步驟

### 修復 1: 路由路徑參數

找到股票查詢路由（約第 3706 行）：

```python
# 原本
@router.get("/{symbol}", summary="查詢股票")

# 修改為
@router.get("/{symbol:path}", summary="查詢股票")
```

### 修復 2: 動態歷史數據期間

找到 `get_stock_analysis` 函數中抓取歷史數據的部分：

```python
# 原本
df = yahoo_finance.get_stock_history(symbol, period="10y")

# 修改為（動態嘗試不同期間）
df = None
for period in ["10y", "5y", "2y", "1y", "6mo"]:
    df = yahoo_finance.get_stock_history(symbol, period=period)
    if df is not None and len(df) >= 20:  # 至少需要 20 筆數據
        logger.info(f"{symbol} 使用 {period} 期間，共 {len(df)} 筆數據")
        break
```

---

## 📝 完整修改後的函數

```python
@router.get("/{symbol:path}", summary="查詢股票")
async def get_stock_analysis(
    symbol: str,
    refresh: bool = Query(False, description="是否強制更新資料"),
):
    """
    查詢單一股票的技術分析報告
    """
    from app.data_sources.yahoo_finance import yahoo_finance
    from app.services.indicator_service import indicator_service
    
    # 台股代號自動轉換
    symbol = normalize_tw_symbol(symbol)
    original_symbol = symbol
    logger.info(f"開始查詢股票: {symbol}")
    
    try:
        # 動態嘗試不同期間（解決新股歷史數據不足問題）
        df = None
        used_period = None
        for period in ["10y", "5y", "2y", "1y", "6mo"]:
            logger.info(f"嘗試抓取 {symbol} {period} 數據...")
            df = yahoo_finance.get_stock_history(symbol, period=period)
            if df is not None and len(df) >= 20:
                used_period = period
                logger.info(f"{symbol} 使用 {period} 期間，共 {len(df)} 筆數據")
                break
        
        # 如果 .TW 找不到，嘗試 .TWO (上櫃股票)
        if (df is None or df.empty) and symbol.endswith('.TW'):
            two_symbol = symbol.replace('.TW', '.TWO')
            logger.info(f"{symbol} 找不到，嘗試上櫃股票: {two_symbol}")
            for period in ["10y", "5y", "2y", "1y", "6mo"]:
                df = yahoo_finance.get_stock_history(two_symbol, period=period)
                if df is not None and len(df) >= 20:
                    symbol = two_symbol
                    used_period = period
                    logger.info(f"成功找到上櫃股票: {two_symbol}")
                    break
        
        if df is None or df.empty:
            logger.warning(f"找不到股票資料: {original_symbol}")
            raise HTTPException(
                status_code=404,
                detail=f"找不到股票: {original_symbol}（已嘗試上市 .TW 和上櫃 .TWO）"
            )
        
        # ... 後續代碼保持不變 ...
```

---

## ✅ 驗證

修復後測試以下股票：

| 代碼 | 說明 | 預期結果 |
|------|------|---------|
| `BRK.B` | 波克夏 B 股 | ✅ 正常顯示 |
| `BRK-B` | 替代寫法 | ✅ 正常顯示 |
| `FIG` | Figma (2024 IPO) | ✅ 正常顯示（使用 1y 數據）|
| `AAPL` | Apple | ✅ 正常顯示 |
| `2330` | 台積電 | ✅ 正常顯示 |

---

## ⚠️ 注意事項

1. 使用 `:path` 轉換器後，URL 中的 `/` 也會被捕獲，需確保沒有其他路由衝突
2. 新股可能只有較短期間的數據，CAGR 計算結果可能不完整
3. 某些股票可能同時有 `BRK.B` 和 `BRK-B` 兩種寫法，建議前端統一處理

---

## 📌 常見特殊股票代碼

| 公司 | 代碼 | 說明 |
|------|------|------|
| Berkshire Hathaway A | BRK.A 或 BRK-A | 高價股 |
| Berkshire Hathaway B | BRK.B 或 BRK-B | 一般投資人 |
| Alphabet A | GOOGL | 有投票權 |
| Alphabet C | GOOG | 無投票權 |
| Meta Platforms | META | 原 FB |

Yahoo Finance API 通常接受 `.` 或 `-` 作為分隔符，建議後端統一處理。
