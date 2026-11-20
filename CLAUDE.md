> **給同時拿到 SELA-Starter-Kit 的 Claude：**
> 這是已對齊 Kit V4.16.0 的成熟專案，不是新專案。
> 1. 以本專案 CLAUDE.md 為主、Kit 為輔
> 2. 本專案刻意不對齊 Kit 的部分：
>    - 配色維持現有橘色系主色（非 Kit 工具類預設北歐霧藍 #5A7A8B），因 2026-01 起使用者已驗證 10 個月
>    - App logo = 黃底（#FED902）白色壁虎 + 紅綠 K 線 + SELA 字樣（SELA 2026-11-20 提供，生圖 AI 產出 + Claude 底色校正與轉檔）；保留壁虎與 SELA 字樣是 SELA 的決定，不要再「修正」成不含壁虎的版本。SELA 原版 logo（`static/assets/sela.svg`）只用在 README 底部的品牌歸屬
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

- **版本：** V1.15.3
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
| `app/config.py` → `VERSION = 'V1.15.3'` | **唯一要改的地方**；`APP_VERSION`、`/api/version`、`/_health`、畫面四處版號都從這裡來 |
| `CLAUDE.md` 〇「版本」與六章版本歷程 | 手改 |
| `README.md`「目前版本」與版本歷程 | 手改 |
| `app/main.py` `/api/version` 的 features 清單 | 手改（只是說明文字）|
| zip 檔名與資料夾名 | `AutoStock V1.15.3` |

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

### 套件版本（V1.15.3 起全部鎖定）

`requirements.txt` 的直接依賴全用 `==`，數值取自 2026-08-26 V1.14.0 在 Railway 實際安裝並正常運作的組合（Python 3.11）。升級任何套件都要單獨一版，並用 Python 3.11 跑 `tests/smoke.py`、部署後看 Railway 啟動 log。資料庫連線字串在 `database.py` 明確指定 `+psycopg2` 與 `+asyncpg`，不靠 SQLAlchemy 預設驅動。

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
| LINE 推播訊息內容 | `app/tasks/scheduler.py`（名稱表用 `signal_service.SIGNAL_NAMES`）|
| 前端認證 / session | `static/js/core.js` 的 `checkAuth()` + `updateUserUI()` |
| 版本號顯示（前端）| `static/js/core.js` 的 `loadAppVersion()` → 4 個 element；登入頁 `static/index.html` |
| App logo | 母圖 `static/assets/app-logo-1024.png`（其餘尺寸都由它縮）；畫面用 `static/logo.png`（256）；分頁與主畫面圖示在 `static/favicon/`；`theme-color` = 介面主色 `#FA7A35`（四頁 `<meta>` 與 `site.webmanifest` 要一致）|
| 全螢幕圖表 | `static/js/chart-fix-final.js`（DOM 載入時鎖定 open/close/render/setChartRange，其他檔不要再定義同名函式）|
| 網址直開區塊 | `dashboard.html#<區塊名>`（`core.js` 登入後讀 `location.hash`）；舊 `compare.html` 只轉址到 `#cagr` |
| 訊號偵測 | `app/tasks/scheduler.py` 的 `scheduler_service` → `indicator_service`（`signal_service.py` 只剩型別與名稱表）|
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

**#15. 改到沒人用的程式還以為修好了**
- 症狀：V1.15.0 把 `SIGNAL_EMOJI` 換成單色符號、CLAUDE.md 寫「LINE 推播符號在這裡」，V1.15.1 才發現它根本沒人讀
- 原因：LINE 推播實際在 `scheduler.py` 組字；`signal_service.py` 的偵測與格式化函式全是舊版死碼
- 做法：改之前先確認有人呼叫（全專案搜尋名稱）；`vulture app --min-confidence 60` 加上搜尋可找出這類死碼

**#16. 同名全域函式在多支 JS 重複定義，後載入的蓋掉前面，前面的白寫**
- 症狀：`openChartFullscreen` 三份（search.js → chart-fix.js → chart-fix-final.js）、`quickTrade`、`toggleCollapsible`、`adminFetchSubscriptions` 各兩份；改了前面那份畫面沒變
- 原因：歷次修補都是「新檔覆蓋舊函式」，舊版沒刪
- 做法：V1.15.1 只留實際生效的那份；新增修補直接改原檔，不再另開 *-fix.js


**#17. 契約檢查只比路徑形狀，參數段剛好吻合就漏抓**
- 症狀：dashboard 管理區「踢出全部」打 `/api/admin/users/kick-all`（後端是 `/api/admin/kick-all`），smoke 沒抓到
- 原因：`users/kick-all` 剛好符合 `/users/{user_id}` 的形狀
- 做法：V1.15.1 修正路徑；新增管理端點時，前端路徑對照後端定義逐字核對

**#18. 有彩色細節的 AI 生圖 logo，不能用「底色↔白」亮度公式整張校正**
- 症狀：照 sela-logo 的亮度混合公式校正，字下的金色陰影留下斑塊、白色偏米色
- 原因：公式假設圖裡只有底色與白；這張有越往下越深的金色漸層，加上紅綠 K 線
- 做法：用藍色通道當「白的比例」（黃金系 B≈0、白 B=255），只處理 R>200 且 G>150 的黃白系像素，紅綠 K 線自然排除

**#19. 套件沒鎖版本，一改 requirements 就整批升級，線上啟動即崩潰**
- 症狀：V1.15.0–V1.15.2 部署後服務 CRASHED，登入卡住；log 為 `ModuleNotFoundError: No module named 'psycopg'`
- 原因：`sqlalchemy>=2.0.0` 沒上限；V1.15.1 改了 requirements，Railway 重新安裝全部套件，裝到 SQLAlchemy 2.1（`postgresql://` 預設驅動改成 psycopg 第 3 版，本專案只裝 psycopg2）；同時 FastAPI、pandas、yfinance 也一起跳版。V1.15.0 沒改 requirements 也崩，是因為那次一樣觸發重裝
- 做法：`database.py` 明確寫 `postgresql+psycopg2://`；直接依賴全部鎖在 8 月驗證過的版本；smoke 加上「用 PostgreSQL 連線字串匯入一次」（只用 SQLite 測不出這類錯）；推上 GitHub 後要看 Railway 部署狀態是 SUCCESS，不是只看推送成功

---

## 五、煙霧測試（唯一入口）

```bash
pip install -r requirements.txt   # 第一次；沒裝也能跑，只是跳過 import 檢查
python3 tests/smoke.py            # 全綠才能打包；失敗回傳非 0
```

檢查：Python 語法、JS 語法（含 HTML 內嵌 script）、FastAPI 實際 import 與 OpenAPI（SQLite 與 PostgreSQL 連線字串各一次；要跟 Railway 一樣用 Python 3.11）、前後端 API 契約、版號對帳（config = CLAUDE.md = README = 版本歷程）、handoff 落後幾版。

Kit 鐵律另跑：`python3 <sela-deploy>/assets/kit-check.py . --version V1.15.0`

---

## 六、版本歷程（最近 10 版）

| 版本 | 重點 |
|------|------|
| V1.15.3 | 緊急修正：V1.15.0–V1.15.2 線上啟動崩潰（SQLAlchemy 2.1 預設驅動改 psycopg）；同步引擎明確指定 `+psycopg2`；套件全部鎖定 8 月驗證過的版本；smoke 加 PostgreSQL 連線字串匯入檢查 |
| V1.15.2 | 換上 app 專屬 logo：底色校正成 `#FED902`、128 色調色盤壓縮；favicon、手機主畫面圖示、登入頁與側欄都換新；四頁補 `theme-color`；manifest 名稱改為「自動選股系統」|
| V1.15.1 | 瘦身、功能不變：刪 20 個整檔死碼（含 `cli.py`、舊版搜尋模組、一次性腳本）與檔內未用或被覆蓋的函式，Python 少 3,762 行、JS 少 3,236 行（程式碼總計少約 22%），前端 static 748 KB → 510 KB；`compare.html` 改轉址到 dashboard 同功能；logo 換 Kit 正式 256px 檔（74 KB → 7 KB）；移除 `rich`、`pytest` 套件；修「踢出全部」打錯路徑 |
| V1.15.0 | 對齊 Kit V4.16.0：`VERSION` 單一真相 + 免登入 `/_health`；畫面 emoji 換 Font Awesome 線條圖示、LINE 推播改單色符號、log 與文件去 emoji；`tests/smoke.py`（含 API 契約檢查）；`.commander.json` 接賈維斯；補回 `.gitignore`；管理後台與比較頁禁止雙指放大；刪 debug 輸出；修正文件裡寫錯的兩個環境變數名 |
| V1.14.0 | 排程簡化為週一~週六 06:00 單一批次；移除管理員登入觸發更新與訂閱源排程；`force=True` 終於對股票生效 |
| V1.13.3 | 實作 `/kick`、`/kick-all`、`/remove-admin`；修 `set-admin` 缺 query、追蹤清單匯入 FormData → JSON；cagr XSS |
| V1.13.2 | 使用者旅程審查：admin 不存在端點暫時改提示 |
| V1.13.1 | 外部審稿 P0/P1：交易列表路徑、`broker_id` 漏接與所有權驗證、`escapeHTML()`、production fail-fast、CORS、admin cooldown |
| V1.13.0 | 首次 Kit 對齊（Kit V1.8.1）：SELA favicon 套組、CLAUDE.md 九章格式、handoff |
| V1.12.3 | 修復情緒指數顯示：`data.data?.stock` 改回 `data.stock` |

---

## 七、下版候選工作（按優先序）

1. **修「重設參數」按鈕**：設定頁的 `resetParams()` 從 V1.14.0 前就沒有定義，按了沒反應（V1.15.1 掃描發現，不是這版造成）
2. **確認 06:00 批次真的有跑** — Railway deploy log 找「每日批次更新完成」，追蹤清單的價格時間應是當天 06:00
3. **追蹤清單載入性能診斷** — 用戶反映開啟慢，查是 API 慢還是前端渲染
4. **動態 API 測試** — 審稿建議的「登入 → 追蹤 CRUD → 交易 CRUD → 券商 → 持股 → admin 權限」流程測試，補 smoke 只比路徑形狀的不足
5. 背景任務錯誤在管理後台可見（坑 #12）
6. 管理功能有兩套介面：設定頁下方的管理卡片（settings.js）與「管理後台」區塊（admin.js），加上獨立的 `admin.html`（唯一有診斷日誌、設定／移除管理員的地方）——要不要合併成一套
7. Tailwind 改建置版（瀏覽器 console 的 CDN 警告）

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
□ SELA 推 GitHub；Railway 部署狀態要是 SUCCESS（不是 CRASHED），/_health 回新版號、登入、追蹤清單、情緒指數數值正確
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

V1.15.3 修正 V1.15.0 起的線上啟動崩潰並鎖定套件版本；累積 19 條專案坑，下版第一優先是修原本就壞的「重設參數」按鈕。
