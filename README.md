# 📊 報酬率比較功能 - 前端更新說明

## 檔案說明

- `static/compare.html` - 獨立的報酬率比較頁面

## 部署步驟

1. 將 `static/compare.html` 複製到你的專案 `static/` 目錄
2. 訪問 `/static/compare.html` 即可使用

## 建議：在 Dashboard 加入連結

在 `static/dashboard.html` 的導航區域加入以下連結：

### 桌面版側邊欄 (如果有的話)

```html
<a href="/static/compare.html" class="nav-link flex items-center px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg">
    <i class="fas fa-chart-bar mr-3"></i>
    <span>報酬率比較</span>
</a>
```

### 或在頂部導航加入

```html
<a href="/static/compare.html" class="text-gray-600 hover:text-gray-800">
    📊 報酬率比較
</a>
```

## 功能說明

1. **快速比較** - 使用預設的股票/加密貨幣組合
   - 美國科技股 (AAPL, MSFT, GOOGL, AMZN, NVDA)
   - 主流加密貨幣 (BTC, ETH, SOL, BNB, XRP)
   - 大盤指數 (S&P 500, 納斯達克, 道瓊)
   - 熱門 ETF (SPY, QQQ, VOO, VTI, IWM)
   - 高股息股票 (JNJ, PG, KO, PEP, VZ)

2. **自訂比較** - 手動輸入最多 5 個標的

3. **比較維度**
   - 時間週期：1年、3年、5年、10年
   - 基準指數：S&P 500、納斯達克、道瓊工業
   - 排序方式：依不同週期報酬率排序

4. **我的組合** - 登入後可儲存/載入自訂組合

## API 端點

| 端點 | 說明 |
|------|------|
| `GET /api/compare/presets` | 取得預設組合列表 |
| `GET /api/compare/quick/{id}` | 快速比較預設組合 |
| `POST /api/compare/cagr` | 執行自訂比較 |
| `GET /api/compare/saved` | 取得我的組合 (需登入) |
| `POST /api/compare/saved` | 儲存組合 (需登入) |
| `DELETE /api/compare/saved/{id}` | 刪除組合 (需登入) |
