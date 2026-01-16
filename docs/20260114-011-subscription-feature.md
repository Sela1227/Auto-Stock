# SELA 訂閱精選功能

## 功能說明

自動抓取「美股大叔」Substack 文章中提及的股票代碼，用戶可訂閱查看。

### 特點

- **自動抓取**：每小時自動抓取新文章
- **30 天有效期**：每次被提及重新計算，累計提及次數
- **訂閱制**：用戶自選是否訂閱
- **整合價格**：顯示即時價格（來自快取）

---

## 檔案結構

```
app/
├── database.py                         # 資料庫（含遷移）
├── models/
│   └── subscription.py                 # Model: 訂閱源、精選、用戶訂閱
├── services/
│   ├── rss_fetcher.py                  # RSS 爬蟲
│   └── subscription_service.py         # 訂閱服務
├── routers/
│   └── subscription.py                 # API 路由
└── tasks/
    └── subscription_tasks.py           # 排程任務
docs/
└── 20260114-011-subscription-feature.md
```

---

## 部署步驟

### 1. 覆蓋檔案

解壓後覆蓋到專案目錄

### 2. 在 main.py 註冊路由

```python
from app.routers import subscription
app.include_router(subscription.router)
```

### 3. 在 main.py 加入排程任務

找到 `scheduler` 設定的地方，加入：

```python
from app.tasks.subscription_tasks import scheduled_fetch_subscriptions

# 每小時抓取訂閱源
scheduler.add_job(
    scheduled_fetch_subscriptions,
    'interval',
    hours=1,
    id='subscription_fetch',
    name='訂閱源抓取(每小時)',
)
```

### 4. 安裝依賴

```bash
pip install feedparser beautifulsoup4
```

或加入 `requirements.txt`：

```
feedparser>=6.0.0
beautifulsoup4>=4.12.0
```

### 5. 部署後初始化

訪問一次（回溯抓取 30 天）：

```
POST /api/subscription/admin/init
POST /api/subscription/admin/fetch?backfill=true
```

---

## API 說明

### 訂閱源

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/subscription/sources` | 所有訂閱源 |
| GET | `/api/subscription/sources/{slug}` | 單一訂閱源 |

### 用戶訂閱

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/subscription/my` | 我的訂閱 |
| POST | `/api/subscription/subscribe/{source_id}` | 訂閱 |
| DELETE | `/api/subscription/unsubscribe/{source_id}` | 取消訂閱 |

### 精選列表

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/subscription/picks` | 我的訂閱精選（需登入）|
| GET | `/api/subscription/picks/{source_slug}` | 特定來源精選（公開）|

### 管理

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/subscription/admin/init` | 初始化訂閱源 |
| POST | `/api/subscription/admin/fetch?backfill=true` | 回溯抓取 |

---

## 資料流程

```
每小時排程
    │
    ├─► GET unclestocknotes.substack.com/feed
    │
    ├─► 解析 RSS 文章
    │
    ├─► 正則提取股票代碼
    │   - $AAPL 格式（高可信度）
    │   - (AAPL) 括號格式
    │   - 已知代碼白名單
    │
    ├─► 過濾常見詞（THE, AND, ETF...）
    │
    └─► 寫入 auto_picks
        - 新代碼：建立，expires_at = 30天後
        - 舊代碼：更新 last_seen_at、重算 expires_at、mention_count++
```

---

## 提及次數說明

```
NVDA 第一次提及 (1/14)
├─► expires_at = 2/14
├─► mention_count = 1

NVDA 第二次提及 (1/20)
├─► expires_at = 2/20（重算）
├─► mention_count = 2

NVDA 第三次提及 (2/15)
├─► expires_at = 3/15（重算）
├─► mention_count = 3
```

---

## 前端整合（待完成）

之後會在 dashboard.html 新增「📡 訂閱精選」Tab
