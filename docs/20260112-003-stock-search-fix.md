# 🔧 股票搜尋修復：BRK.B、FIG 等問題

> 文件編號: 20260112-003  
> 更新日期: 2026-01-12  
> 類型: Bug 修復  
> 優先級: 高

---

## 🐛 問題描述

| 股票 | 問題現象 | 根本原因 |
|------|----------|---------|
| BRK.B | 搜尋返回 404 | 1. URL 中 `.B` 被解析為副檔名<br>2. Yahoo 可能需要 `BRK-B` 格式 |
| FIG | 找不到股票 | 2024 IPO 新股，只有 1 年數據，但系統要求 10 年 |

---

## 📁 修改檔案

- `app/routers/stock.py` - 主要修改
- 參考：`app/routers/stock_patch.py` - 完整修改說明

---

## 🚀 修復步驟（共 3 步）

### 步驟 1: 修改路由定義

找到約第 **3706 行**：

```python
# ❌ 原本
@router.get("/{symbol}", summary="查詢股票")

# ✅ 改為
@router.get("/{symbol:path}", summary="查詢股票")
```

### 步驟 2: 新增股票代碼變體函數

在 `normalize_tw_symbol` 函數後面加入：

```python
def get_symbol_variants(symbol: str) -> list:
    """
    產生股票代碼的變體列表
    BRK.B -> ["BRK.B", "BRK-B"]
    """
    variants = [symbol]
    
    # 含 `.` 但不是台股，也嘗試 `-` 格式
    if '.' in symbol and not symbol.endswith('.TW') and not symbol.endswith('.TWO'):
        variants.append(symbol.replace('.', '-'))
    
    # 含 `-`，也嘗試 `.` 格式
    if '-' in symbol:
        variants.append(symbol.replace('-', '.'))
    
    return variants
```

### 步驟 3: 修改歷史數據抓取邏輯

找到約第 **3722-3741 行**，將：

```python
# ❌ 原本
df = yahoo_finance.get_stock_history(symbol, period="10y")

if (df is None or df.empty) and symbol.endswith('.TW'):
    # ... 台股處理 ...

if df is None or df.empty:
    raise HTTPException(status_code=404, ...)
```

替換為：

```python
# ✅ 修復後
df = None
used_period = None
actual_symbol = symbol

# 產生代碼變體（BRK.B -> BRK-B）
symbol_variants = get_symbol_variants(symbol)

# 嘗試不同期間（解決新股問題）
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

# 使用實際找到的 symbol
symbol = actual_symbol
```

---

## ✅ 驗證

修復後測試：

| 輸入 | 預期行為 |
|------|---------|
| `BRK.B` | 自動嘗試 BRK.B 和 BRK-B |
| `BRK-B` | 自動嘗試 BRK-B 和 BRK.B |
| `FIG` | 自動嘗試較短期間（1y, 6mo）|
| `AAPL` | 正常（10y）|
| `2330` | 正常（自動加 .TW）|

---

## 📌 特殊股票代碼對照

| 公司 | Yahoo 格式 | 說明 |
|------|-----------|------|
| Berkshire A | BRK-A 或 BRK.A | 系統會自動嘗試兩種 |
| Berkshire B | BRK-B 或 BRK.B | 系統會自動嘗試兩種 |
| Figma | FIG | 2024 IPO，需用短期間 |
