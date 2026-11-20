<p align="center">
  <img src="static/assets/sela.svg" alt="SELA logo" width="80">
</p>

# AutoStock — 自動選股系統

> 多用戶台股 / 美股 / 加密貨幣追蹤平台：追蹤清單、投資記錄、技術指標、恐懼貪婪指數、LINE Login  
> FastAPI + Vanilla JS + PostgreSQL，部署於 Railway：https://web-production-c219.up.railway.app/

---

## 目前版本：V1.15.0

---

## 版本歷程

### V1.15.0（2026-11-20）Kit 對齊
- 對齊 SELA Starter Kit V4.16.0；版號單一來源 `app/config.py` 的 `VERSION`
- 新增免登入 `/_health`（只回版號）與 `.commander.json`，接上賈維斯巡邏
- 畫面 emoji 換成線條圖示；LINE 推播訊號改單色符號
- 新增 `tests/smoke.py`：語法、啟動 import、前後端 API 契約、版號對帳一次跑完
- 補回 `.gitignore`；修正文件裡寫錯的環境變數名

### V1.14.0（2026-08-26）排程簡化
- 改為週一~週六 06:00（美股收盤後）單一批次更新；移除登入觸發與訂閱源排程

### V1.13.1 – V1.13.3（2026-05）審稿修正
- 交易列表路徑、券商欄位與所有權驗證、XSS 跳脫、production 設定檢查、CORS
- 管理後台踢出 / 全員踢出 / 移除管理員端點；追蹤清單匯入改送 JSON

### V1.13.0（2026-04-12）Kit 對齊
- 整合 SELA 真實 favicon 套組（16/32/180/192/512px + webmanifest）
- CLAUDE.md 改為九章章法格式，坑與 Kit 全域編號交叉對照
- 產出 SELA-handoff.md（首次 Kit 對齊里程碑）

### V1.12.3（2026-04-12）Bug Fix
- 修復情緒指數永遠顯示 50：`data.data?.stock` 改回 `data.stock`

### V1.12.2（2026-04-12）資安 + 修復
- JS 語法修復：`core.js` try/catch；`dashboard.js` 4 處函數缺結尾 `}`
- 資安強化：XSS 防護（`json.dumps`）、debug-log rate limit、state token log 遮蔽
- 重構：Bearer 解析統一 `dependencies/auth.py`；`sync_db_session` context manager
- 情緒指數多來源備用 + DB 12 小時新鮮度自動刷新

### V1.12.1（2026-04-10）Bug Fix
- 修復啟動 crash：`auth.py` NameError（`User` 未定義）

### V1.12（2026-04-10）
- 前端診斷日誌（`/auth/debug-log`、`/auth/debug-logs`）

### V1.11
- 前端 JS 性能優化（DOM 快取、批量更新、命名空間）

### V1.10
- 版本號動態顯示；Cache-only 市場指數載入

### V1.05（2026-04-07）效能優化
- 技術指標預計算排程；清除過期快取

### V1.02（2026-04-07）
- 極簡排程：只在交易時段更新，大幅降低 Railway 費用

### V1.01（2026-04-07）
- 內存快取：非交易時段回 DB，10–40x 性能提升

### V1.00（2026-04-07）
- 完整功能上線：台股 / 美股 / 加密貨幣 / 追蹤清單 / 投資記錄 / 訂閱精選 / 報酬比較

---

## 快取機制

| 快取類型 | 交易時段 | 非交易時段 |
|----------|----------|-----------|
| 股票詳情 | 5 分鐘 | 1 小時 |
| 技術指標 | 10 分鐘 | 24 小時 |
| 情緒指數（內存）| 60 秒 | 60 秒 |
| 情緒指數（DB）| 12 小時自動刷新 | 12 小時自動刷新 |

---

## 排程任務

| 時間（台北）| 任務 |
|------------|------|
| 週一~週六 06:00 | 股價全量 + 情緒指數 + 四大指數 + 匯率 + 指標預計算 |
| 每天 03:00 | 清除過期快取 |

訂閱源與即時更新改由管理後台手動觸發。

---

## 環境變數

| 變數 | 必填 |
|------|------|
| `DATABASE_URL` | 必填 |
| `JWT_SECRET_KEY` | 必填（production 用預設值會拒絕啟動）|
| `LINE_LOGIN_CHANNEL_ID` | 必填 |
| `LINE_LOGIN_CHANNEL_SECRET` | 必填 |
| `LINE_LOGIN_CALLBACK_URL` | 必填 |
| `APP_ENV` | 必填（正式站填 `production`）|
| `ADMIN_LINE_USER_IDS` | 建議 |
| `LINE_MESSAGING_CHANNEL_ACCESS_TOKEN` | 選填（LINE 推播）|

---

## 驗證

```bash
python3 tests/smoke.py
```
