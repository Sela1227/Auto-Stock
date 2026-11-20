# SELA-handoff.md ｜ AutoStock V1.15.0

> 上一份 handoff 是 V1.13.0（對齊 Kit V1.8.1），當時提的 N1 市場感知快取、N2 FastAPI 啟動 NameError、#3 補強不重搬。

## 〇、專案速覽

- **專案名稱：** AutoStock（自動選股系統）
- **專案類型：** FastAPI + Railway（多用戶 Web App，Vanilla JS + Tailwind CDN）
- **技術棧：** Python 3.11 + FastAPI + SQLAlchemy 2.0 Async/Sync + PostgreSQL + APScheduler + LINE Login
- **部署路徑：** SELA 推 GitHub → Railway 自動部署
- **使用 Kit 版本：** V4.16.0（從 V1.8.1 跳版補對齊）
- **完成版本：** V1.15.0
- **完成日期：** 2026-11-20

## 二、本次新增（建議進 Kit）

**[坑] 打包排除規則 `--exclude "*.git*"` 連 `.gitignore` 一起排掉**
- 症狀：連續 4 版 zip 沒有 `.gitignore`，kit-check P1 才擋下
- 原因：本意排 `.git/`，萬用字元也吃掉 `.gitignore`、`.github/`、`.gitattributes`
- 做法：排除寫精確路徑 `-x "*/.git/*"`；打包後 `unzip -l` 確認 `.gitignore` 在。建議 Kit 給一行標準打包指令讓專案照抄
- 影響範圍：所有用 `zip -r` 打包的專案
- 證據：本專案 CLAUDE.md 坑 #13（V1.13.1–V1.14.0）
- 查重：grep「exclude」「\*.git\*」→ 無

**[坑] 背景任務呼叫不存在的方法名，被 except 吞掉好幾版**
- 症狀：管理員登入觸發的股價更新從沒成功過，畫面無任何異狀，log 只有一行 error
- 原因：呼叫 `update_all_prices()`，實際方法叫 `update_all`；`BackgroundTasks` 裡的 `AttributeError` 被 try/except 接住
- 做法：煙霧測試實際呼叫一次背景任務進入點；失敗要在管理介面可見，不能只寫 log
- 影響範圍：所有有排程 / BackgroundTasks 的後端
- 證據：本專案坑 #12（V1.14.0 才發現）
- 查重：grep「AttributeError」→ #28、#34 都是 framework 版本問題，不同；grep「吞」→ 無

**[Kit 修改建議] OPT-7 補強：批次去 emoji 的兩個死角**
- 現狀：OPT-7 講「介面 emoji → ICO()」，沒講既有大專案怎麼批次清
- 建議補：①先掃「整個字串就是 emoji」的值（`'🥇'`、`SIGNAL_EMOJI = {…: "📈"}`、`? '🔺' : '🔻'`），逐一換圖示或單色符號，**再**批次刪其餘——否則清成 `''`，語法照過、畫面與推播少了方向提示；②Markdown 表格的 ✅ ❌ 狀態欄要轉 ✓ ✗，不能刪（刪了整欄空白）；③`textContent` 渲染的訊息只能刪、不能塞 `<i>`
- 理由：本案 749 處；純 emoji 字串 9 處 JS、17 個 LINE 推播符號、README 必填欄被清空，複查才補回

**[Kit 修改建議] 坑 #3 補強：請求端的契約漂移，加一個靜態比對當早期信號**
- 現狀：#3 講回應結構一致；本案連踩的是**請求端**：路徑參數 vs query（`/transactions/tw` 被當 `transaction_id` → 422）、FormData vs JSON body、必填 `Query(...)` 沒傳、呼叫已刪除的端點
- 建議：煙霧測試加「前端每個 `apiRequest/fetch('/api/…')` 都對得到後端路由」的靜態比對（解析 `APIRouter(prefix=)` + `@router.<method>("…")`，`{param}` 與 `${…}` 各當一段）。本案實作在 `tests/smoke.py` 的 `check_contract()`，約 40 行，對舊版實測抓到殘留的 `/remove-admin` 呼叫
- 取捨：只比路徑形狀，抓不到型別與 body 格式
- 理由：V1.13.1 外部審稿逐條人工比對才抓到 4 個 422/404

**[Kit 修改建議] sela-deploy railway.md：沙盒連不到站時，線上版號改用 Railway 部署紀錄**
- 現狀：鐵律「讀不到線上版號就停」；本對話的出站代理擋 `*.up.railway.app`，curl 與 WebFetch 都讀不到
- 建議：Railway 專案可用連接器 `list-deployments`，每筆有 commit 訊息（SELA 的 commit 訊息就是版號），當作線上版號來源並在回報寫明來源
- 理由：本案靠這條確認線上 V1.14.0 才放行

**[Kit 修改建議] jarvis-interface.md：補「Railway + SELA 自己推 GitHub」的 `.commander.json` 範例**
- 現狀：範例都是 Cloudflare 腳本部署（有 `prod.cmd`、`-test`）
- 建議：加一個只有 `monitor.url`（指向 `/_health`）、`smoke`、`prod.url`、`prod.version_url`，**不寫 `prod.cmd`** 的範例，並寫明「部署走 git 推送的專案，賈維斯只巡邏、同步、封存」
- 理由：照範本寫 `prod.cmd` 等於在 git 上加自動化，違反鐵律

### 可加但等更多證據

- zip 沒標 UTF-8 旗標時，中文檔名解壓變 `SELA_#U4ea4#U6613…`，之後每版照抄（本案 13 個 docs 檔名亂碼好幾個月）；用 Python `zipfile` 打包會自動標旗標。跟坑 #20（下載中文檔名）不同，N=1
- 文件寫的環境變數名跟程式讀的不一致（2 個），照文件設會靜默無效；可考慮 smoke 比對 `.env.example` 與 `Settings` 欄位

## 五、留在這個專案、不要回流 Kit 的東西

- 週一~週六 06:00 單一批次的時間點選擇（美股收盤後、週六補抓週五）——業務決策
- LINE 推播訊號符號對照（▲ ▼ → ⚠ ※ 對各技術訊號）
- 前後端 API 契約表的具體端點（交易列表、追蹤清單匯入、set-admin）
- 情緒指數多來源與 12 小時新鮮度
- `validate_production()` 檢查的具體變數清單（做法可參考，清單是本專案的）
- 管理員 kick / kick-all 寫 `SystemConfig` token 版本號的實作
- 配色、品牌（SELA logo、不做 app logo）

## 六、Kit 維護 Claude 的行動清單

- **建議升 Kit 版本：** b+1，理由：2 條新坑 + 4 條修改建議（OPT-7、#3、railway.md、jarvis-interface.md）
- **必做：**
  - [ ] 新增坑「`--exclude "*.git*"` 排掉 `.gitignore`」，並在 sela-deploy 給標準打包指令
  - [ ] 新增坑「背景任務的 AttributeError 被吞」
  - [ ] OPT-7 補批次去 emoji 的三個死角
  - [ ] 坑 #3 補請求端契約漂移與靜態比對
- **暫緩：**
  - [ ] railway.md 用部署紀錄讀線上版號——等第二個 Railway 專案也遇到代理擋站
  - [ ] zip UTF-8 旗標、環境變數名不一致——各 N=1
- **不做：**
  - [ ] 06:00 批次、LINE 推播符號表（業務）
