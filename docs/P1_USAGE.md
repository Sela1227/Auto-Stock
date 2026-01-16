# P1 狀態管理使用說明

## 概述

P1 新增 `AppState` 統一狀態管理，解決：
- 資料分散在各模組，難以同步
- 狀態變化無法追蹤
- 跨模組通訊困難

---

## 載入順序

```html
<script src="/static/js/utils.js"></script>
<script src="/static/js/core.js"></script>
<script src="/static/js/state.js"></script>   <!-- P1 新增 -->
<script src="/static/js/modals.js"></script>
<!-- 其他模組 -->
```

---

## 基本用法

### 讀取狀態

```javascript
// 取得當前用戶
const user = AppState.user;

// 取得追蹤清單
const watchlist = AppState.watchlist;

// 取得當前 section
const section = AppState.currentSection;
```

### 設置狀態

```javascript
// 設置單一狀態
AppState.set('isLoading', true);

// 批量設置
AppState.setMultiple({
    isLoading: false,
    currentStock: stockData
});

// 使用便捷方法
AppState.setCurrentStock(stockData);
AppState.setWatchlist(list);
AppState.setPortfolio({ tw: twList, us: usList });
```

### 監聽變化

```javascript
// 監聽特定狀態
AppState.on('currentStock', (newStock, oldStock) => {
    console.log('股票切換:', oldStock?.symbol, '→', newStock?.symbol);
    updateStockUI(newStock);
});

// 監聽追蹤清單變化
AppState.on('watchlist', (newList) => {
    renderWatchlist(newList);
});

// 監聽所有變化 (Debug 用)
AppState.on('*', (key, newValue, oldValue) => {
    console.log(`State changed: ${key}`, oldValue, '→', newValue);
});

// 一次性監聽
AppState.once('watchlistLoaded', () => {
    console.log('追蹤清單首次載入完成');
});
```

### 取消監聽

```javascript
// on() 返回取消函數
const unsubscribe = AppState.on('currentStock', handler);

// 之後取消
unsubscribe();

// 或取消所有監聽
AppState.offAll('currentStock');
```

---

## 可用狀態

| 狀態 | 類型 | 說明 |
|------|------|------|
| `user` | Object | 當前用戶 |
| `isAdmin` | Boolean | 是否管理員 |
| `currentSection` | String | 當前頁面 |
| `currentStock` | Object | 當前查看的股票 |
| `searchHistory` | Array | 搜尋歷史 (最多10筆) |
| `watchlist` | Array | 追蹤清單 |
| `watchlistLoaded` | Boolean | 清單是否已載入 |
| `portfolio` | Object | 持股 {tw, us, summary} |
| `tags` | Array | 標籤列表 |
| `indices` | Object | 指數資料 |
| `sentiment` | Object | 市場情緒 |
| `isLoading` | Boolean | 全域載入狀態 |
| `activeModal` | String | 當前開啟的 Modal |

---

## 便捷方法

| 方法 | 說明 |
|------|------|
| `setUser(user)` | 設置用戶並同步 isAdmin |
| `switchSection(name)` | 切換頁面，記錄前一頁 |
| `setCurrentStock(stock)` | 設置股票並加入搜尋歷史 |
| `setWatchlist(list)` | 設置追蹤清單 |
| `addToWatchlist(item)` | 新增到追蹤清單 |
| `removeFromWatchlist(symbol)` | 從追蹤清單移除 |
| `setPortfolio(data)` | 更新持股資料 |
| `setTags(tags)` | 設置標籤 |
| `setLoading(bool)` | 設置載入狀態 |
| `reset()` | 重置所有狀態 (登出時) |

---

## 遷移範例

### 追蹤清單模組

```javascript
// ❌ 舊寫法：各自管理狀態
let watchlistData = [];

async function loadWatchlist() {
    const res = await apiRequest('/api/watchlist');
    const data = await res.json();
    watchlistData = data.data;
    renderWatchlist(watchlistData);
}

// ✅ 新寫法：使用 AppState
async function loadWatchlist() {
    // 避免重複載入
    if (AppState.watchlistLoaded) {
        renderWatchlist(AppState.watchlist);
        return;
    }
    
    AppState.setLoading(true);
    const res = await apiRequest('/api/watchlist');
    const data = await res.json();
    AppState.setWatchlist(data.data);  // 自動設置 watchlistLoaded = true
    AppState.setLoading(false);
}

// 監聽變化自動更新 UI
AppState.on('watchlist', renderWatchlist);
```

### 搜尋模組

```javascript
// ❌ 舊寫法
let currentChartData = null;

function renderSearchResult(data) {
    currentChartData = data.chart_data;
    window.currentChartData = currentChartData;  // 全域污染
    // ...
}

// ✅ 新寫法
function renderSearchResult(data) {
    AppState.setCurrentStock({
        symbol: data.symbol,
        name: data.name,
        price: data.price,
        chartData: data.chart_data
    });
}

// 其他模組可以監聽
AppState.on('currentStock', (stock) => {
    // 自動更新相關 UI
});
```

---

## Debug 模式

```javascript
// 開啟 Debug 模式，會 log 所有狀態變化
window.SELA_DEBUG = true;

// Console 輸出範例:
// 📊 State: currentSection dashboard → watchlist
// 📊 State: watchlist [] → [{...}, {...}]
```

---

## 注意事項

1. **避免直接修改**：使用 `set()` 而不是直接賦值 `AppState.xxx = value`
2. **異步載入**：state.js 需在 core.js 之後載入
3. **向後兼容**：舊代碼仍可運作，可逐步遷移
