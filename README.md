# SELA 修復包 2026-01-17

## 📦 包含修復

### 🚀 效能優化
- 非開盤時間直接使用本地資料（不呼叫 API）
- 優先顯示永久資料，體感速度大幅提升
- 查詢過的加密貨幣自動快取

### 🔧 圖表修復
- 時間範圍按鈕無法點擊 ✅
- 圖例無法點擊切換顯示/隱藏 ✅
- 圖表右邊空白太小 ✅

---

## 📁 檔案結構

```
sela-fix-20260117/
├── app/
│   ├── routers/
│   │   ├── crypto.py          # 加密貨幣快取修復
│   │   ├── stock.py           # 效能優化（非開盤不呼叫 API）
│   │   └── watchlist.py       # 回傳市場狀態
│   └── services/
│       └── price_cache_service.py  # 智慧快取判斷
├── static/
│   ├── css/
│   │   └── chart-fix.css      # 圖表樣式修復
│   └── js/
│       ├── chart-buttons-fix.js    # 按鈕修復 Patch
│       └── search/
│           └── search-render.js    # 完整圖表修復
└── README.md
```

---

## 🔧 部署步驟

### 1. 後端檔案（必須）
```bash
cp app/routers/crypto.py /path/to/project/app/routers/
cp app/routers/stock.py /path/to/project/app/routers/
cp app/routers/watchlist.py /path/to/project/app/routers/
cp app/services/price_cache_service.py /path/to/project/app/services/
```

### 2. 前端檔案（圖表修復）

**方式 A：完整替換**
```bash
cp static/js/search/search-render.js /path/to/project/static/js/search/
```

**方式 B：Patch 模式（推薦）**
```bash
cp static/js/chart-buttons-fix.js /path/to/project/static/js/
cp static/css/chart-fix.css /path/to/project/static/css/
```

然後在 `dashboard.html` 的 `</body>` 前加入：
```html
<link rel="stylesheet" href="/static/css/chart-fix.css">
<script src="/static/js/chart-buttons-fix.js"></script>
```

### 3. 重啟服務
```bash
# Railway 會自動重啟
# 或手動：
railway up
```

---

## ⚡ 效能提升預期

| 場景 | 舊版 | 新版 |
|-----|------|------|
| 非開盤查詢股票（有資料） | 1-3 秒 | < 100ms ⚡ |
| 非開盤追蹤清單載入 | 500ms-2s | < 50ms ⚡ |
| 開盤中查詢 | 不變 | 不變 |

---

## 🧪 測試檢查清單

- [ ] 非開盤時間查詢台股，應該毫秒級回應
- [ ] 查詢 BTC/ETH 後，檢查 `stock_price_cache` 表有記錄
- [ ] 圖表按鈕 (1M/3M/6M...) 可以點擊切換
- [ ] 圖例可以點擊隱藏/顯示線條
- [ ] 圖表右邊有足夠空白

---

## 📝 API 變更

### `/api/stock/{symbol}`
新增欄位：
```json
{
  "market_open": false  // 市場是否開盤
}
```

### `/api/watchlist/with-prices`
新增欄位：
```json
{
  "market_status": {
    "tw_open": false,
    "us_open": true,
    "crypto_open": true
  }
}
```
