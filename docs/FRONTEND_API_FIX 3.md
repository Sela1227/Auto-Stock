# 🔧 前端 API 端點修復指南

## 問題說明

目前前端使用了**錯誤的** sentiment API 端點，導致每次載入都直接打外部 API，而不是使用資料庫快取。

### 端點對比

| 端點 | 定義位置 | 是否使用 DB 快取 | 狀態 |
|------|----------|------------------|------|
| `/api/market/sentiment` | stock.py | ❌ 否，直接打外部 API | 前端目前使用 |
| `/market/sentiment` | market.py | ✅ 是，優先讀 DB | **應該使用** |

---

## 需要修改的檔案

### `static/js/dashboard.js`

找到以下程式碼並修改：

#### 修改 1: loadSentiment 函數

```javascript
// ❌ 原本 (錯誤)
async function loadSentiment() {
    try {
        const res = await fetch('/api/market/sentiment');
        // ...
    }
}

// ✅ 修改後 (正確)
async function loadSentiment() {
    try {
        const res = await fetch('/market/sentiment');  // 移除 /api 前綴
        // ...
    }
}
```

#### 修改 2: loadSentimentModalChart 函數

```javascript
// ❌ 原本 (錯誤)
async function loadSentimentModalChart(days) {
    // ...
    const res = await fetch(`/api/market/sentiment/${currentSentimentMarket}/history?days=${days}`);
    // ...
}

// ✅ 修改後 (正確)
async function loadSentimentModalChart(days) {
    // ...
    const res = await fetch(`/market/sentiment/${currentSentimentMarket}/history?days=${days}`);
    // ...
}
```

---

## 快速修復命令

在專案目錄執行：

```bash
# macOS / Linux
sed -i '' 's|/api/market/sentiment|/market/sentiment|g' static/js/dashboard.js

# Linux (無 '')
sed -i 's|/api/market/sentiment|/market/sentiment|g' static/js/dashboard.js

# Windows PowerShell
(Get-Content static/js/dashboard.js) -replace '/api/market/sentiment', '/market/sentiment' | Set-Content static/js/dashboard.js
```

---

## 驗證修復

修復後，可以用瀏覽器開發者工具檢查：

1. 開啟 Network 分頁
2. 重新載入頁面
3. 搜尋 "sentiment"
4. 確認請求 URL 是 `/market/sentiment` 而不是 `/api/market/sentiment`

---

## 效果

修復後：
- ✅ 非交易時段：直接從資料庫讀取（毫秒級回應）
- ✅ 交易時段：檢查快取年齡，過期才打外部 API
- ✅ 減少外部 API 調用，降低被限速風險
