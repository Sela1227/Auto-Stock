# SELA 前端模組化版本 - 2026/01/15 22:30

## 📦 目錄結構

```
static/
├── dashboard.html         # 主頁面 (1520 行 - 原 5500 行)
├── css/
│   └── dashboard.css      # CSS 樣式 (329 行)
└── js/
    ├── utils.js           # 工具函數 (244 行)
    ├── core.js            # 核心模組 (386 行)
    ├── dashboard.js       # 儀表板 (460 行)
    ├── search.js          # 股票查詢 (600 行)
    ├── watchlist.js       # 追蹤清單 (572 行)
    ├── portfolio.js       # 投資記錄 (445 行)
    ├── compare.js         # 走勢比較 (256 行)
    ├── subscription.js    # 訂閱精選 (99 行)
    ├── settings.js        # 設定 (240 行)
    └── transaction.js     # 交易功能 (410 行)
```

## ✨ 模組功能

| 模組 | 功能 |
|------|------|
| `utils.js` | 格式化、防抖、storage 封裝、檔案解析 |
| `core.js` | 認證、API 請求、Session 管理、導航、Toast |
| `dashboard.js` | BTC 價格、三大指數、市場情緒、指數圖表 Modal |
| `search.js` | 股票搜尋、結果顯示、全螢幕圖表、年化報酬率 Modal |
| `watchlist.js` | 追蹤清單、排序、匯出匯入、目標價設定 |
| `portfolio.js` | 持股總覽、交易紀錄、匯出匯入 |
| `compare.js` | 走勢比較圖表 |
| `subscription.js` | 訂閱精選功能 |
| `settings.js` | 指標設定、通知設定、模板套用 |
| `transaction.js` | 台股/美股交易 Modal |

## 🔧 部署方式

1. 將整個 `static/` 目錄複製到你的專案
2. 確保靜態資源路徑正確：
   - CSS: `/static/css/dashboard.css`
   - JS: `/static/js/*.js`

## 📊 效果對比

| 項目 | 優化前 | 模組化後 | 減少 |
|------|--------|----------|------|
| dashboard.html | 5500 行 | 1520 行 | **72%** |
| JavaScript | 內聯 ~3700 行 | 11 個模組 ~4200 行 | 結構化 |
| 可維護性 | 低 | 高 | - |
| 功能擴展 | 困難 | 容易 | - |  

## 🚀 優點

1. **易於維護**：每個功能獨立成模組
2. **可重用**：函數可在其他頁面使用
3. **易於測試**：可單獨測試各模組
4. **團隊協作**：不同人可同時修改不同模組
5. **向後兼容**：所有函數都導出到 window

## ⚠️ 注意事項

- 模組載入順序很重要：
  1. `utils.js` - 工具函數（無依賴）
  2. `core.js` - 核心功能（依賴 utils）
  3. 其他模組（依賴 core）
- 所有模組都使用 IIFE，不會污染全域命名空間
- 函數通過 `window.xxx = xxx` 導出，支援 HTML onclick

