> **給同時拿到 SELA-Starter-Kit 的 Claude：**
> 這是已對齊 Kit V4.16.0 的成熟專案，不是新專案。
> 1. 以本專案 CLAUDE.md 為主、Kit 為輔
> 2. 本專案刻意不對齊 Kit 的部分：
>    - 配色維持現有橘色系主色（非 Kit 工具類預設北歐霧藍 #5A7A8B），因 2026-01 起使用者已驗證 10 個月
>    - 不做業務 app 專屬 logo，保留 SELA logo 為主視覺（SELA 2026-11-20 決定，之後想做隨時可做）
>    - 部署走 SELA 自己推 GitHub → Railway 自動部署；Claude 不 push、不設 hook，`.commander.json` 因此不寫 `prod.cmd`、沒有 `-test` 試用站
>    - `docs/` 是 V0.x–V1.0 時期的歷史文件，只去 emoji、不改寫內容；現況以本檔為準
>    - 英文程式名 = AutoStock、中文俗稱 = 自動選股系統（UI 顯示名維持中文）
> 3. 不要為對齊 Kit 而動既有設計——已驗證的就是事實標準
> 4. 版號規則照 Kit（V<a>.<b>.<c>，部署版無後綴）
> 5. 下次完成版本時評估 SELA-handoff.md（Kit 鐵律 #0）

# CLAUDE.md — AutoStock（自動選股系統）

> **這份是給下次 Claude 看的工作上下文，不是文件。**
> 判斷標準只有一個：下次 Claude 讀完，能不能直接動手？
> 每升一版至少更新三處：踩過的坑、版本歷程、下版候選工作。

---

## 〇、當前狀態

- **版本：** V1.15.0
- **正式網址：** https://web-production-c219.up.railway.app/
- **已對齊 Kit：** V4.16.0
- **狀態：** 上線中（Railway 專案「自動選股系統」、服務 Stock、region europe-west4）
- **一句話定位：** 台股 / 美股 / 加密貨幣的追蹤用 Web App（不是即時分析），多用戶、追蹤清單、投資記錄、LINE Login
- **技術棧：** Python 3.11 + FastAPI + SQLAlchemy 2.0（Async/Sync 混用）+ PostgreSQL + Vanilla JS + Tailwind CSS（CDN）+ APScheduler + LINE Login + JWT + Railway
- **入口點：** `app/main.py` → `app = FastAPI(...)`；排程在 `lifespan()` 內註冊
- **資料更新：** 週一~週六 06:00（台北）單一批次（美股收盤後）；其餘時間不打外部 API，管理後台有手動按鈕
- **線上版號：** `/_health`（免登入，只回 `{"ok":true,"version":"V…"}`，賈維斯巡邏讀這支）

---

## 一、技術棧決策（為什麼這樣選）

| 選擇 | 替代品 | 選這個的理由 |
|------|--------|------------|
| FastAPI | Django / Flask | async 原生支援、Pydantic 驗證、自動 OpenAPI |
| SQLAlchemy 2.0 Async | Tortoise ORM | 成熟穩定、支援 async + sync 混用（排程需要同步）|
| Vanilla JS + Tailwind | React / Vue | 不需要 build step，直接部署，Railway 成本低 |
| LINE Login | Google OAuth | 目標用戶（台灣）LINE 普及率高 |
| Railway + PostgreSQL | Heroku / Render | PostgreSQL plugin 內建、部署快 |
| APScheduler | Celery / RQ | 不需要額外 Redis，Railway 單服務即可跑排程 |
| 每日單一批次 | 盤中每 30 分更新 | 定位是追蹤不是即時；06:00 抓得到美股最新收盤（V1.14.0 SELA 定案）|

> SQLAlchemy 混用 Async（router）與 Sync（排程）是刻意設計，不是技術債。

---

## 二、業務對映表

> 同一業務概念散在多處，改一處必須同步以下所有點。

### 版本號（V1.15.0 起單一真相）

| 位置 | 說明 |
|------|------|
| `app/config.py` → `VERSION = 'V1.15.0'` | **唯一要改的地方**；`APP_VERSION`、`/api/version`、`/_health`、畫面四處版號都從這裡來 |
| `CLAUDE.md` 〇「版本」與六章版本歷程 | 手改 |
| `README.md`「目前版本」與版本歷程 | 手改 |
| `app/main.py` `/api/version` 的 features 清單 | 手改（只是說明文字）|
| zip 檔名與資料夾名 | `AutoStock V1.15.0` |

前端顯示直接用 API 回的字串（已含 `V`），**不要再自己加 `v` 前綴**——`tests/smoke.py` 會擋。

### 情緒指數資料路徑（V1.12.3 血淚教訓）

| 層次 | 欄位 | 說明 |
|------|------|------|
| `routers/market.py` 回傳 | `{success, stock, crypto}` | **頂層欄位，不是 `data.xxx`** |
| `services/market_service.py` | `result["stock"]`, `result["crypto"]` | dict key |
| `static/js/dashboard.js` | `data.stock`, `data.crypto` | **絕對不是 `data.data?.stock`** |

### 前後端 API 契約（V1.13.1–V1.13.3 連踩四次）

| 端點 | 前端必須這樣送 | 不要 |
|------|---------------|------|
| 交易列表 | `GET /api/portfolio/transactions?market=tw` | `/transactions/tw`（會被當 `transaction_id` → 422）|
| 追蹤清單匯入 | JSON `{items: [...]}` | `FormData`（後端收 `WatchlistImportRequest`）|
| 設為管理員 | `POST .../set-admin?is_admin=true` | 漏 query（後端 `Query(...)` 必填 → 422）|

新增或改 API 後跑 `python3 tests/smoke.py`，它會比對前端每個 `/api`、`/auth` 呼叫後端都有路由（只比路徑形狀，參數型別與 body 格式仍要自己核對）。

### 認證依賴（統一出口）

```python
# 一律從這裡 import，不要各 router 自己實作
from app.dependencies import get_current_user, get_admin_user, get_optional_user
```

### 技術指標欄位名（全小寫）

`ma5`, `ma10`, `ma20`, `ma60`, `ma120`, `ma240`, `rsi`, `macd_dif`, `macd_dea`, `macd_hist`, `kd_k`, `kd_d`, `bb_upper`, `bb_middle`, `bb_lower`, `obv`

### 環境變數名（文件曾寫錯兩個，以程式為準）

| 程式讀的名字 | 曾誤寫成 |
|---|---|
| `ADMIN_LINE_USER_IDS` | `ADMIN_LINE_IDS` |
| `LINE_MESSAGING_CHANNEL_ACCESS_TOKEN` | `LINE_CHANNEL_ACCESS_TOKEN` |

---

## 三、關鍵檔案路徑

| 想改什麼 | 動哪些檔 |
|---------|---------|
| 版本號 | `app/config.py` 的 `VERSION`，再同步 CLAUDE.md / README |
| 認證邏輯 | `app/dependencies/auth.py`（唯一出口）|
| 排程任務 | `app/main.py` 的 `lifespan()`（`scheduler.add_job`）＋ `daily_preload()` |
| 股價批次更新 | `app/services/price_cache_service.py` 的 `update_all(force=True)` |
| DB session（排程用）| `app/main.py` 的 `sync_db_session()` context manager |
| 情緒指數資料 | `app/data_sources/fear_greed.py` + `app/services/market_service.py` |
| LINE 推播訊號符號 | `app/services/signal_service.py` 的 `SIGNAL_EMOJI`（單色符號 ▲ ▼ → ⚠ ※）|
| 前端認證 / session | `static/js/core.js` 的 `checkAuth()` + `updateUserUI()` |
| 版本號顯示（前端）| `static/js/core.js` 的 `loadAppVersion()` → 4 個 element；登入頁 `static/index.html` |
| XSS 跳脫 | `static/js/utils.js` 的 `escapeHTML()`；外部資料插 innerHTML 一律經過它 |
| Production 設定檢查 | `app/config.py` 的 `validate_production()`（漏設就拒絕啟動）|
| LINE Login callback | `app/routers/auth.py` 的 `/auth/line/callback` |
| 管理後台 | `static/admin.html` + `app/routers/admin.py` |
| 驗證入口 | `tests/smoke.py`（賈維斯與審查員都跑這支）|
| 賈維斯接口 | `.commander.json`（SELA 管的檔）|

---

## 四、踩過的坑（編號累積，永不重排）

> 對應 Kit 全域坑編號標 `[Kit #N]`（V1.15.0 對照 Kit V4.16.0 重驗過）。

**#1. 情緒指數永遠顯示 50/Neutral（資料路徑誤改）** `[Kit #3]`
- 症狀：兩個情緒指數都固定顯示 50，Neutral，DB 明明有正確資料
- 原因：重構括號修復時把 `data.stock` 誤改成 `data.data?.stock`；`/api/market/sentiment` 回傳頂層欄位
- 做法：改 API 解析前先用 DevTools Network tab 看實際回傳結構

**#2. JS 多個函數缺結尾 `}`，整個模組無法載入** `[Kit #7]`（原標 #23，已併入 #7）
- 症狀：`window.apiRequest`, `window.$` 全是 undefined；SyntaxError
- 原因：手動修 JS 留注釋殘留破壞縮排對齊；`dashboard.js` 共 4 個函數缺結尾
- 做法：`tests/smoke.py` 對全部 JS 與 HTML 內嵌 script 跑 `node --check`

**#3. `auth.py NameError: User is not defined`（啟動即 crash）** `[Kit #7]`（本專案是該條證據）
- 症狀：Railway 部署後整個服務無法啟動，所有 API 回 502
- 原因：`debug-logs` endpoint 用了 `User` 型別，但沒 import
- 做法：`tests/smoke.py` 實際 `from app.main import app` 並產 OpenAPI

**#4. Bearer token 解析在 3 個地方各自重複** `[Kit #5]`
- 症狀：修認證邏輯時要改 3 個地方，漏改一個就行為不一致
- 原因：早期各 router 各自實作 `get_current_user`
- 做法：V1.12.2 起統一到 `app/dependencies/auth.py`

**#5. 排程 DB session 6 個函數各自開關，有一個漏了 `finally`** `[Kit #24]`
- 症狀：服務跑一陣子後 connection pool 漸耗盡
- 原因：複製貼上的樣板程式
- 做法：V1.12.2 起用 `sync_db_session()` context manager 統一管理

**#6. XSS via LINE 用戶名稱字串插值** `[Kit #18]`
- 症狀：用戶名稱含 `"` 或 `</script>` 可執行任意 JS
- 原因：`html_content = f"""... "{user.display_name}" ..."""` 直接插入
- 做法：`json.dumps()` 整包序列化 + display 用 HTML escape；前端外部資料用 `escapeHTML()` + `data-*` 取代 `onclick` 字串插值（V1.13.1）

**#7. CNN Fear & Greed API 單一來源，Railway IP 被封就全壞** `[Kit #15]`
- 症狀：美股情緒指數永遠顯示 fallback 值 50
- 原因：`_get_fear_greed_alternative()` 直接 `return None`
- 做法：V1.12.2 加 feargreedmeter.com + alternative.me 兩個備用來源

**#8. DB 情緒資料無新鮮度檢查，讀到過期舊值**
- 症狀：前端仍顯示舊資料，必須手動觸發排程才更新
- 原因：`get_latest_sentiment()` 不管資料是幾天前的都直接回傳
- 做法：V1.12.2 加 12 小時新鮮度檢查，過期自動呼叫外部 API

**#9. State token 完整印到 Railway log**
- 症狀：log 中可見完整 state token
- 原因：`logger.info(f"Created state: {state}")`
- 做法：只印 `{state[:8]}...{state[-4:]}`

**#10. 前後端 API 契約漂移（路徑 vs query、FormData vs JSON、必填參數沒傳、呼叫不存在的端點）** `[Kit #3 補強]`
- 症狀：交易列表 422、追蹤清單匯入 422、設為管理員 422、踢出用戶 404——前端畫面看起來正常，按下去才壞
- 原因：前後端各自改，沒有任何東西比對兩邊（V1.13.1 外部審稿逐條人工比對才抓到）
- 做法：`tests/smoke.py` 的 API 契約檢查（路徑形狀）；body 格式與必填 query 看二章「前後端 API 契約」表

**#11. 參數或欄位加了、內部沒接上，功能靜默不生效** `[Kit #41]`
- 症狀：改交易的券商存不進去；管理後台「更新價格快取」在收盤時按了沒反應
- 原因：`update_transaction` 的 `allowed_fields` 漏 `broker_id`；`update_all(force=True)` 只把 `force` 傳給加密貨幣，股票仍被開盤判斷跳過
- 做法：新參數從入口一路追到最底層用上；端到端按一次確認有變化

**#12. 背景工作呼叫不存在的方法名，被 try/except 吞掉好幾版**
- 症狀：管理員登入後的股價更新從沒成功過，畫面與 log 都看不出來（只有一行 error）
- 原因：`auth.py` 呼叫 `update_all_prices()`，實際方法叫 `update_all`；`AttributeError` 被背景任務的 except 吞掉
- 做法：V1.14.0 移除登入觸發、加別名；背景任務出錯要在管理後台看得到，不能只寫 log

**#13. 打包排除規則 `--exclude "*.git*"` 把 `.gitignore` 一起排掉**
- 症狀：V1.13.1–V1.14.0 的 zip 都沒有 `.gitignore`，kit-check P1 擋下
- 原因：本意只排 `.git/`，萬用字元連 `.gitignore`、`.github/` 都吃掉
- 做法：排除寫精確路徑 `-x ".git/*"`；打包後 `unzip -l` 確認 `.gitignore` 在

**#14. 批次刪 emoji 時，「整個字串就是 emoji」的地方會變空字串**
- 症狀：排名獎牌、漲跌箭頭、LINE 推播訊號符號清完變空白，畫面與推播少了方向提示
- 原因：`'🥇'`、`SIGNAL_EMOJI` 這類值本身就是 emoji，正則一刪就成 `''`，語法照樣過
- 做法：先掃「純 emoji 字串」逐一換成 Font Awesome 圖示或單色符號，再批次刪其餘（V1.15.0 已全數處理）

---

## 五、煙霧測試（唯一入口）

```bash
pip install -r requirements.txt   # 第一次；沒裝也能跑，只是跳過 import 檢查
python3 tests/smoke.py            # 全綠才能打包；失敗回傳非 0
```

檢查：Python 語法、JS 語法（含 HTML 內嵌 script）、FastAPI 實際 import 與 OpenAPI、前後端 API 契約、版號對帳（config = CLAUDE.md = README = 版本歷程）、handoff 落後幾版。

Kit 鐵律另跑：`python3 <sela-deploy>/assets/kit-check.py . --version V1.15.0`

---

## 六、版本歷程（最近 10 版）

| 版本 | 重點 |
|------|------|
| V1.15.0 | 對齊 Kit V4.16.0：`VERSION` 單一真相 + 免登入 `/_health`；畫面 emoji 換 Font Awesome 線條圖示、LINE 推播改單色符號、log 與文件去 emoji；`tests/smoke.py`（含 API 契約檢查）；`.commander.json` 接賈維斯；補回 `.gitignore`；管理後台與比較頁禁止雙指放大；刪 debug 輸出；修正文件裡寫錯的兩個環境變數名 |
| V1.14.0 | 排程簡化為週一~週六 06:00 單一批次；移除管理員登入觸發更新與訂閱源排程；`force=True` 終於對股票生效 |
| V1.13.3 | 實作 `/kick`、`/kick-all`、`/remove-admin`；修 `set-admin` 缺 query、追蹤清單匯入 FormData → JSON；cagr XSS |
| V1.13.2 | 使用者旅程審查：admin 不存在端點暫時改提示 |
| V1.13.1 | 外部審稿 P0/P1：交易列表路徑、`broker_id` 漏接與所有權驗證、`escapeHTML()`、production fail-fast、CORS、admin cooldown |
| V1.13.0 | 首次 Kit 對齊（Kit V1.8.1）：SELA favicon 套組、CLAUDE.md 九章格式、handoff |
| V1.12.3 | 修復情緒指數顯示：`data.data?.stock` 改回 `data.stock` |
| V1.12.2 | JS 語法修復；資安強化；重構（Bearer 解析、sync_db_session）；情緒指數多來源 |
| V1.12.1 | 修復啟動 crash（`NameError: User`）|
| V1.12 | 前端診斷日誌（`/auth/debug-log`）；管理後台診斷區塊 |

---

## 七、下版候選工作（按優先序）

1. **確認 06:00 批次真的有跑** — Railway deploy log 找「每日批次更新完成」，追蹤清單的價格時間應是當天 06:00
2. **追蹤清單載入性能診斷** — 用戶反映開啟慢，查是 API 慢還是前端渲染
3. **動態 API 測試** — 審稿建議的「登入 → 追蹤 CRUD → 交易 CRUD → 券商 → 持股 → admin 權限」流程測試，補 smoke 只比路徑形狀的不足
4. 背景任務錯誤在管理後台可見（坑 #12）
5. Tailwind 改建置版（瀏覽器 console 的 CDN 警告）
6. `compare.html` 走勢比較頁的 LINE Login 狀態同步

---

## 八、升版必讀

### 部署流程（SELA 推 GitHub → Railway 自動部署）

```
□ 改 app/config.py 的 VERSION，同步 CLAUDE.md〇與六章、README
□ python3 tests/smoke.py 全綠
□ kit-check.py 全綠
□ 打包：zip -r "AutoStock V<x.y.z>.zip" "AutoStock V<x.y.z>" -x "*/.git/*" "*/__pycache__/*" "*/venv/*" "*.pyc" "*/.env" "*.log" "*/.DS_Store"
□ unzip -l 確認 .gitignore、.commander.json、tests/smoke.py 都在（坑 #13）
□ 部署前用 Railway 部署紀錄或 /_health 比線上版號，絕不拿舊的蓋新的
□ SELA 推 GitHub；部署後 /_health 回新版號、登入、追蹤清單、情緒指數數值正確
```

### 環境變數（新環境必設）

| 變數 | 說明 |
|------|------|
| `DATABASE_URL` | PostgreSQL（Railway 自動提供）|
| `JWT_SECRET_KEY` | 隨機長字串（production 用預設值會拒絕啟動）|
| `LINE_LOGIN_CHANNEL_ID` | LINE Login Channel ID |
| `LINE_LOGIN_CHANNEL_SECRET` | LINE Login Channel Secret |
| `LINE_LOGIN_CALLBACK_URL` | `https://web-production-c219.up.railway.app/auth/line/callback` |
| `APP_ENV` | `production` |
| `ADMIN_LINE_USER_IDS` | 管理員 LINE User ID（逗號分隔）|
| `LINE_MESSAGING_CHANNEL_ACCESS_TOKEN` | LINE 推播（選填）|

> LINE Developers Console 必須把 Callback URL 加入（每個環境各一條）。

### Railway 用量（2026-11-20 實測 7 天）

服務 Stock 平均記憶體 0.18 GB、CPU 近 0；Postgres-bnNp 0.04 GB；另一個名為「Postgres」的服務全為 0（已停用）。

---

## 九、一句話總結

V1.15.0 對齊 Kit V4.16.0：版號單一真相、免登入 `/_health`、畫面改線條圖示、`tests/smoke.py` 一個入口含 API 契約檢查並接上賈維斯；累積 14 條專案坑，下版第一優先是確認 06:00 批次真的有跑。
