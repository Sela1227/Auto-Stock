# 🚀 SELA 部署與運維指南

> 版本: 2.0  
> 最後更新: 2026-01-17  
> 整合自: RAILWAY_SETUP.md、各更新包文件

---

## 1. Railway 部署

### 1.1 添加 PostgreSQL

1. 進入 Railway 專案
2. 點擊 **New** → **Database** → **Add PostgreSQL**
3. 等待資料庫建立完成

### 1.2 取得資料庫連線字串

1. 點擊 PostgreSQL 服務
2. 進入 **Variables** 標籤
3. 複製 `DATABASE_URL`

格式: `postgres://username:password@host:port/database`

### 1.3 設定環境變數

在 **Web Service** 中設定：

```bash
# 資料庫 (推薦使用變數引用)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# LINE Login
LINE_LOGIN_CHANNEL_ID=你的_channel_id
LINE_LOGIN_CHANNEL_SECRET=你的_channel_secret
LINE_LOGIN_CALLBACK_URL=https://你的網域/auth/line/callback

# JWT
JWT_SECRET_KEY=你的隨機密鑰
JWT_EXPIRE_DAYS=7

# 應用程式
APP_ENV=production
DEBUG=false
```

### 1.4 LINE Login 多環境配置

在 LINE Developers Console 的 Callback URL 設定（換行分隔）:
```
https://production.railway.app/auth/line/callback
https://staging.railway.app/auth/line/callback
http://localhost:8000/auth/line/callback
```

---

## 2. 資料庫遷移

### 2.1 重要限制

⚠️ **Railway 一般用戶無法直接執行 SQL**

所有資料庫遷移必須透過 `database.py` 的 `run_migrations()` 函數自動執行。

### 2.2 遷移函數範例

```python
# app/database.py

def run_migrations():
    """自動執行資料庫遷移"""
    with engine.connect() as conn:
        # 新增欄位範例
        conn.execute(text("""
            ALTER TABLE stock_price_cache 
            ADD COLUMN IF NOT EXISTS ma20 NUMERIC(12, 4)
        """))
        
        # 新增表範例
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id SERIAL PRIMARY KEY,
                from_currency VARCHAR(10),
                to_currency VARCHAR(10),
                rate FLOAT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.commit()
```

### 2.3 系統自動建立的表

首次啟動會自動建立以下表：

| 表格 | 說明 |
|------|------|
| users | 用戶資料 (LINE Login) |
| watchlists | 追蹤清單 |
| watchlist_tags | 標籤 |
| stock_price_cache | 股價快取 |
| crypto_prices | 幣價快取 |
| market_sentiment | 市場情緒 |
| index_prices | 四大指數 |
| portfolio_transactions | 交易紀錄 |
| portfolio_holdings | 持股彙總 |
| exchange_rates | 匯率 |
| user_indicator_settings | 指標設定 |
| user_alert_settings | 通知設定 |
| user_indicator_params | 參數設定 |

---

## 3. 排程任務

### 3.1 任務清單

| 時間 | 任務 | ID |
|------|------|-----|
| 每 10 分鐘 | 價格快取更新 | `price_cache_update` |
| 週一~五 13:35 | 台股收盤更新 | `tw_stock_update` |
| 週二~六 05:05 | 美股收盤更新 | `us_stock_update` |
| 每天 09:00 | 匯率更新（早） | `exchange_rate_morning` |
| 每天 12:00 | 匯率更新（中） | `exchange_rate_noon` |
| 每天 17:00 | 匯率更新（晚） | `exchange_rate_evening` |
| 每小時 | 訂閱源抓取 | `subscription_fetch` |

### 3.2 排程設定 (main.py)

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# 價格快取更新（每 10 分鐘）
scheduler.add_job(
    update_price_cache,
    'interval',
    minutes=10,
    id='price_cache_update',
    name='價格快取更新'
)

# 台股收盤更新（週一~五 13:35）
scheduler.add_job(
    update_tw_stocks,
    'cron',
    day_of_week='mon-fri',
    hour=13,
    minute=35,
    id='tw_stock_update',
    name='台股收盤更新'
)

# 美股收盤更新（週二~六 05:05）
scheduler.add_job(
    update_us_stocks,
    'cron',
    day_of_week='tue-sat',
    hour=5,
    minute=5,
    id='us_stock_update',
    name='美股收盤更新'
)

# 訂閱源抓取
scheduler.add_job(
    scheduled_fetch_subscriptions,
    'interval',
    hours=1,
    id='subscription_fetch',
    name='訂閱源抓取(每小時)'
)

scheduler.start()
```

---

## 4. 部署檢查清單

### 4.1 部署前

- [ ] 所有 Python 檔案使用 UTF-8 編碼
- [ ] requirements.txt 已更新
- [ ] 環境變數已設定
- [ ] LINE Callback URL 已添加

### 4.2 部署後

- [ ] 確認容器啟動成功
- [ ] 確認 "Database initialized" 訊息
- [ ] 測試登入功能
- [ ] 測試 API 端點

### 4.3 驗證 API

```bash
# 健康檢查
curl https://your-domain.railway.app/

# 股票查詢
curl https://your-domain.railway.app/api/stock/AAPL

# 加密貨幣
curl https://your-domain.railway.app/api/crypto/BTC

# 市場情緒
curl https://your-domain.railway.app/api/market/sentiment
```

---

## 5. 故障排除

### 5.1 連線失敗

**檢查項目**:
- DATABASE_URL 是否正確
- PostgreSQL 服務是否運行中
- 網路防火牆設定

### 5.2 表格不存在

**解決方案**:
- 檢查日誌確認 "Database initialized" 訊息
- 確認 `run_migrations()` 有被調用
- 嘗試重新部署

### 5.3 SSL 錯誤

在 DATABASE_URL 後面加上：
```
?sslmode=require
```

### 5.4 postgres:// vs postgresql://

Railway 使用 `postgres://`，SQLAlchemy 需要 `postgresql://`。

程式已自動處理轉換：
```python
database_url = os.getenv("DATABASE_URL", "")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
```

### 5.5 Railway 部署卡住

**現象**: "Taking a snapshot of the code" 卡住 24+ 分鐘
**解法**: 取消重新部署，或檢查 Railway 狀態 https://status.railway.app

### 5.6 ModuleNotFoundError

```
ModuleNotFoundError: No module named 'app.services.index_service'
```
**解法**: 檢查 import 路徑是否正確，確認對應模組存在

---

## 6. 監控與日誌

### 6.1 日誌級別

```python
# app/logging_config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### 6.2 關鍵日誌

| 日誌 | 意義 |
|------|------|
| `Starting SELA v0.x.x` | 應用程式啟動 |
| `Database initialized` | 資料庫連線成功 |
| `Scheduler started` | 排程器啟動 |
| `Price cache updated: N stocks` | 價格快取更新完成 |

### 6.3 效能監控

建議監控：
- API 回應時間
- 資料庫查詢次數
- 外部 API 呼叫次數（Yahoo Finance、CoinGecko）
- 記憶體使用量

---

## 7. 備份與還原

### 7.1 資料庫備份

```bash
# 導出
pg_dump $DATABASE_URL > backup.sql

# 導入
psql $DATABASE_URL < backup.sql
```

### 7.2 關鍵備份項目

- 用戶資料 (`users`)
- 追蹤清單 (`watchlists`)
- 交易紀錄 (`portfolio_transactions`)
- 用戶設定 (`user_*_settings`)

---

## 8. 更新部署

### 8.1 標準流程

```bash
# 1. 提交程式碼
git add .
git commit -m "feat: 功能描述"
git push

# 2. Railway 自動偵測並部署

# 3. 驗證
curl https://your-domain.railway.app/
```

### 8.2 需要遷移時

1. 更新 `database.py` 的 `run_migrations()` 函數
2. 正常部署
3. 首次啟動時會自動執行遷移

### 8.3 回滾

在 Railway 控制台選擇之前的部署版本進行回滾

---

## 9. 前端部署步驟

### 9.1 後端修改

```bash
# 替換檔案
cp stock.py app/routers/stock.py
cp price_cache_service.py app/services/price_cache_service.py
```

### 9.2 前端修改

```bash
# 解壓前端修正包
unzip frontend_fix_20260115.zip -d static/
```

### 9.3 部署後驗證清單

1. 查詢股票 → 應顯示完整技術指標和圖表
2. 追蹤清單 → 排序應有「MA20距離」選項
3. 訂閱精選 → 點「+」應顯示「XXX 已加入追蹤清單」
4. 設定頁面 → 應看到「管理員工具」區塊
5. 管理員工具 → 點「抓取訂閱精選」應抓取最新文章
6. 圖表功能 → 時間範圍按鈕可點擊切換
7. MA 均線 → 應正常顯示在圖表中

---

## 10. 資源限制注意

- Railway 免費方案每月約 500 小時，注意用量
- Yahoo Finance API 有請求頻率限制
- CoinGecko 免費 API 有每分鐘請求限制
- PostgreSQL 免費方案有儲存空間限制
