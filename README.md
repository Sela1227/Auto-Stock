# 🔧 Bug 修復包 - 台股代號 & CAGR 計算

## 修復的問題

### Bug 1: 台股代號需要手動加 .TW
**問題**: 輸入 `0050`、`2330` 等純數字台股代號時無法查詢
**原因**: Yahoo Finance 需要 `0050.TW` 格式
**修復**: 自動偵測並轉換台股代號

| 輸入 | 轉換後 |
|------|--------|
| `0050` | `0050.TW` |
| `2330` | `2330.TW` |
| `00878` | `00878.TW` |
| `AAPL` | `AAPL` (不變) |
| `^GSPC` | `^GSPC` (不變) |

### Bug 2: 比較功能的 CAGR 計算不含配息
**問題**: 比較頁面的 CAGR 只用分割調整價格，沒有計入配息
**原因**: 原本使用 `indicator_service.calculate_cagr()`，只用 close 價格
**修復**: 使用和「年化報酬率」頁面一樣的計算公式，包含：
- 分割調整 (adj_close)
- 配息還原 (dividend reinvestment)

## 修改的檔案

```
app/
├── routers/
│   └── stock.py          ← 加入台股代號自動轉換
└── services/
    └── compare_service.py ← 使用含配息的 CAGR 計算
```

## 部署步驟

1. 備份原檔案
2. 將 `app/routers/stock.py` 覆蓋到專案
3. 將 `app/services/compare_service.py` 覆蓋到專案
4. 重新部署

## 修改重點

### stock.py
新增 `normalize_tw_symbol()` 函數，在以下位置使用：
- `get_stock_analysis()` - 查詢股票
- `get_stock_chart()` - 股票圖表
- `compare_stocks()` - 走勢比較
- `get_stock_returns()` - 年化報酬率
- `debug_prices()` - Debug 工具

### compare_service.py
- 新增 `_normalize_symbol()` 方法
- 新增 `_calculate_cagr_with_dividends()` 方法
- 取得配息資料並還原調整
- 新增台股 ETF 和科技股預設組合

## 測試建議

1. 測試台股查詢：
   - 輸入 `0050` → 應顯示元大台灣50
   - 輸入 `2330` → 應顯示台積電

2. 測試比較功能：
   - 比較 `0050` 和 `0056` → 應有數據
   - CAGR 數值應和「年化報酬率」頁面一致
