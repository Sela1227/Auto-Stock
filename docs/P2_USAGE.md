# P2 模組拆分 + 事件委託使用說明

## 概述

P2 將 search.js (886行) 拆分為 3 個模組，並加入事件委託優化。

---

## 拆分結構

```
static/js/
├── core.js              # 核心 (P0+P1)
├── state.js             # 狀態管理 (P1)
└── search/              # 搜尋模組 (P2)
    ├── search-core.js   # 搜尋邏輯 + 快取 (~180 行)
    ├── search-render.js # 結果渲染 + 事件委託 (~300 行)
    └── search-chart.js  # 圖表功能 (~280 行)
```

**原本：** 1 個 886 行的檔案
**現在：** 3 個模組，每個 ~250 行，總計 ~760 行

---

## 載入順序

```html
<!-- 核心 -->
<script src="/static/js/core.js"></script>
<script src="/static/js/state.js"></script>

<!-- 搜尋模組 (按順序載入) -->
<script src="/static/js/search/search-core.js"></script>
<script src="/static/js/search/search-render.js"></script>
<script src="/static/js/search/search-chart.js"></script>
```

或使用合併版：
```html
<script src="/static/js/search.js"></script>  <!-- 合併版 -->
```

---

## 事件委託優化

### 舊寫法 (每個按鈕都綁定)

```javascript
// ❌ HTML 中使用 onclick
<button onclick="searchSymbol('AAPL', true)">刷新</button>
<button onclick="openChartFullscreen('AAPL', 150)">圖表</button>
<button onclick="quickAddToWatchlist('AAPL')">追蹤</button>

// 問題：
// 1. 每個按鈕都是獨立事件監聽器
// 2. 動態生成的內容需要重新綁定
// 3. 全域函數污染
```

### 新寫法 (事件委託)

```javascript
// ✅ HTML 使用 data-action
<button data-action="refresh" data-symbol="AAPL">刷新</button>
<button data-action="open-chart" data-symbol="AAPL" data-price="150">圖表</button>
<button data-action="add-watchlist" data-symbol="AAPL" data-type="stock">追蹤</button>

// JavaScript：父容器統一處理
container.addEventListener('click', (e) => {
    const target = e.target.closest('[data-action]');
    if (!target) return;
    
    const action = target.dataset.action;
    const symbol = target.dataset.symbol;
    
    switch (action) {
        case 'refresh':
            searchSymbol(symbol, true);
            break;
        case 'open-chart':
            openChartFullscreen(symbol, target.dataset.price);
            break;
        case 'add-watchlist':
            quickAddToWatchlist(symbol, target.dataset.type);
            break;
    }
});
```

### 優點

| 項目 | 舊寫法 | 新寫法 |
|------|--------|--------|
| 監聽器數量 | N 個 | 1 個 |
| 動態內容 | 需重新綁定 | 自動生效 |
| 記憶體 | 較高 | 較低 |
| 可維護性 | 分散 | 集中 |

---

## 模組職責

### search-core.js
- `searchStock()` - 從輸入框搜尋
- `searchSymbol(symbol, forceRefresh)` - 搜尋指定代號
- `quickAddToWatchlist(symbol, type)` - 快速加入追蹤
- `clearStockCache()` - 清除快取
- `getStockCacheStats()` - 快取統計

### search-render.js
- `renderSearchResult(data, symbol)` - 渲染入口
- `renderStockResult(stock, isCrypto, isTaiwan)` - 渲染結果卡片
- `toggleCollapsible(button)` - 摺疊面板
- 事件委託處理

### search-chart.js
- `openChartFullscreen(symbol, price)` - 開啟全螢幕圖表
- `closeChartFullscreen()` - 關閉圖表
- `setChartRange(days)` - 設置時間範圍
- `renderFullscreenChart(chartData, days)` - 渲染圖表
- `renderVolumeChart(chartData, days, labels)` - 渲染成交量
- `loadReturnsModal(symbol)` - 載入報酬率 Modal
- `closeReturnsModal()` - 關閉報酬率 Modal

---

## SELA 命名空間

所有搜尋功能整合到 `SELA.search`：

```javascript
SELA.search.searchStock()
SELA.search.searchSymbol('AAPL')
SELA.search.quickAddToWatchlist('AAPL', 'stock')
SELA.search.openChartFullscreen('AAPL', 150)
SELA.search.clearCache()
```

---

## 向後兼容

所有原有的全域函數仍可使用：

```javascript
// 這些都還能用
searchStock()
searchSymbol('AAPL')
quickAddToWatchlist('AAPL')
openChartFullscreen('AAPL', 150)
toggleCollapsible(button)
```

---

## 部署方式

### 方式 1：分開載入（開發環境）
```html
<script src="/static/js/search/search-core.js"></script>
<script src="/static/js/search/search-render.js"></script>
<script src="/static/js/search/search-chart.js"></script>
```

### 方式 2：合併版（生產環境）
```bash
cat search-core.js search-render.js search-chart.js > search.js
```

---

## 效能對比

| 指標 | 優化前 | 優化後 |
|------|--------|--------|
| 檔案大小 | 886 行 | ~760 行 |
| 事件監聯器 | ~20 個/卡片 | 1 個/容器 |
| 動態綁定 | 需要 | 不需要 |
| 模組耦合 | 高 | 低 |
| 可測試性 | 差 | 好 |

---

## 遷移其他模組

同樣的模式可以應用到其他大檔案：

```
watchlist.js → watchlist/
├── watchlist-core.js
├── watchlist-render.js
└── watchlist-actions.js

portfolio.js → portfolio/
├── portfolio-core.js
├── portfolio-render.js
└── portfolio-chart.js
```
