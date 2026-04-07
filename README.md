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

### 市場情緒
- 美股 Fear & Greed Index（CNN）
- 加密貨幣恐慌貪婪指數（Alternative.me）
- 存入資料庫快取，回應毫秒級

### 投資組合
- 交易紀錄（買入/賣出）
- 自動計算持股成本、損益
- 支援多券商、不同手續費率

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
| 登入 | LINE Login + JWT |
| 部署 | Railway |

---

## 本地開發

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

---

## 版本歷程

### V1.0.0（2026-04-07）
- 初始優化版正式發布
- 排程優化：減少 60% 執行次數，只在交易時段更新價格
- 情緒指數 DB 快取：回應從秒級降至毫秒級
- 資料庫索引優化
- 智能交易時段判斷：台股 09:00-13:30、美股 21:30-05:00

---

## 開發規範

- 版本命名：新功能 +0.1、Bug fix +0.01、大改版 +1.0
- 每次發布必須更新 `app/config.py` 的 `APP_VERSION`
- 技術指標欄位名一律小寫（ma20, rsi, macd_dif...）
- 前端情緒 API 使用 `/market/sentiment`（有 DB 快取）
