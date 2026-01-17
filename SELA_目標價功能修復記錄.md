# SELA 目標價功能修復記錄

**日期**: 2026-01-17  
**版本**: v2.0 - 高於/低於方向功能

---

## 📋 功能需求

1. 設定目標價時可選擇「高於時提醒」或「低於時提醒」
2. 追蹤清單顯示目標價標記（區分方向）
3. 儲存/清除目標價後即時更新畫面

---

## 🐛 問題診斷過程

### 問題 1：API 路徑不匹配
- **現象**：設定目標價失敗 404
- **原因**：前端呼叫 `/api/watchlist/${id}/target`，後端定義 `/{item_id}/target-price`
- **解法**：統一使用 `/target-price`

### 問題 2：direction 變數未定義
- **現象**：`UnboundLocalError: cannot access local variable 'direction'`
- **原因**：補丁把 `direction` 放在 `if` 區塊外，但只在內部定義
- **解法**：將 `direction` 定義移到 `if current_price and target_price:` 區塊內

### 問題 3：numpy 類型無法序列化
- **現象**：股票查詢 500 錯誤，`TypeError: 'numpy.int64' object is not iterable`
- **原因**：MA 進階分析返回 numpy 類型
- **解法**：加入 `_to_python_type()` 輔助函數轉換

### 問題 4：Modal 沒有方向選擇 UI
- **現象**：Modal 只有價格輸入，沒有高於/低於選項
- **解法**：更新 `modals.js` 中的 `targetPriceModal` 模板

### 問題 5：showTargetPriceModal 沒傳 direction 參數
- **現象**：方向選擇無效
- **原因**：事件處理器只傳 3 個參數，缺少第 4 個 `direction`
- **解法**：修正 watchlist.js 事件處理

### 問題 6：儲存後沒有即時更新標記（關鍵！）
- **現象**：設定成功有 Toast，但標記沒更新
- **診斷過程**：
  1. 確認 `saveTargetPrice` 被呼叫 ✓
  2. 確認 `loadWatchlist()` 被呼叫 ✓
  3. 確認 API 返回正確資料 ✓
  4. 檢查 DOM 沒有更新 ✗
- **根本原因**：`loadWatchlist()` 有 AppState 快取機制
  ```javascript
  if (window.AppState && AppState.watchlistLoaded && AppState.watchlist.length > 0) {
      renderWatchlistCards(AppState.watchlist);  // 使用舊資料！
      return;
  }
  ```
- **解法**：儲存/清除後先清除快取再重載
  ```javascript
  if (window.AppState) {
      AppState.watchlistLoaded = false;
  }
  await loadWatchlist();
  ```

---

## 📁 修改的檔案

### 1. app/routers/watchlist.py
- Schema 新增 `target_direction: Optional[str] = "above"`
- API 處理 direction 參數
- 回傳資料包含 `target_direction`
- `target_reached` 邏輯區分高於/低於

### 2. app/models/watchlist.py
- 新增欄位 `target_direction = Column(String(10), nullable=True, default='above')`

### 3. app/database.py
- 新增遷移 `add_target_direction_to_watchlists`

### 4. static/js/watchlist.js
- 事件處理器傳入 `direction` 參數
- `showTargetPriceModal` 設定方向 radio 並更新樣式
- `saveTargetPrice` / `clearTargetPrice` 清除 AppState 快取
- 目標價標記顯示加入方向箭頭和顏色區分

### 5. static/js/modals.js
- `targetPriceModal` 新增高於/低於選擇 UI
- 新增 `updateDirectionStyle()` 函數

---

## 🎨 UI 設計

### 方向選擇（Modal）
```
┌─────────────────┬─────────────────┐
│   ↑ 高於時提醒   │   ↓ 低於時提醒   │
│    突破買入      │    跌破停損      │
│  (綠色選中框)    │  (紅色選中框)    │
└─────────────────┴─────────────────┘
```

### 標記顯示（卡片）
| 狀態 | 樣式 |
|------|------|
| 高於未達標 | 🟢 綠底綠框 `↑ 目標 $XX (+X%)` |
| 低於未達標 | 🔴 紅底紅框 `↓ 目標 $XX (-X%)` |
| 已達標 | 🟡 黃色加深+陰影+閃爍 `↑/↓ 已達標 $XX` |

---

## 💡 關鍵學習

### 1. AppState 快取陷阱
當使用全域狀態快取時，修改資料後必須：
- 清除快取標記（`AppState.watchlistLoaded = false`）
- 或直接更新快取資料
- 否則重載會使用舊資料

### 2. 調試技巧
```javascript
// 檢查 DOM 容器
document.querySelector('[data-symbol="XXX"]')?.closest('[id]')?.id

// 檢查 API 回傳
apiRequest('/api/xxx').then(r => r.json()).then(d => console.log(d))

// 檢查函數內容
functionName.toString().includes('關鍵字')
```

### 3. 安全取值
使用 `getattr(item, 'target_direction', 'above')` 確保即使欄位不存在也不會報錯

---

## ✅ 測試檢查清單

- [x] 設定高於目標價 → 顯示綠色標記
- [x] 設定低於目標價 → 顯示紅色標記
- [x] 清除目標價 → 標記消失
- [x] 即時更新（不需刷新頁面）
- [x] 達標時顯示黃色閃爍
- [x] 匯出/匯入包含 direction
