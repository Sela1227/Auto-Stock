# CLAUDE.md — AutoStock 開發交接文件
> 專門給 Claude 讀。讀完即可繼續開發，不需要問問題。

---

## 一、系統是什麼

**AutoStock — SELA 多用戶自動選股分析系統**

- 股票與加密貨幣技術分析 Web App
- 全端：FastAPI 後端 + Vanilla JS 前端 + PostgreSQL 資料庫
- 部署於 Railway（含 PostgreSQL Plugin）
- 手機優先，響應式設計，Tailwind CSS
- 支援台股（.TW/.TWO）、美股、加密貨幣（BTC/ETH）

**當前版本：V1.12.3**

---

## 二、技術棧

```
前端：Vanilla JavaScript + Tailwind CSS + Chart.js
後端：Python 3.11 + FastAPI + Uvicorn
ORM：SQLAlchemy 2.0（Async + Sync 混用）
資料庫：PostgreSQL（Railway 內建）
排程：APScheduler（CronTrigger）
股票數據：Yahoo Finance（yfinance，免費）
加密貨幣：CoinGecko API（免費）
情緒指數：CNN Fear & Greed + Alternative.me（免費）
登入：LINE Login + JWT（python-jose）
通知：LINE Messaging API
```

---

## 三、專案結構

```
autostock/
├── CLAUDE.md               ← 本文件（給 Claude 讀）
├── README.md               ← 使用者/部署說明
├── railway.json            ← Railway 部署設定
├── requirements.txt        ← Python 依賴
├── runtime.txt             ← Python 版本（3.11.0）
│
├── app/
│   ├── main.py             ← FastAPI 入口 + 排程定義
│   ├── config.py           ← 環境變數 + APP_VERSION ← 每次發布必改
│   ├── database.py         ← SQLAlchemy 連線 + 自動遷移
│   ├── logging_config.py   ← 日誌設定
│   │
│   ├── models/             ← SQLAlchemy Models
│   ├── routers/            ← API 路由
│   │   ├── auth.py         ← LINE Login / JWT / debug-log
│   │   ├── admin.py        ← 後台管理（需 is_admin）
│   │   ├── watchlist.py    ← 追蹤清單
│   │   ├── portfolio.py    ← 投資記錄
│   │   ├── stock.py        ← 股票查詢
│   │   ├── stock_info.py   ← 股票基本資料
│   │   ├── market.py       ← 指數 / 情緒
│   │   ├── subscription.py ← 訂閱精選
│   │   ├── settings.py     ← 用戶設定
│   │   ├── broker.py       ← 券商管理
│   │   ├── compare.py      ← 走勢比較
│   │   ├── tags.py         ← 標籤管理
│   │   └── crypto.py       ← 加密貨幣
│   │
│   ├── services/           ← 商業邏輯
│   ├── data_sources/       ← 外部 API（Yahoo / CoinGecko）
│   ├── dependencies/       ← FastAPI 共用依賴注入 ← 認證統一在這
│   │   └── auth.py         ← get_current_user / get_admin_user / get_optional_user
│   └── tasks/              ← APScheduler 排程任務
│
├── static/
│   ├── index.html          ← 登入頁
│   ├── dashboard.html      ← 主頁面（SPA）
│   ├── admin.html          ← 管理後台
│   ├── compare.html        ← 走勢比較
│   ├── css/
│   └── js/
│       ├── core.js         ← 認證、session、版本號、共用函數
│       ├── state.js        ← AppState 全域狀態
│       ├── utils.js        ← 格式化工具函數
│       ├── layout.js       ← 側欄、導航
│       ├── dashboard.js    ← 儀表板
│       ├── watchlist.js    ← 追蹤清單
│       ├── portfolio.js    ← 投資記錄
│       ├── transaction.js  ← 交易記錄
│       ├── search.js       ← 股票搜尋
│       ├── sections.js     ← 各 section 切換
│       ├── settings.js     ← 設定頁
│       ├── broker.js       ← 券商管理
│       ├── subscription.js ← 訂閱精選
│       └── admin.js        ← 管理後台
│
├── migrations/             ← 補充遷移 SQL
├── scripts/                ← 工具腳本
└── docs/                   ← 開發文件
```

---

## 四、認證架構（重要）

### 統一入口：`app/dependencies/auth.py`

```python
from app.dependencies import get_current_user, get_admin_user, get_optional_user
```

三個 Depends 函數，**所有 router 一律從這裡 import**，禁止自行重複實作：

| 函數 | 用途 | 失敗行為 |
|------|------|---------|
| `get_current_user` | 任何登入用戶 | 401 |
| `get_admin_user` | 管理員才能存取 | 401 / 403 |
| `get_optional_user` | 可選登入（無 token 回 None）| 無 |

### JWT 特性

- 一般用戶 token 有效期：**10 分鐘**（`JWT_EXPIRE_MINUTES_USER`）
- 管理員 token 有效期：**60 分鐘**（`JWT_EXPIRE_MINUTES_ADMIN`）
- Token 被踢出機制：`SystemConfig` 表的 `global_token_version` / `user_token_version:{id}`
- Payload 含：`sub`（user_id）、`line_user_id`、`display_name`、`is_admin`、`jti`

### LINE Login 流程

```
前端 → GET /auth/line → 導向 LINE 授權頁
LINE → GET /auth/line/callback?code=...&state=...
     → 驗證 state（HMAC-SHA256，10分鐘有效）
     → exchange code → access_token
     → 取 LINE profile
     → 建立/更新 User in DB
     → 簽發 JWT，寫入 localStorage
     → 導向 /static/dashboard.html
```

**XSS 防護**：callback HTML 用 `json.dumps` + HTML escape 傳遞用戶資料，禁止直接字串插值。

---

## 五、資料庫 Session 規則

### Async（router/endpoint 用）

```python
from app.database import get_async_session
db: AsyncSession = Depends(get_async_session)
```

### Sync（排程任務 / 背景工作用）

```python
# main.py 提供的 context manager，不要自己開關 session
from app.main import sync_db_session

with sync_db_session() as db:
    MyService(db).do_something()
```

**禁止**在 router 裡直接 `SyncSessionLocal()` — 那是排程專用。

---

## 六、技術指標欄位名

| 指標 | 欄位名（全小寫）|
|------|--------------|
| MA | ma5, ma10, ma20, ma60, ma120, ma240 |
| RSI | rsi |
| MACD | macd_dif, macd_dea, macd_hist |
| KD | kd_k, kd_d |
| 布林通道 | bb_upper, bb_middle, bb_lower |
| OBV | obv |

**indicator_service.py 輸出全小寫，router 讀取也必須用小寫。**

---

## 七、前端規範

### API 呼叫

```js
// 統一用 window.apiRequest（core.js 提供）
const data = await apiRequest('/auth/me');
// 回傳格式：data.xxx（不是 data.data.xxx）
```

### 版本號顯示

版本號在 4 個地方顯示，由 `core.js` 的 `loadAppVersion()` 統一從 `/api/version` 拉取後更新：
- `#headerVersion`（桌面 header）
- `#mobileVersion`（手機 header）
- `#sidebarVersion`（側欄）
- `#settingsVersion`（設定頁）

config.py 改了版本號後，部署即自動反映，**禁止在 HTML 裡寫死版本字串**。

### `showSection` 注意

```js
// event 參數必須是可選的，因為也從非導航處調用
function showSection(name, event = null) { ... }
```

### is_admin 判斷

管理後台入口顯示：由 `/auth/me` 回傳的 `serverUser.is_admin` 決定（server 來源）。  
Session timeout：也從 `currentUser`（server 驗證後）讀取，**不從 localStorage.is_admin 讀**。

---

## 八、排程任務

| 任務 | 時間（台北）| 說明 |
|------|------------|------|
| 台股價格更新 | 週一~五 09:00-13:30 每 30 分 | 只在交易時段 |
| 美股價格更新 | 週一~五 21:30-05:00 每 30 分 | 只在交易時段 |
| 台股收盤更新 | 週一~五 13:35 | 強制更新 |
| 美股收盤更新 | 週二~六 05:05 | 強制更新 |
| 情緒指數 | 09:00、21:00 | 存入 DB |
| 匯率更新 | 09:30（工作日）| USD/TWD |
| 訂閱源抓取 | 08:00、18:00 | RSS 解析 |

**市場感知快取**：非交易時段直接回傳 DB 快取，不打外部 API，節省 Railway 費用。

---

## 九、資安規範

| 類別 | 規範 |
|------|------|
| XSS | callback HTML 一律 `json.dumps` + HTML escape，禁止字串插值 |
| CSRF | State token = HMAC-SHA256 簽名，10 分鐘有效 |
| State log | 只印前8+後4字元，不寫完整 state |
| Rate limit | `/auth/debug-log`：每 IP 每分鐘最多 20 次 |
| 認證 | 管理員操作一律 `Depends(get_admin_user)` |
| Session | is_admin 從 server 回傳讀取，非 localStorage |

---

## 十、已知問題與修復記錄

### 交易 API 修復（2026-01-17）
1. **405 錯誤**：前端路徑多 `/tw`/`/us` 後綴 → 移除
2. **422 錯誤**：前端 body 缺 `market` 欄位 → 加 `market:'tw'/'us'`
3. **500 錯誤**：`PortfolioService.create_transaction()` 缺 `broker_id` 參數

### 前端 API 格式
- 回傳格式：`data.stock`（不是 `data.data.stock`）
- indicator_service 欄位：小寫 `ma20`/`rsi`/`macd_dif`

### `/api/market/sentiment` vs `/market/sentiment`
- `/api/market/sentiment`：繞過快取，直接打外部 API（**避免使用**）
- `/market/sentiment`：優先讀 DB 快取（**應使用這個**）

---

## 十一、環境變數

| 變數 | 說明 | 必填 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 連線字串（Railway 自動提供）| ✅ |
| `JWT_SECRET_KEY` | JWT 簽名密鑰（隨機長字串）| ✅ |
| `LINE_LOGIN_CHANNEL_ID` | LINE Login Channel ID | ✅ |
| `LINE_LOGIN_CHANNEL_SECRET` | LINE Login Channel Secret | ✅ |
| `LINE_LOGIN_CALLBACK_URL` | `https://你的網域/auth/line/callback` | ✅ |
| `APP_ENV` | `production` / `development` | ✅ |
| `ADMIN_LINE_IDS` | 管理員 LINE User ID（逗號分隔）| 建議 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE 推播 | 選填 |
| `JWT_EXPIRE_MINUTES_USER` | 一般用戶 token 期限（預設 10）| 選填 |
| `JWT_EXPIRE_MINUTES_ADMIN` | 管理員 token 期限（預設 60）| 選填 |

---

## 十二、打包規則

每次發布前必須：
1. 更新 `app/config.py` 的 `APP_VERSION`
2. 更新本文件的「當前版本」與版本歷史
3. 更新 `README.md`

```bash
zip -r "AutoStock V版本號.zip" "AutoStock V版本號/" \
  --exclude "*.git*" --exclude "*__pycache__*" \
  --exclude "*.env" --exclude "*/venv/*" \
  --exclude "*.log" --exclude ".DS_Store" --exclude "*.pyc"
```

**版本命名規則**
- 新功能：+0.1（V1.12 → V1.13）
- Bug fix / 小改：+0.01（V1.12 → V1.12.1）
- 大改版：+1.0（V1.x → V2.0）

---

## 十三、版本歷史

| 版本 | 日期 | 關鍵變更 |
|------|------|---------|
| V1.12.3 | 2026-04-12 | 修復情緒指數顯示：`loadSentiment` 和 `loadSentimentDetail` 的 `data.data?.stock` 改回 `data.stock`（`/api/market/sentiment` 回傳頂層欄位，不是 `data` 包一層）|
| V1.12.2 | 2026-04-12 | JS 語法修復（core.js try/catch、dashboard.js 多處缺 `}`）；favicon 新增；移除 404 的 target-price-fix.js；資安強化（XSS json.dumps、rate limit、state log 遮蔽）；重構消除重複（Bearer 解析、sync_db_session、get_current_user）；情緒指數多來源（feargreedmeter、alternative.me 備用）＋ DB 12 小時新鮮度檢查；版本號動態顯示修復（設定頁、admin 自動載入日誌）|
| V1.12.1 | 2026-04-10 | 修復啟動 crash（`NameError: User`）|
| V1.12 | 2026-04-10 | 前端診斷日誌（`/auth/debug-log`）；管理後台自動顯示診斷區塊 |
| V1.11 | — | 前端 JS 性能優化（P0–P4）：DOM 快取、批量更新、命名空間 |
| V1.10 | — | 版本號動態顯示；cache-only 市場指數/情緒載入 |
| V1.05 | — | 預計算技術指標快取；清除過期快取排程 |
| V1.02 | — | 極簡排程：只在交易時段更新，大幅降低 Railway 費用 |
| V1.01 | — | 內存快取：非交易時段回傳 DB 快取，10-40x 性能提升 |
| V1.00 | 2026-04-07 | 完整功能上線：台股/美股/加密貨幣/追蹤/投資記錄/訂閱/報酬比較 |
