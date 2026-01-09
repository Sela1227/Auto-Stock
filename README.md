# 🚀 追蹤清單價格快取功能

## 概述

將追蹤清單的即時價格改為從資料庫快取讀取，由排程每 10 分鐘批次更新。

**效果**：
- 載入時間從 50-150 秒 → **< 1 秒**
- Yahoo Finance 請求從每次載入都打 → **每 10 分鐘 1 次**

---

## 檔案清單

```
app/
├── models/
│   └── price_cache.py          # 新增：StockPriceCache Model
├── services/
│   └── price_cache_service.py  # 新增：快取服務
├── routers/
│   └── watchlist.py            # 修改：新增 API 端點
├── tasks/
│   └── price_cache_task.py     # 新增：排程任務
└── main.py                     # 修改：註冊排程

frontend/
└── watchlist_with_cache.js     # 新增：前端改用快取 API
```

---

## 整合步驟

### 1️⃣ 新增 Model

將 `app/models/price_cache.py` 複製到專案。

在 `app/models/__init__.py` 加入：
```python
from app.models.price_cache import StockPriceCache
```

### 2️⃣ 建立資料表

執行資料庫遷移或直接執行 SQL：

```sql
CREATE TABLE stock_price_cache (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    price NUMERIC(12, 4),
    prev_close NUMERIC(12, 4),
    change NUMERIC(12, 4),
    change_pct NUMERIC(8, 4),
    volume BIGINT,
    asset_type VARCHAR(10) DEFAULT 'stock',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_asset_type ON stock_price_cache(asset_type);
CREATE INDEX idx_cache_updated ON stock_price_cache(updated_at);
```

### 3️⃣ 新增 Service

將 `app/services/price_cache_service.py` 複製到專案。

### 4️⃣ 修改 watchlist.py 路由

在現有的 `app/routers/watchlist.py` 中加入以下端點：

```python
from app.models.price_cache import StockPriceCache

@router.get("/with-prices", summary="追蹤清單（含即時價格）")
async def get_watchlist_with_prices(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    取得用戶追蹤清單，包含即時價格（從快取讀取）
    """
    # 1. 取得用戶的追蹤清單
    stmt = (
        select(Watchlist)
        .where(Watchlist.user_id == user.id)
        .order_by(Watchlist.added_at.desc())
    )
    result = await db.execute(stmt)
    watchlist_items = list(result.scalars().all())
    
    if not watchlist_items:
        return {"success": True, "data": [], "total": 0}
    
    # 2. 取得所有 symbol
    symbols = [item.symbol for item in watchlist_items]
    
    # 3. 從快取批次取得價格
    cache_stmt = select(StockPriceCache).where(
        StockPriceCache.symbol.in_(symbols)
    )
    cache_result = await db.execute(cache_stmt)
    cached_prices = {r.symbol: r for r in cache_result.scalars().all()}
    
    # 4. 組合資料
    data = []
    for item in watchlist_items:
        cache = cached_prices.get(item.symbol)
        data.append({
            "id": item.id,
            "symbol": item.symbol,
            "asset_type": item.asset_type,
            "note": item.note,
            "added_at": item.added_at.isoformat() if item.added_at else None,
            "name": cache.name if cache else None,
            "price": float(cache.price) if cache and cache.price else None,
            "change": float(cache.change) if cache and cache.change else None,
            "change_pct": float(cache.change_pct) if cache and cache.change_pct else None,
            "price_updated_at": cache.updated_at.isoformat() if cache and cache.updated_at else None,
        })
    
    return {"success": True, "data": data, "total": len(data)}
```

### 5️⃣ 設定排程任務

在 `app/main.py` 加入排程：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.tasks.price_cache_task import price_cache_scheduler

# 建立排程器
scheduler = AsyncIOScheduler()

# 1. 每 10 分鐘執行（自動判斷開盤時間）
#    - 台股開盤 (09:00-13:30) → 更新台股
#    - 美股開盤 (21:30-05:00) → 更新美股  
#    - 加密貨幣 → 24 小時更新
scheduler.add_job(
    price_cache_scheduler.run_update,
    'interval',
    minutes=10,
    id='price_cache_interval',
    name='價格快取更新(每10分鐘)',
)

# 2. 台股收盤後執行一次（週一到週五 13:35）
scheduler.add_job(
    price_cache_scheduler.run_tw_close_update,
    CronTrigger(day_of_week='mon-fri', hour=13, minute=35),
    id='price_cache_tw_close',
    name='台股收盤更新',
)

# 3. 美股收盤後執行一次（週二到週六 05:05）
scheduler.add_job(
    price_cache_scheduler.run_us_close_update,
    CronTrigger(day_of_week='tue-sat', hour=5, minute=5),
    id='price_cache_us_close',
    name='美股收盤更新',
)

# 在 app 啟動時啟動排程
@app.on_event("startup")
async def startup_event():
    scheduler.start()
    # 啟動時執行一次（強制更新所有）
    price_cache_scheduler.run_force_update()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
```

### 6️⃣ 修改前端

用 `frontend/watchlist_with_cache.js` 的內容替換 `dashboard.html` 中的：
- `loadWatchlist()` 函數
- `loadWatchlistOverview()` 函數

---

## API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/watchlist/with-prices` | GET | 取得追蹤清單（含價格，從快取） |
| `/api/watchlist/refresh-cache` | POST | 手動更新快取（管理員） |
| `/api/watchlist/cache-status` | GET | 查看快取狀態 |

---

## 資料流程

```
┌────────────────────────────────────────────────────────────┐
│                    排程任務                                  │
│                                                            │
│  每 10 分鐘:                                                │
│    ├─ 台股開盤 (09:00-13:30)? → 更新台股                    │
│    ├─ 美股開盤 (21:30-05:00)? → 更新美股                    │
│    └─ 加密貨幣 (24小時)       → 更新加密貨幣                 │
│                                                            │
│  收盤後:                                                    │
│    ├─ 13:35 → 台股最終收盤價                                │
│    └─ 05:05 → 美股最終收盤價                                │
│                                                            │
│  更新方式: yf.Tickers() 批次抓取（1 次請求）                  │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                 stock_price_cache 表                        │
│                                                            │
│  symbol    │ name     │ price  │ change_pct │ updated_at  │
│  ──────────┼──────────┼────────┼────────────┼───────────  │
│  0050.TW   │ 元大台灣50│ 150.5  │ 1.2        │ 12:00:00    │
│  AAPL      │ Apple    │ 180.0  │ -0.5       │ 05:05:00    │
│  BTC       │ Bitcoin  │ 45000  │ 2.3        │ 12:00:00    │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│            GET /api/watchlist/with-prices                  │
│                                                            │
│  1. SELECT * FROM watchlists WHERE user_id = ?             │
│  2. SELECT * FROM stock_price_cache WHERE symbol IN (...)  │
│  3. 回傳合併結果                                             │
│                                                            │
│  ⚡ 回應時間: < 100ms                                       │
└────────────────────────────────────────────────────────────┘
```

---

## 開盤時間設定（台灣時間）

| 市場 | 開盤時間 | 更新頻率 |
|------|----------|----------|
| 台股 | 09:00 - 13:30 | 每 10 分鐘 |
| 美股 | 21:30 - 05:00 | 每 10 分鐘 |
| 加密貨幣 | 24 小時 | 每 10 分鐘 |

**收盤後**：只在收盤時間點更新一次（確保有最終收盤價）

---

## 注意事項

1. **首次部署後**：需要等 10 分鐘或手動呼叫 `/api/watchlist/refresh-cache` 才會有資料
2. **新增追蹤**：新追蹤的股票要等下次排程才會有價格
3. **Railway**：確認 APScheduler 在 Railway 上正常運作

---

## 測試

1. 部署後等 10 分鐘
2. 開啟追蹤清單頁面
3. 應該在 1 秒內載入完成
4. 查看 `/api/watchlist/cache-status` 確認快取狀態
