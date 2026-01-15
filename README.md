# SELA 前端優化版 - 2026/01/15

## 📦 包含檔案

```
static/
├── dashboard.html     # 優化版 HTML（5169 行，減少 330 行）
├── css/
│   └── dashboard.css  # 抽離的 CSS 樣式（329 行）
└── js/
    └── utils.js       # 工具函數庫（170 行）
```

## ✨ 優化內容

### 1. CSS 抽離
- 將所有 CSS 樣式移至 `css/dashboard.css`
- HTML 減少 ~330 行
- 便於樣式統一管理和維護

### 2. 工具函數庫
新增 `js/utils.js` 包含以下工具函數：

**格式化工具：**
- `formatNumber(num, decimals)` - 數字格式化
- `formatPrice(price, currency)` - 價格格式化
- `formatPercent(value, showSign)` - 百分比格式化
- `formatDate(dateStr, format)` - 日期格式化
- `formatLargeNumber(num)` - 大數字縮寫（K/M/B/T）
- `formatShares(shares, market)` - 股數格式化
- `getChangeClass(value)` - 漲跌樣式
- `getChangeIcon(value)` - 漲跌圖示

**防抖與節流：**
- `debounce(func, wait)` - 防抖
- `throttle(func, limit)` - 節流

**Storage 封裝：**
- `storage.get(key, defaultValue)`
- `storage.set(key, value)`
- `storage.remove(key)`

**檔案處理：**
- `parseCSV(content)` - 解析 CSV
- `parseJSON(content)` - 解析 JSON
- `previewFile(file, callback)` - 預覽檔案

## 🔧 部署方式

1. 將 `css/` 和 `js/` 目錄複製到你的 `static/` 目錄
2. 用新的 `dashboard.html` 替換原有檔案
3. 確保服務器正確處理靜態檔案

## 🚀 未來優化方向

這是第一階段優化，未來可以進一步：

1. **JS 模組化**：將 JavaScript 按功能拆分成獨立模組
2. **組件化**：將 Modal、卡片等 UI 元件抽成可重用組件
3. **打包工具**：使用 esbuild/webpack 打包並壓縮

詳細的模組化框架已準備好在 `sela_refactor_framework.zip` 中。

## 📊 效果對比

| 項目 | 優化前 | 優化後 | 減少 |
|------|--------|--------|------|
| dashboard.html | 5499 行 | 5169 行 | 330 行 |
| CSS | 內聯 | 獨立檔案 | - |
| 工具函數 | 散落各處 | 統一管理 | - |

## ⚠️ 注意事項

- CSS 檔案路徑：`/static/css/dashboard.css`
- JS 檔案路徑：`/static/js/utils.js`
- 確保靜態資源路徑正確
