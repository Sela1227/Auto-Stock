# AutoStock — SELA 多用戶自動選股分析系統

FastAPI + Vanilla JS + PostgreSQL，部署於 Railway

---

## 目前版本：V1.12.3

---

## 版本歷程

### V1.12.3（2026-04-12）🐛 Bug Fix
- 修復情緒指數顯示錯誤：`data.stock` 被誤改為 `data.data?.stock` 導致永遠顯示 50/Neutral

### V1.12.2（2026-04-12）🔒 資安 + 🐛 修復
- **JS 語法修復**：`core.js` try 缺 catch；`dashboard.js` 4 處函數缺結尾 `}`
- **新增 favicon**；移除 404 的 `target-price-fix.js` 引用
- **資安強化**：XSS 防護（`json.dumps`）、debug-log rate limit、state token log 遮蔽
- **重構**：Bearer 解析統一至 `dependencies/auth.py`；`sync_db_session` context manager；`get_current_user` 去重
- **情緒指數**：DB 12 小時新鮮度自動刷新；多來源備用（feargreedmeter、alternative.me）
- **版本號顯示**：設定頁、admin 頁自動載入診斷日誌修復

### V1.12.1（2026-04-10）🐛 Bug Fix
- 修復啟動 crash：`auth.py` 第 465 行 `NameError: name 'User' is not defined`

### V1.12（2026-04-10）
- 前端診斷日誌（`/auth/debug-log`、`/auth/debug-logs`）
- 管理後台自動顯示診斷區塊

### V1.11
- 前端 JS 性能優化（P0–P4）：DOM 快取、批量更新、命名空間統一

### V1.10
- 版本號動態顯示（`/api/version`）
- Cache-only 市場指數 / 情緒載入策略

### V1.05（2026-04-07）⚡ 效能大優化
- 技術指標預計算排程
- 清除過期快取排程
- 股票詳情快取

### V1.02（2026-04-07）
- 極簡排程：只在交易時段更新，大幅降低 Railway 費用

### V1.01（2026-04-07）
- 內存快取：非交易時段回傳 DB 快取，10–40x 性能提升

### V1.00（2026-04-07）
- 完整功能上線：台股 / 美股 / 加密貨幣 / 追蹤清單 / 投資記錄 / 訂閱精選 / 報酬比較

---

## 快取機制

| 快取類型 | 有效期（交易時段）| 有效期（非交易時段）|
|----------|-------------------|---------------------|
| 股票詳情 | 5 分鐘 | 1 小時 |
| 技術指標 | 10 分鐘 | 24 小時 |
| 情緒指數（內存）| 60 秒 | 60 秒 |
| 情緒指數（DB）| 12 小時自動刷新 | 12 小時自動刷新 |

---

## 排程任務

| 時間（台北）| 任務 |
|------------|------|
| 21:00 | 每日預載（情緒 + 指數 + 匯率 + 指標預計算）|
| 09:00 | 情緒補充 |
| 09:30 | 匯率補充 |
| 08:00, 18:00 | 訂閱源抓取 |

---

## 環境變數

| 變數 | 說明 | 必填 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 連線字串（Railway 自動提供）| ✅ |
| `JWT_SECRET_KEY` | JWT 簽名密鑰 | ✅ |
| `LINE_LOGIN_CHANNEL_ID` | LINE Login Channel ID | ✅ |
| `LINE_LOGIN_CHANNEL_SECRET` | LINE Login Channel Secret | ✅ |
| `LINE_LOGIN_CALLBACK_URL` | `https://你的網域/auth/line/callback` | ✅ |
| `APP_ENV` | `production` / `development` | ✅ |
| `ADMIN_LINE_IDS` | 管理員 LINE User ID（逗號分隔）| 建議 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE 推播 | 選填 |

---

## 部署（Railway）

1. 上傳 ZIP → 解壓 → push 到 GitHub
2. Railway 連接 repo，自動偵測 `Procfile`
3. 設定環境變數
4. PostgreSQL plugin 加入專案
5. 每次更新記得改 `app/config.py` 的 `APP_VERSION`
