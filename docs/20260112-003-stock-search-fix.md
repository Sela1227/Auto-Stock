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

## 📌 常見特殊股票代碼

| 公司 | 代碼 | 說明 |
|------|------|------|
| Berkshire Hathaway A | BRK.A 或 BRK-A | 高價股 |
| Berkshire Hathaway B | BRK.B 或 BRK-B | 一般投資人 |
| Alphabet A | GOOGL | 有投票權 |
| Alphabet C | GOOG | 無投票權 |
