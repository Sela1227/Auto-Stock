# 📈 SELA 系統規格書

> 版本: 2.0  
> 最後更新: 2026-01-17  
> 專案: SELA 多用戶自動選股分析系統

---

## 1. 專案概述

### 1.1 核心特色

| 特色 | 說明 |
|------|------|
| 多用戶支援 | LINE 登入，每人獨立追蹤清單與投資組合 |
| 共享資料庫 | 股價資料共用，減少 API 呼叫 |
| 彈性指標 | 用戶可自選要顯示/通知的指標 |
| 智能預警 | 突破、交叉、極端值自動推播 |
| 雙市場 | 同時支援美股、台股與加密貨幣 |
| 市場感知快取 | 非交易時段直接使用快取，大幅提升效能 |

### 1.2 支援資產

| 類型 | 標的 | 來源 |
|------|------|------|
| 美股 | 所有 Yahoo Finance 支援的股票 | Yahoo Finance |
| 台股 | Yahoo Finance 台股 (.TW / .TWO) | Yahoo Finance |
| 加密貨幣 | BTC、ETH | CoinGecko |

---

## 2. 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                        前端介面                              │
│              (Web 應用程式 - dashboard.html)                 │
├─────────────────────────────────────────────────────────────┤
│                        API 層 (FastAPI)                      │
│    ├─ auth.py          用戶驗證 (LINE Login)                 │
│    ├─ stock.py         股票查詢                              │
│    ├─ crypto.py        加密貨幣查詢                          │
│    ├─ watchlist.py     追蹤清單管理                          │
│    ├─ portfolio.py     投資組合管理                          │
│    ├─ subscription.py  訂閱精選                              │
│    ├─ settings.py      用戶設定                              │
│    └─ admin.py         管理功能                              │
├─────────────────────────────────────────────────────────────┤
│                      商業邏輯層 (Services)                    │
│    ├─ indicator_service.py    技術指標計算                   │
│    ├─ signal_service.py       訊號偵測                       │
│    ├─ price_cache_service.py  市場感知快取 ⭐                │
│    ├─ chart_service.py        圖表生成                       │
│    └─ portfolio_service.py    投資組合計算                   │
├─────────────────────────────────────────────────────────────┤
│                       資料庫層 (PostgreSQL)                   │
│    ├─ 共享資料 (股價快取、情緒指數、指數價格)                 │
│    └─ 私有資料 (用戶、追蹤清單、投資組合、設定)               │
├─────────────────────────────────────────────────────────────┤
│                    外部資料來源                               │
│    ├─ Yahoo Finance (美股/台股)                              │
│    ├─ CoinGecko (加密貨幣)                                   │
│    ├─ CNN Fear & Greed (美股情緒)                            │
│    └─ Alternative.me (幣圈情緒)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 專案目錄結構

```
sela-stock-analysis/
├── app/
│   ├── data_sources/           # 外部資料來源
│   │   ├── yahoo_finance.py    # 美股/台股
│   │   ├── coingecko.py        # 加密貨幣
│   │   ├── fear_greed.py       # 情緒指數
│   │   └── taiwan_stocks.py    # 台股名稱對照
│   ├── models/                 # 資料模型
│   │   ├── user.py             # 用戶
│   │   ├── watchlist.py        # 追蹤清單
│   │   ├── watchlist_tag.py    # 標籤
│   │   ├── portfolio.py        # 投資組合
│   │   ├── price_cache.py      # 價格快取
│   │   ├── subscription.py     # 訂閱精選
│   │   └── user_settings.py    # 用戶設定
│   ├── routers/                # API 路由
│   │   ├── auth.py             # 認證
│   │   ├── stock.py            # 股票查詢
│   │   ├── crypto.py           # 加密貨幣
│   │   ├── watchlist.py        # 追蹤清單
│   │   ├── portfolio.py        # 投資組合
│   │   ├── subscription.py     # 訂閱精選
│   │   └── admin.py            # 管理
│   ├── services/               # 商業邏輯
│   │   ├── indicator_service.py    # 技術指標
│   │   ├── signal_service.py       # 訊號偵測
│   │   ├── price_cache_service.py  # 價格快取
│   │   ├── chart_service.py        # 圖表
│   │   └── portfolio_service.py    # 投資組合
│   ├── tasks/                  # 排程任務
│   │   ├── scheduler.py        # 排程器
│   │   └── subscription_tasks.py
│   ├── dependencies.py         # 認證依賴注入 ⭐
│   ├── database.py             # 資料庫連線
│   ├── config.py               # 設定
│   └── main.py                 # 入口
├── static/
│   ├── js/
│   │   ├── core.js             # 核心工具 (DOM快取)
│   │   ├── state.js            # 狀態管理 (AppState)
│   │   ├── search.js           # 搜尋功能
│   │   ├── watchlist.js        # 追蹤清單
│   │   ├── portfolio.js        # 投資組合
│   │   ├── subscription.js     # 訂閱功能
│   │   ├── settings.js         # 設定頁面
│   │   ├── modals.js           # Modal 管理
│   │   └── chart-fix-final.js  # 圖表修復
│   ├── css/
│   │   └── dashboard.css
│   └── dashboard.html          # 主頁面
└── docs/                       # 文件
```

---

## 4. 資料庫設計

### 4.1 共享資料表

#### stock_price_cache（股票價格快取）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵 |
| symbol | VARCHAR(20) | 股票代號 |
| name | VARCHAR(100) | 股票名稱 |
| price | NUMERIC(12,4) | 現價 |
| prev_close | NUMERIC(12,4) | 前收 |
| change | NUMERIC(10,4) | 漲跌 |
| change_pct | NUMERIC(8,4) | 漲跌幅 |
| volume | BIGINT | 成交量 |
| ma20 | NUMERIC(12,4) | 20日均線 |
| updated_at | TIMESTAMP | 更新時間 |

#### market_sentiment（市場情緒指數）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵 |
| date | DATE | 日期 |
| market | VARCHAR(10) | stock / crypto |
| value | INTEGER | 指數值 (0-100) |
| classification | VARCHAR(20) | 文字分類 |

#### index_prices（四大指數）
| 欄位 | 類型 | 說明 |
|------|------|------|
| symbol | VARCHAR(20) | 指數代碼 |
| name | VARCHAR(50) | 指數名稱 |
| price | NUMERIC(12,4) | 現價 |
| change | NUMERIC(10,4) | 漲跌 |
| change_pct | NUMERIC(8,4) | 漲跌幅 |

### 4.2 私有資料表

#### users（用戶資料）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵 |
| line_user_id | VARCHAR(50) | LINE 唯一識別碼 |
| display_name | VARCHAR(100) | LINE 顯示名稱 |
| picture_url | VARCHAR(500) | LINE 頭像 |
| is_admin | BOOLEAN | 是否為管理員 |
| login_count | INTEGER | 登入次數 |

#### watchlists（追蹤清單）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵 |
| user_id | INTEGER | 用戶 ID |
| symbol | VARCHAR(20) | 股票/幣種代號 |
| asset_type | VARCHAR(10) | stock / crypto |
| target_price | NUMERIC(12,4) | 目標價 |
| note | VARCHAR(200) | 備註 |

#### portfolio_transactions（交易紀錄）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵 |
| user_id | INTEGER | 用戶 ID |
| symbol | VARCHAR(20) | 股票代碼 |
| name | VARCHAR(100) | 股票名稱 |
| market | VARCHAR(10) | tw / us |
| transaction_type | VARCHAR(10) | buy / sell |
| quantity | INTEGER | 總股數 |
| price | NUMERIC(12,4) | 成交價 |
| fee | NUMERIC(10,2) | 手續費 |
| tax | NUMERIC(10,2) | 交易稅 |
| transaction_date | DATE | 交易日期 |

#### portfolio_holdings（持股彙總）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵 |
| user_id | INTEGER | 用戶 ID |
| symbol | VARCHAR(20) | 股票代碼 |
| market | VARCHAR(10) | tw / us |
| total_shares | INTEGER | 總持股 |
| avg_cost | NUMERIC(12,4) | 平均成本 |
| realized_profit | NUMERIC(14,2) | 已實現損益 |

#### exchange_rates（匯率）
| 欄位 | 類型 | 說明 |
|------|------|------|
| from_currency | VARCHAR(10) | USD |
| to_currency | VARCHAR(10) | TWD |
| rate | FLOAT | 匯率 |
| updated_at | DATETIME | 更新時間 |

---

## 5. API 設計

### 5.1 主要端點

| 方法 | 端點 | 說明 |
|------|------|------|
| **股票查詢** |
| GET | `/api/stock/{symbol}` | 查詢股票詳情+技術指標 |
| **加密貨幣** |
| GET | `/api/crypto/{symbol}` | 查詢加密貨幣詳情 |
| **追蹤清單** |
| GET | `/api/watchlist` | 取得追蹤清單 |
| GET | `/api/watchlist/with-prices` | 追蹤清單含價格 |
| POST | `/api/watchlist` | 新增追蹤 |
| DELETE | `/api/watchlist/{symbol}` | 移除追蹤 |
| GET | `/api/watchlist/popular` | 熱門追蹤 🆕 |
| **投資組合** |
| GET | `/api/portfolio/summary` | 投資摘要 |
| GET | `/api/portfolio/holdings` | 持股列表 |
| POST | `/api/portfolio/transactions` | 新增交易 |
| **訂閱精選** |
| GET | `/api/subscription/sources` | 訂閱源列表 |
| GET | `/api/subscription/picks` | 我的訂閱精選 |
| POST | `/api/subscription/subscribe/{id}` | 訂閱 |
| **設定** |
| GET | `/api/settings/indicators` | 指標設定 |
| PUT | `/api/settings/indicators` | 更新指標設定 |
| **管理** |
| POST | `/api/admin/update-price-cache` | 更新價格快取 |
| POST | `/api/admin/update-indices` | 更新指數 |
| POST | `/api/admin/fetch-subscriptions` | 抓取訂閱精選 |

### 5.2 回應格式

```json
// 成功
{
  "success": true,
  "data": { ... },
  "market_open": false
}

// 錯誤
{
  "success": false,
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "找不到此股票代號"
  }
}
```

### 5.3 API 新增欄位（v2.0）

```json
// GET /api/stock/{symbol} 新增
{
  "market_open": false,  // 市場是否開盤
  "chart_data": {
    "volumes": [...]     // 🆕 成交量數據
  },
  "indicators": {
    "ma": {
      "dist_ma20": 2.5,        // 🆕 距離 MA20 百分比
      "dist_ma50": 5.1,        // 🆕 距離 MA50 百分比
      "dist_ma200": 15.3,      // 🆕 距離 MA200 百分比
      "golden_cross_20_50": true,   // 🆕 黃金交叉
      "golden_cross_20_50_days": 5  // 🆕 幾天前
    }
  }
}

// GET /api/watchlist/with-prices 新增
{
  "market_status": {
    "tw_open": false,
    "us_open": true,
    "crypto_open": true
  }
}
```

---

## 6. 技術指標

### 6.1 支援的技術指標

| 指標 | 說明 | 判讀 |
|------|------|------|
| MA | 移動平均線 (20/50/200/250) | 多頭/空頭排列、黃金/死亡交叉 |
| RSI | 相對強弱指數 | >70 超買、<30 超賣 |
| MACD | 指數平滑異同移動平均 | 黃金/死亡交叉、柱狀圖背離 |
| KD | 隨機指標 | >80 超買、<20 超賣 |
| 布林通道 | Bollinger Bands | 突破上/下軌 |
| OBV | 能量潮 | 量價背離 |

### 6.2 欄位名稱對照（重要⚠️）

`indicator_service.py` 產生的欄位都是**小寫**：

| 指標 | 欄位名 |
|------|--------|
| MA20 | `ma20` |
| MA50 | `ma50` |
| MA200 | `ma200` |
| RSI | `rsi` |
| MACD | `macd_dif`, `macd_dea`, `macd_hist` |
| KD | `kd_k`, `kd_d` |

**routers 讀取時也必須使用小寫**

### 6.3 綜合評分系統

| 訊號 | 分數 | 說明 |
|------|------|------|
| 價格 > MA20 | +1 | 短期多頭 |
| MA20 > MA50 | +1 | 中期多頭 |
| MA50 > MA200 | +1 | 長期多頭 |
| RSI > 70 | -1 | 超買警示 |
| RSI < 30 | +1 | 超賣機會 |
| MACD > 0 | +1 | 多頭動能 |

---

## 7. 市場情緒分級

| 數值 | 分類 | 意義 |
|------|------|------|
| 0-25 | 極度恐懼 | 可能買點 |
| 26-45 | 恐懼 | 偏謹慎 |
| 46-55 | 中性 | 觀望 |
| 56-75 | 貪婪 | 偏樂觀 |
| 76-100 | 極度貪婪 | 可能賣點 |

---

## 8. 排程任務

| 時間 | 任務 | 說明 |
|------|------|------|
| 每 10 分鐘 | 價格快取更新 | 僅交易時段 |
| 週一~五 13:35 | 台股收盤更新 | 收盤後完整更新 |
| 週二~六 05:05 | 美股收盤更新 | 收盤後完整更新 |
| 每天 09:00/12:00/17:00 | 匯率更新 | USD/TWD |
| 每小時 | 訂閱源抓取 | RSS 文章解析 |

---

## 9. 環境變數

```bash
# 資料庫
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# LINE Login
LINE_LOGIN_CHANNEL_ID=your_channel_id
LINE_LOGIN_CHANNEL_SECRET=your_channel_secret
LINE_LOGIN_CALLBACK_URL=https://your-domain.com/auth/line/callback

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_EXPIRE_DAYS=7

# 應用程式
APP_ENV=production
DEBUG=false
```

---

## 10. 技術選型

| 項目 | 選擇 | 理由 |
|------|------|------|
| 後端框架 | FastAPI | 高效能、自動 API 文件 |
| 資料庫 | PostgreSQL | 穩定、多用戶併發 |
| ORM | SQLAlchemy | 成熟穩定 |
| 任務排程 | APScheduler | 定時更新 |
| 股價抓取 | yfinance | 免費、穩定 |
| 數據處理 | pandas, numpy | 金融分析標配 |
| 部署 | Railway | 簡單、PostgreSQL 整合 |
