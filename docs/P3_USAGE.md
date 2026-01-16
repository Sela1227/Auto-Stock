# P3 事件委託 + AppState 整合使用說明

## 概述

P3 優化 `watchlist.js` 和 `portfolio.js`，加入：
1. 事件委託 - 減少監聽器數量
2. AppState 整合 - 統一狀態管理
3. DOM 快取 - 使用 `$()` 函數

---

## 優化前後對比

### watchlist.js

| 項目 | 優化前 | 優化後 |
|------|--------|--------|
| 監聽器/卡片 | ~8 個 | 1 個 |
| 狀態管理 | 私有變數 | AppState |
| DOM 查詢 | getElementById | $() 快取 |

### portfolio.js

| 項目 | 優化前 | 優化後 |
|------|--------|--------|
| 監聯器/卡片 | ~3 個 | 1 個 |
| 狀態管理 | 無 | AppState |
| DOM 查詢 | getElementById | $() 快取 |

---

## 事件委託模式

### 舊寫法

```html
<!-- 每個按鈕都有 onclick -->
<button onclick="removeFromWatchlist('AAPL')">刪除</button>
<button onclick="searchSymbol('AAPL')">分析</button>
<button onclick="quickTrade('AAPL', 'Apple', 'us', 'buy')">買入</button>
```

### 新寫法

```html
<!-- 使用 data-action 屬性 -->
<button data-action="remove" data-symbol="AAPL">刪除</button>
<button data-action="analyze" data-symbol="AAPL">分析</button>
<button data-action="trade" data-symbol="AAPL" data-name="Apple" data-market="us" data-type="buy">買入</button>
```

```javascript
// 父容器統一處理
container.addEventListener('click', (e) => {
    const target = e.target.closest('[data-action]');
    if (!target) return;
    
    switch (target.dataset.action) {
        case 'remove':
            removeFromWatchlist(target.dataset.symbol);
            break;
        case 'analyze':
            searchSymbol(target.dataset.symbol);
            break;
        case 'trade':
            quickTrade(
                target.dataset.symbol,
                target.dataset.name,
                target.dataset.market,
                target.dataset.type
            );
            break;
    }
});
```

---

## AppState 整合

### watchlist.js 整合

```javascript
// 載入時同步到 AppState
async function loadWatchlist() {
    // 檢查是否已有快取
    if (AppState.watchlistLoaded && AppState.watchlist.length > 0) {
        renderWatchlistCards(AppState.watchlist);
        return;
    }
    
    const res = await apiRequest('/api/watchlist/with-prices');
    const data = await res.json();
    
    // 同步到 AppState
    AppState.setWatchlist(data.data);
}

// 新增時樂觀更新
async function addToWatchlist() {
    const res = await apiRequest('/api/watchlist', { method: 'POST', body: {...} });
    
    if (data.success) {
        // 樂觀更新，不等重新載入
        AppState.addToWatchlist({
            symbol,
            asset_type: assetType,
            added_at: new Date().toISOString()
        });
    }
}

// 刪除時更新
async function removeFromWatchlist(symbol) {
    const res = await apiRequest(`/api/watchlist/${symbol}`, { method: 'DELETE' });
    
    if (data.success) {
        AppState.removeFromWatchlist(symbol);
    }
}
```

### portfolio.js 整合

```javascript
// 載入摘要
async function loadPortfolioSummary() {
    const res = await apiRequest('/api/portfolio/summary');
    const data = await res.json();
    
    if (data.success) {
        // 同步到 AppState
        AppState.setPortfolio({ summary: data.data });
    }
}

// 載入持股
async function loadHoldings() {
    const res = await apiRequest('/api/portfolio/holdings');
    const data = await res.json();
    
    if (data.success) {
        AppState.setPortfolio({
            tw: data.data.tw || [],
            us: data.data.us || []
        });
    }
}
```

---

## 支援的 data-action

### watchlist.js

| action | 參數 | 說明 |
|--------|------|------|
| `sort` | field | 排序 |
| `remove` | symbol | 移除追蹤 |
| `analyze` | symbol | 詳細分析 |
| `trade` | symbol, name, market, type | 快速交易 |
| `target-price` | id, symbol, target | 設定目標價 |
| `assign-tag` | id, symbol | 指派標籤 |
| `filter-tag` | tagId | 篩選標籤 |

### portfolio.js

| action | 參數 | 說明 |
|--------|------|------|
| `analyze` | symbol | 詳細分析 |
| `delete-transaction` | id, market | 刪除交易 |
| `switch-tab` | tab | 切換頁籤 |
| `export` | - | 匯出 |
| `show-import` | - | 顯示匯入 Modal |

---

## SELA 命名空間

```javascript
// watchlist
SELA.watchlist.load()
SELA.watchlist.loadOverview()
SELA.watchlist.add()
SELA.watchlist.remove(symbol)
SELA.watchlist.changeSort(field)
SELA.watchlist.exportData()
SELA.watchlist.importData()

// portfolio
SELA.portfolio.load()
SELA.portfolio.loadSummary()
SELA.portfolio.loadHoldings()
SELA.portfolio.loadTransactions(market)
SELA.portfolio.switchTab(tab)
SELA.portfolio.exportData()
SELA.portfolio.importData()
SELA.portfolio.quickTrade(symbol, name, market, type)
```

---

## 部署

```bash
cp static/js/watchlist.js 專案/static/js/
cp static/js/portfolio.js 專案/static/js/

git add .
git commit -m "P3 優化: watchlist + portfolio 事件委託"
git push
```

---

## 效能對比

假設追蹤清單有 20 個項目：

| 指標 | 優化前 | 優化後 | 改善 |
|------|--------|--------|------|
| 監聯器數量 | ~160 個 | 1 個 | -99% |
| 重複載入 | 有 | 使用 AppState 快取 | 減少 API 請求 |
| DOM 查詢 | 每次都查 | 快取 | -90% |

---

## 注意事項

1. **向後兼容**：所有原有全域函數仍可使用
2. **漸進式遷移**：可以逐步將其他模組改用事件委託
3. **AppState 快取**：匯入資料後需要清除快取

```javascript
// 匯入後清除快取
AppState.set('watchlistLoaded', false);
AppState.set('portfolioLoaded', false);
```
