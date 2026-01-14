# SELA 更新包 20260114 - 排序功能 + MA20 支援

## 目錄結構

```
├── static/
│   └── dashboard.html              # 前端排序功能
├── app/
│   ├── models/
│   │   └── price_cache.py          # 快取 Model（加 ma20 欄位）
│   ├── services/
│   │   ├── cache_helper.py         # 快取輔助模組
│   │   └── price_cache_service.py  # 批次更新服務（計算 MA20）
│   └── routers/
│       ├── watchlist.py            # API 返回 ma20
│       └── stock.py                # 查詢時寫入 MA20
└── README.md
```

**所有檔案都是完整版本，直接覆蓋即可。**

---

## 功能說明

### 1. 追蹤清單排序

```
排序： [自訂] [代碼] [漲幅↓] [跌幅↓] [MA20]
```

| 模式 | 說明 |
|------|------|
| 自訂 | 按加入時間（最新在前）|
| 代碼 | A-Z 排序 |
| 漲幅↓ | 漲幅高到低 |
| 跌幅↓ | 漲幅低到高 |
| **MA20** | 站上 MA20 優先 |

### 2. MA20 標籤顯示

```
AAPL  股  Apple Inc.
$185.50  ▲ 2.31%  [站上MA20]
```

| 標籤 | 條件 |
|------|------|
| ▲MA20 | 價格高於 MA20 超過 3% |
| 站上MA20 | 價格高於 MA20 在 0-3% |
| 測MA20 | 價格低於 MA20 在 0-3% |
| ▼MA20 | 價格低於 MA20 超過 3% |

---

## 部署步驟

### 步驟 1: 覆蓋檔案

解壓後直接覆蓋到專案目錄：

```bash
unzip sela-update-20260114.zip -d /path/to/project/
```

### 步驟 2: 修改 main.py（自動遷移）

在 `main.py` 的 `Database initialized` 之後加入：

```python
# --- 自動資料庫遷移 ---
from app.utils.migrations import run_migrations
from app.database import SessionLocal

try:
    db = SessionLocal()
    run_migrations(db)
    db.close()
    logger.info("Database migrations completed")
except Exception as e:
    logger.warning(f"Database migrations failed: {e}")
```

這樣啟動時會自動檢查並添加 `ma20` 欄位。

### 步驟 3: 重新部署

```bash
git add .
git commit -m "feat: 追蹤清單排序 + MA20 支援"
git push
```

---

## 驗證方式

1. 查詢一個股票（如 AAPL）
2. 檢查資料庫：
   ```sql
   SELECT symbol, price, ma20 FROM stock_price_cache WHERE symbol = 'AAPL';
   ```
3. 確認 ma20 欄位有值
4. 前端追蹤清單應顯示 MA20 標籤
5. MA20 排序功能正常

---

## 資料流程

```
用戶查詢股票
    │
    ├─► Yahoo Finance 取得數據
    │
    ├─► 計算技術指標（含 MA20）
    │
    ├─► 寫入 StockPriceCache（含 MA20）
    │
    └─► 回傳結果


管理員登入 / 排程更新
    │
    └─► batch_update_stock_prices
        │
        ├─► 取得 1 個月歷史數據
        │
        ├─► 計算 MA20 = 最近 20 天收盤價平均
        │
        └─► 寫入快取


追蹤清單頁面
    │
    └─► GET /api/watchlist/with-prices
        │
        └─► 從快取讀取（含 ma20 欄位）
            │
            └─► 前端排序 + 顯示標籤
```
