# SELA 圖表終極修復包

## 📁 檔案
```
static/js/chart-fix-final.js
```

## 🚀 部署步驟

### 1. 複製檔案
```bash
cp static/js/chart-fix-final.js /path/to/project/static/js/
```

### 2. 修改 dashboard.html

找到 `</body>` 標籤，在它**之前**加入：

```html
<!-- 圖表終極修復 - 必須放在最後 -->
<script src="/static/js/chart-fix-final.js"></script>
</body>
```

**重要**: 這行必須是最後一個 `<script>` 標籤！

### 3. 清除快取並重新整理
- Chrome: `Ctrl+Shift+R` 或 `Cmd+Shift+R`
- 或在 DevTools → Network → 勾選 "Disable cache"

---

## 🔍 診斷步驟

如果還是不行，請按照以下步驟診斷：

### 步驟 1：打開瀏覽器控制台
- Chrome: `F12` → Console 標籤
- Safari: `Cmd+Option+I` → Console

### 步驟 2：搜尋任意股票（如 AAPL 或 2330）

### 步驟 3：檢查控制台輸出

**正常應該看到：**
```
🔧 [FINAL] chart-fix-final.js 開始載入...
🔧 [FINAL] 安裝函數...
🔒 [FINAL] setChartRange 已鎖定
🔒 [FINAL] renderFullscreenChart 已鎖定
✅ [FINAL] 函數安裝完成
```

### 步驟 4：點擊「圖表」按鈕

**正常應該看到：**
```
📊 [FINAL] _open symbol=AAPL
📊 [FINAL] _setRange days=65
📊 [FINAL] _render days=65
📊 [FINAL] 數據: {labels: 65, prices: 65, ma20: "65✓", ma50: "65✓", ma200: "65✓"}
📊 [FINAL] datasets: 4
✅ [FINAL] 圖表完成
```

### 步驟 5：點擊時間按鈕（1M/3M/6M...）

**正常應該看到：**
```
📊 [FINAL] 按鈕點擊 days=22
📊 [FINAL] _setRange days=22
📊 [FINAL] _render days=22
```

---

## ❌ 常見問題

### 問題 1：看不到 [FINAL] 日誌
**原因**: `chart-fix-final.js` 沒有載入

**檢查**:
1. 檢查 dashboard.html 是否有加入 `<script src="/static/js/chart-fix-final.js"></script>`
2. 檢查檔案路徑是否正確
3. 在控制台輸入 `typeof setChartRange` 應該回傳 `"function"`

### 問題 2：MA 數據顯示 "0✗"
**原因**: 後端沒有傳送 MA 數據

**檢查**:
在控制台輸入：
```javascript
console.log(window.currentChartData)
```

檢查 `ma20`、`ma50`、`ma200` 是否有數據。

如果是空陣列 `[]`，代表後端問題，需要檢查：
- `app/services/indicator_service.py`
- `app/routers/stock.py` 的 `chart_data` 生成部分

### 問題 3：按鈕點擊無反應
**原因**: 可能有其他 JavaScript 錯誤

**檢查**:
查看控制台是否有紅色錯誤訊息

---

## 📞 回報問題

請提供以下資訊：
1. 控制台完整輸出（搜尋股票後的所有日誌）
2. `console.log(window.currentChartData)` 的輸出
3. 控制台是否有錯誤訊息（紅色）
4. 瀏覽器類型和版本
