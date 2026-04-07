# AutoStock

**SELA 多用戶自動選股分析系統**  
全端 Web App，FastAPI + Vanilla JS + PostgreSQL，部署於 Railway

---

## 使用情境

個人/家庭股票投資追蹤工具，支援台股、美股、加密貨幣，提供技術指標分析、市場情緒、投資組合管理。加到手機主畫面後像 App 一樣使用。

---

## 主要功能

### 追蹤清單
- LINE 帳號登入，每人獨立追蹤清單
- 支援台股（2330.TW）、美股（AAPL）、加密貨幣（BTC/ETH）
- 設定目標價，到價提醒
- 標籤分類（科技股、金融股、觀察中...）
- 熱門追蹤排行榜

### 技術指標
- MA 移動平均線（5/10/20/60/120/240 日）
- RSI 相對強弱指數
- MACD 指數平滑異同移動平均
- KD 隨機指標
- 布林通道
- OBV 能量潮
- 綜合評分（多指標加權）

### 智能訊號
- 黃金交叉 / 死亡交叉
- 超買 / 超賣警示
- 突破預警（布林通道上下軌）
- MA 支撐 / 壓力

### 市場情緒
- 美股 Fear & Greed Index（CNN）
- 加密貨幣恐慌貪婪指數（Alternative.me）
- 歷史走勢圖
- 存入資料庫快取，回應毫秒級

### 投資組合
- 交易紀錄（買入/賣出）
- 自動計算持股成本、損益
- 支援多券商、不同手續費率
- 年化報酬率（CAGR）計算
- 多標的報酬率比較

### 訂閱精選
- 自動追蹤財經專家部落格（RSS）
- 解析文章抓取推薦股票
- 30 天滾動顯示

### 其他
- 三大指數即時行情（道瓊、S&P 500、NASDAQ）
- 匯率換算（USD/TWD）
- 響應式設計，手機體驗佳
- 支援加到主畫面（PWA）

---

## 技術規格

| 層次 | 技術 |
|------|------|
| 前端 | Vanilla JavaScript + Tailwind CSS + Chart.js |
| 後端 | Python 3.11 + FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| 資料庫 | PostgreSQL（Railway 內建）|
| 排程 | APScheduler |
| 股票數據 | Yahoo Finance（yfinance）|
| 加密貨幣 | CoinGecko API |
| 情緒指數 | CNN Fear & Greed + Alternative.me |
| 登入 | LINE Login + JWT |
| 部署 | Railway |

所有外部 API 均為免費，個人使用完全免費。

---

## 環境變數（.env）

| 變數 | 說明 | 必填 |
|------|------|------|
| DATABASE_URL | PostgreSQL 連線字串（Railway 自動提供）| 是 |
| JWT_SECRET_KEY | 任意長隨機字串 | 是 |
| LINE_LOGIN_CHANNEL_ID | LINE Login Channel ID | 是 |
| LINE_LOGIN_CHANNEL_SECRET | LINE Login Channel Secret | 是 |
| LINE_LOGIN_CALLBACK_URL | `https://你的網域/auth/line/callback` | 是 |
| APP_ENV | `production` | 是 |
| LINE_CHANNEL_ACCESS_TOKEN | LINE 推播（選填）| 否 |

---

## 本地開發

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入必填變數

# 啟動開發伺服器
uvicorn app.main:app --reload --port 8000
```

瀏覽器開啟 http://localhost:8000

---

## Railway 部署

```
1. Railway 建立專案，加入 PostgreSQL（自動給 DATABASE_URL）
2. 連結 GitHub repo
3. 填寫環境變數（LINE Login 相關）
4. 自動 build + deploy
5. 在 LINE Developers Console 加入 Callback URL
```

詳細步驟請見部署指南文件。

---

## 版本歷程

### V1.0.0（2026-04-07）
- 初始優化版正式發布
- 排程優化：減少 60% 執行次數，只在交易時段更新價格
- 情緒指數 DB 快取：回應從秒級降至毫秒級
- 資料庫索引優化：追蹤清單、交易紀錄查詢加速
- 智能交易時段判斷：台股 09:00-13:30、美股 21:30-05:00
- 成本監控 API：`/api/admin/cost-metrics`
- 完整技術指標：MA/RSI/MACD/KD/BB/OBV
- 投資組合管理：交易紀錄、持股、損益計算
- 訂閱精選：RSS 自動抓取專家推薦
- LINE Login 登入
- Railway 一鍵部署

---

## 開發規範

- 版本命名：新功能 +0.1、Bug fix +0.01、大改版 +1.0
- 每次發布必須更新 `app/config.py` 的 `APP_VERSION`
- 同步更新 README.md 版本歷程 及 CLAUDE.md 版本欄位
- 技術指標欄位名一律小寫（ma20, rsi, macd_dif...）
- 前端情緒 API 使用 `/market/sentiment`（有 DB 快取）

---

## 相關文件

- `CLAUDE.md` — 開發交接文件（給 Claude）
- `SELA_系統規格書.md` — 完整系統架構
- `SELA_部署指南.md` — Railway 部署步驟
- `SELA_開發指南.md` — 開發環境設定
