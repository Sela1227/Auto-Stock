# Railway PostgreSQL 設定指南

## 步驟 1：在 Railway 添加 PostgreSQL

1. 進入你的 Railway 專案
2. 點擊 **New** → **Database** → **Add PostgreSQL**
3. 等待資料庫建立完成

## 步驟 2：取得資料庫連線字串

1. 點擊新建立的 PostgreSQL 服務
2. 進入 **Variables** 標籤
3. 複製 `DATABASE_URL` 的值

格式類似：
```
postgres://username:password@host:port/database
```

## 步驟 3：設定環境變數

在你的 **Web Service** (不是 PostgreSQL) 中設定：

1. 點擊 Web Service → **Variables**
2. 添加以下變數：

```bash
# 資料庫 (從 PostgreSQL 服務複製)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# 或直接貼上完整的連線字串
# DATABASE_URL=postgres://username:password@host:port/database

# 應用程式
APP_ENV=production
DEBUG=false

# LINE Login
LINE_LOGIN_CHANNEL_ID=你的_channel_id
LINE_LOGIN_CHANNEL_SECRET=你的_channel_secret
LINE_LOGIN_CALLBACK_URL=https://你的網域/auth/line/callback

# JWT
JWT_SECRET_KEY=你的隨機密鑰
JWT_EXPIRE_DAYS=7
```

### 使用 Railway 的變數引用（推薦）

Railway 支援在同一專案內引用其他服務的變數：

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

這樣當資料庫連線資訊變更時，會自動更新。

## 步驟 4：部署

```bash
# 更新代碼
git add .
git commit -m "feat: add PostgreSQL support"
git push
```

Railway 會自動偵測到變更並重新部署。

## 步驟 5：驗證

1. 等待部署完成
2. 檢查日誌，應該看到：
   ```
   Starting SELA 自動選股系統 v0.3.x
   Database initialized
   ```

3. 訪問你的網站測試功能

## 資料庫表格

系統會自動建立以下表格：

| 表格 | 說明 |
|------|------|
| users | 用戶資料 (LINE Login) |
| watchlists | 追蹤清單 |
| stock_prices | 股價快取 |
| crypto_prices | 幣價快取 |
| market_sentiment | 市場情緒 |
| user_indicator_settings | 用戶指標設定 |
| user_alert_settings | 用戶通知設定 |
| user_indicator_params | 用戶參數設定 |
| notifications | 通知記錄 |

## 注意事項

1. **首次部署**：表格會自動建立，不需要手動執行 migration

2. **postgres:// vs postgresql://**：
   - Railway 使用 `postgres://`
   - SQLAlchemy 需要 `postgresql://`
   - 程式已自動處理轉換

3. **連線池**：
   - 使用 `NullPool` 避免連線問題
   - 適合 Railway 的 serverless 環境

## 故障排除

### 連線失敗
- 確認 DATABASE_URL 正確
- 確認 PostgreSQL 服務正在運行

### 表格不存在
- 檢查日誌確認 "Database initialized" 訊息
- 嘗試重新部署

### SSL 錯誤
如果遇到 SSL 錯誤，在 DATABASE_URL 後面加上：
```
?sslmode=require
```
