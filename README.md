# 🚀 價格快取功能 - 簡單整合指南

## 效果

| 優化前 | 優化後 |
|--------|--------|
| 追蹤 5 支股票載入 50-150 秒 | **< 1 秒** |

---

## 整合步驟（3 步）

### 步驟 1️⃣：新增/覆蓋後端檔案

複製以下檔案到你的專案：

```
app/models/price_cache.py           → 新增
app/services/price_cache_service.py → 新增
app/routers/watchlist.py            → 覆蓋（已包含新端點）
```

**重要**：在 `app/models/__init__.py` 加入：
```python
from app.models.price_cache import StockPriceCache
```

> 資料表會在應用啟動時自動建立（透過 `Base.metadata.create_all`），不需要手動執行 SQL！

---

### 步驟 2️⃣：修改 main.py 加入排程

參考 `2_add_to_main.py`，加入：

1. **Import APScheduler**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
```

2. **建立排程器和任務**（複製 `2_add_to_main.py` 中的程式碼）

3. **在 startup 事件啟動排程**
```python
@app.on_event("startup")
async def startup_event():
    # 你原有的程式碼...
    scheduler.start()
    update_price_cache_force()  # 啟動時更新一次
```

4. **確認 requirements.txt 有 APScheduler**
```
apscheduler>=3.10.0
```

---

### 步驟 3️⃣：修改前端 dashboard.html

參考 `3_frontend_changes.js`，替換：
- `loadWatchlist()` 函數
- `loadWatchlistOverview()` 函數

主要改動：API 從 `/api/watchlist` 改成 `/api/watchlist/with-prices`

---

## 驗證

部署後，打開瀏覽器訪問：

```
https://你的網域/api/watchlist/cache-status
```

應該看到：
```json
{
  "success": true,
  "total_cached": 5,
  "symbols": ["0050.TW", "AAPL", ...]
}
```

如果 `total_cached: 0`，等 10 分鐘讓排程執行，或重啟應用。

---

## 檔案清單

```
simple_integration/
├── 2_add_to_main.py                # 加到 main.py 的程式碼
├── 3_frontend_changes.js           # 前端修改
├── app/
│   ├── models/
│   │   └── price_cache.py          # 新 Model（自動建表）
│   ├── services/
│   │   └── price_cache_service.py  # 快取服務
│   └── routers/
│       └── watchlist.py            # 完整版（含新端點）
└── README.md
```

---

## 排程時間

| 排程 | 執行時間 | 說明 |
|------|----------|------|
| 每 10 分鐘 | 全天 | 只更新開盤中的市場 |
| 台股收盤 | 13:35 | 確保有最終收盤價 |
| 美股收盤 | 05:05 | 確保有最終收盤價 |

---

## 常見問題

**Q: 為什麼價格顯示「價格更新中...」？**
A: 快取還沒有資料，等 10 分鐘讓排程執行，或重啟應用。

**Q: 新追蹤的股票沒有價格？**
A: 需要等下次排程執行（最多 10 分鐘）。

**Q: 如何手動觸發更新？**
A: 重啟應用會自動執行一次更新。
