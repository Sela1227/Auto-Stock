# CLAUDE.md — AutoStock 開發交接文件
> 專門給 Claude 讀。讀完即可繼續開發，不需要問問題。
> 版本歷史保持在 README.md。

---

## 一、系統是什麼

**AutoStock — SELA 多用戶自動選股分析系統**

- 股票與加密貨幣技術分析 Web App
- 全端：FastAPI 後端 + Vanilla JS 前端 + PostgreSQL 資料庫
- 部署於 Railway（含 PostgreSQL）
- 手機優先，響應式設計，Tailwind CSS
- 支援台股（.TW/.TWO）、美股、加密貨幣（BTC/ETH）

---

## 二、技術棧

```
前端：Vanilla JavaScript + Tailwind CSS + Chart.js
後端：Python 3.11 + FastAPI + Uvicorn
ORM：SQLAlchemy 2.0
資料庫：PostgreSQL（Railway 內建）
排程：APScheduler
股票數據：Yahoo Finance（yfinance，免費）
加密貨幣：CoinGecko API（免費）
情緒指數：CNN Fear & Greed + Alternative.me（免費）
登入：LINE Login + JWT
通知：LINE Messaging API
```

---

## 三、UI 規範

### CSS 框架
Tailwind CSS（CDN 載入）

### 主要顏色
```css
藍色系：bg-blue-500, text-blue-600（主要操作、美股）
綠色系：bg-green-500, text-green-600（上漲、成功）
紅色系：bg-red-500, text-red-600（下跌、警告）
橘色系：bg-orange-500, text-orange-600（加密貨幣）
灰色系：bg-gray-100, text-gray-600（背景、次要）
```

### 品牌
- App 名稱：AutoStock
- 品牌：SELA
- 登入：LINE Login

### 版本號（每次發布必更新）
```python
# backend: app/config.py
APP_VERSION = "1.0.0"
APP_NAME = "AutoStock 自動選股系統"
```

---

## 四、專案結構

```
autostock/
├── README.md               ← 使用者/部署說明
├── CLAUDE.md               ← 本文件（給 Claude）
├── railway.json            ← Railway 部署設定
├── requirements.txt        ← Python 依賴
├── runtime.txt             ← Python 版本（3.11.0）
│
├── app/
│   ├── __init__.py
│   ├── main.py             ← FastAPI 入口 + 排程設定（優化版）
│   ├── config.py           ← 環境變數 + 版本號
│   ├── database.py         ← SQLAlchemy 連線 + 遷移
│   ├── logging_config.py   ← 日誌設定
│   │
│   ├── models/             ← SQLAlchemy Models
│   ├── routers/            ← API 路由
│   ├── services/           ← 商業邏輯
│   ├── data_sources/       ← 外部資料來源
│   ├── dependencies/       ← FastAPI 依賴注入
│   └── tasks/              ← 排程任務
│
├── static/
│   ├── index.html          ← 登入頁
│   ├── dashboard.html      ← 主頁面（SPA）
│   ├── css/
│   └── js/
│
├── migrations/             ← 資料庫遷移腳本
└── scripts/                ← 工具腳本
```

---

## 五、技術指標

| 指標 | 說明 | 欄位名（小寫）|
|------|------|--------------|
| MA | 移動平均線 | ma5, ma10, ma20, ma60, ma120, ma240 |
| RSI | 相對強弱指數（14日）| rsi |
| MACD | 指數平滑異同移動平均 | macd_dif, macd_dea, macd_hist |
| KD | 隨機指標（9日）| kd_k, kd_d |
| 布林通道 | Bollinger Bands（20日）| bb_upper, bb_middle, bb_lower |
| OBV | 能量潮 | obv |

**重要**：indicator_service.py 產生的欄位都是**小寫**，routers 讀取時也必須用小寫。

---

## 六、市場情緒分級

| 數值 | 分類 | 意義 |
|------|------|------|
| 0-25 | Extreme Fear | 可能買點 |
| 26-45 | Fear | 偏謹慎 |
| 46-55 | Neutral | 觀望 |
| 56-75 | Greed | 偏樂觀 |
| 76-100 | Extreme Greed | 可能賣點 |

---

## 七、關鍵流程

### 價格快取更新（市場感知）
1. 排程檢查是否在交易時段
2. 台股：週一~五 09:00-13:30 台北時間
3. 美股：週一~五 21:30-05:00 台北時間
4. 非交易時段跳過更新，直接使用快取
5. 只更新被用戶追蹤的股票（節省 API 配額）

### 情緒指數快取
1. 每天排程 2 次更新（09:00、21:00）
2. 從 CNN / Alternative.me 抓取後存入 DB
3. API `/market/sentiment` 優先讀 DB，超過 1 天才打外部 API

### LINE Login 流程
1. 前端導向 LINE 授權頁
2. LINE 回調 `/auth/line/callback`
3. 後端用 code 換 access_token + 用戶資料
4. 建立/更新 User，簽發 JWT
5. 重導向前端並帶上 token

---

## 八、排程任務（V1.0.0 優化版）

| 任務 | 時間 | 說明 |
|------|------|------|
| 台股價格更新 | 週一~五 09:00-13:30 每 30 分 | 只在交易時段 |
| 美股價格更新 | 週一~五 21:30-05:00 每 30 分 | 只在交易時段 |
| 台股收盤更新 | 週一~五 13:35 | 強制更新 |
| 美股收盤更新 | 週二~六 05:05 | 強制更新 |
| 情緒指數 | 09:00、21:00 | 存入 DB |
| 匯率更新 | 09:30（工作日）| USD/TWD |
| 訂閱源抓取 | 08:00、18:00 | RSS 解析 |

---

## 九、打包規則

每次發布必須：
1. 更新 `app/config.py` 的 `APP_VERSION`
2. 更新 `README.md` 版本歷程
3. 更新本文件版本欄位

```bash
# 打包 zip
zip -r "AutoStock V1.0.0.zip" "AutoStock V1.0.0/" \
  --exclude "*/venv/*" \
  --exclude "*/__pycache__/*" \
  --exclude "*/.git/*" \
  --exclude "*/.gitignore" \
  --exclude "*/.env" \
  --exclude "*/node_modules/*" \
  --exclude "*/.vscode/*" \
  --exclude "*/.idea/*" \
  --exclude "*.log" \
  --exclude "*/.DS_Store"
```

**版本命名規則**
- 新增功能：+0.1（V1.0.0 → V1.1.0）
- 微小變動 / Bug fix：+0.01（V1.0.0 → V1.01）
- 大改版：+1.0（V1.x → V2.0.0）

---

## 十、版本（當前 V1.0.0）

| 版本 | 日期 | 關鍵變更 |
|------|------|---------|
| V1.0.0 | 2026-04-07 | 優化版：排程減少 60%、智能交易時段判斷、資料庫索引優化、情緒指數 DB 快取 |

---

## 十一、已知問題與修復記錄

### 前端 Bug 修復
1. `showSection` 函數從非導航處調用時沒有 event 對象，需改為可選參數
2. API 返回格式是 `data.stock` 不是 `data.data.stock`
3. `indicator_service` 欄位名用小寫 `ma20/rsi/macd_dif`，routers 需對應

### 交易 API 修復（2026-01-17）
1. 405 錯誤 - 前端路徑多 `/tw` 和 `/us` 後綴，需移除
2. 422 錯誤 - 前端 body 缺 `market` 欄位，需加 `market:'tw'/'us'`
3. 500 錯誤 - 後端 `PortfolioService.create_transaction()` 缺 `broker_id` 參數

### 前端情緒 API
部分頁面仍用 `/api/market/sentiment`（無快取），應改用 `/market/sentiment`

---

## 十二、環境變數

| 變數 | 說明 | 必填 |
|------|------|------|
| DATABASE_URL | PostgreSQL 連線字串（Railway 自動提供）| 是 |
| JWT_SECRET_KEY | JWT 簽名密鑰 | 是 |
| LINE_LOGIN_CHANNEL_ID | LINE Login Channel ID | 是 |
| LINE_LOGIN_CHANNEL_SECRET | LINE Login Channel Secret | 是 |
| LINE_LOGIN_CALLBACK_URL | `https://你的網域/auth/line/callback` | 是 |
| APP_ENV | production / development | 是 |
| LINE_CHANNEL_ACCESS_TOKEN | LINE 推播（選填）| 否 |
