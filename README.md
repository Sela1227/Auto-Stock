# 📈 股票技術分析系統

多用戶股票與加密貨幣技術分析平台，提供完整的技術指標分析與自動化通知功能。

## ✨ 功能特色

- **技術指標分析**
  - 移動平均線 (MA20/MA50/MA200 股票; MA7/MA25/MA99 加密貨幣)
  - RSI 相對強弱指標
  - MACD 指數平滑異同移動平均
  - KD 隨機指標
  - 布林通道 (Bollinger Bands)
  - OBV 能量潮指標
  - 成交量分析

- **智能訊號偵測**
  - 均線黃金交叉/死亡交叉
  - 接近突破/跌破預警
  - RSI 超買超賣警示
  - MACD/KD 交叉訊號

- **綜合評分系統**
  - 多指標共振分析
  - 買進/賣出訊號評分
  - 趨勢強度判斷

- **圖表繪製**
  - 價格走勢圖 + 均線 + 布林通道
  - 成交量柱狀圖
  - RSI、MACD、KD 子圖
  - 交叉點標記

- **加密貨幣支援**
  - BTC、ETH 價格追蹤
  - 幣圈專用技術指標
  - 市場情緒指數

- **市場情緒**
  - CNN Fear & Greed Index (美股)
  - Alternative.me (加密貨幣)

## 🚀 快速開始

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 初始化資料庫

```bash
python -m app.cli init
```

### 查詢股票/加密貨幣

```bash
# 互動模式
python -m app.cli

# 查詢股票
python -m app.cli query AAPL

# 查詢加密貨幣
python -m app.cli query BTC

# 強制更新資料
python -m app.cli query TSLA -r

# 查詢市場情緒
python -m app.cli sentiment

# 生成圖表
python -m app.cli chart AAPL -d 90
```

## 📊 使用範例

### CLI 互動模式

```
📈 股票技術分析系統
版本 0.2.0

輸入代號進行查詢 (股票如 AAPL，加密貨幣如 BTC)
輸入 'sentiment' 查看市場情緒，'q' 離開

代號> AAPL
正在分析 AAPL...

╭─────────────────────────────╮
│ AAPL - Apple Inc.          │
╰─────────────────────────────╯

💰 價格資訊
┌──────────┬────────────┐
│ 現價     │    $195.50 │
│ 52週最高 │    $199.62 │
│ 52週最低 │    $164.08 │
└──────────┴────────────┘

代號> BTC
正在分析 BTC (加密貨幣)...

╭─────────────────────────────────────╮
│ BTC - Bitcoin (加密貨幣)            │
╰─────────────────────────────────────╯

代號> sentiment
📊 市場情緒指數
┌────────────┬──────┬──────────┬────────────────────┐
│ 市場       │ 指數 │ 狀態     │ 建議               │
├────────────┼──────┼──────────┼────────────────────┤
│ 美股       │ 55 😐│ 中性     │ 市場中性，觀望為主 │
│ 加密貨幣   │ 32 😟│ 恐懼     │ 留意潛在機會       │
└────────────┴──────┴──────────┴────────────────────┘
```

## 📁 專案結構

```
stock-analysis/
├── app/
│   ├── __init__.py
│   ├── cli.py              # 命令列介面
│   ├── config.py           # 設定檔
│   ├── database.py         # 資料庫連線
│   ├── models/             # 資料模型
│   ├── services/           # 商業邏輯
│   │   ├── indicator_service.py  # 技術指標計算
│   │   ├── stock_service.py      # 股票服務
│   │   ├── crypto_service.py     # 加密貨幣服務
│   │   └── chart_service.py      # 圖表繪製
│   └── data_sources/       # 外部資料來源
│       ├── yahoo_finance.py      # Yahoo Finance
│       ├── coingecko.py          # CoinGecko
│       └── fear_greed.py         # 情緒指數
├── tests/                  # 測試
├── requirements.txt
└── README.md
```

## 🔧 技術棧

- **後端框架**: FastAPI
- **資料庫**: SQLite (開發) / PostgreSQL (生產)
- **ORM**: SQLAlchemy 2.0
- **資料處理**: pandas, numpy
- **股價資料**: yfinance
- **幣價資料**: CoinGecko API
- **圖表繪製**: matplotlib, mplfinance
- **CLI 美化**: Rich

## 📝 開發階段

- [x] 階段一：核心基礎 (股價抓取、快取、基本指標、CLI)
- [x] 階段二：完整指標 (RSI, MACD, KD, 布林, OBV, 圖表)
- [x] 階段三：加密貨幣整合 (BTC, ETH, 情緒指數)
- [x] 階段四：用戶系統 (LINE Login, JWT, 追蹤清單)
- [x] 階段五：個人化設定 (指標/通知/參數設定)
- [ ] 階段六：通知系統 (LINE Messaging 推播)
- [ ] 階段七：Web 介面
- [ ] 階段八：優化與上線

## 🌐 Web API

### 啟動 API 伺服器

```bash
# 開發模式
uvicorn app.main:app --reload

# 或使用
python -m app.main
```

API 文件：http://localhost:8000/docs

### API 端點

| 路徑 | 方法 | 說明 |
|------|------|------|
| `/auth/line` | GET | LINE 登入 |
| `/auth/line/callback` | GET | LINE 登入回調 |
| `/auth/me` | GET | 取得當前用戶 |
| `/api/stock/{symbol}` | GET | 查詢股票 |
| `/api/stock/{symbol}/chart` | GET | 股票圖表 |
| `/api/crypto/{symbol}` | GET | 查詢加密貨幣 |
| `/api/crypto/{symbol}/chart` | GET | 加密貨幣圖表 |
| `/api/market/sentiment` | GET | 市場情緒 |
| `/api/watchlist` | GET/POST | 追蹤清單 |
| `/api/watchlist/{symbol}` | DELETE/PUT | 管理追蹤 |
| `/api/watchlist/overview` | GET | 追蹤清單總覽 |
| `/api/settings/indicators` | GET/PUT | 指標設定 |
| `/api/settings/alerts` | GET/PUT | 通知設定 |
| `/api/settings/params` | GET/PUT | 參數設定 |
| `/api/settings/template/{name}` | POST | 套用模板 |

### 認證方式

```bash
# 在 Header 帶入 JWT Token
Authorization: Bearer {token}
```

## 🔧 LINE Login 設定

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立 LINE Login Channel
3. 設定 Callback URL
4. 在 `.env` 中設定：

```env
LINE_LOGIN_CHANNEL_ID=your_channel_id
LINE_LOGIN_CHANNEL_SECRET=your_channel_secret
LINE_LOGIN_CALLBACK_URL=http://localhost:8000/auth/line/callback
```

## 📄 授權

MIT License

---

> 本專案為技術分析工具，所有分析結果僅供參考，不構成投資建議。
