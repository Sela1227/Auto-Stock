# CLAUDE.md — AutoStock（SELA 自動選股系統）

> **這份是給下次 Claude 看的工作上下文，不是文件。**
> 判斷標準只有一個：下次 Claude 讀完，能不能直接動手？
> 每升一版至少更新三處：踩過的坑、版本歷程、下版候選工作。

---

## 〇、當前狀態

- **版本：** V1.13.0
- **狀態：** 上線中（Railway，多用戶）
- **一句話定位：** 台股 / 美股 / 加密貨幣技術分析 Web App，支援多用戶、追蹤清單、投資記錄、訂閱精選、LINE Login
- **技術棧：** Python 3.11 + FastAPI + SQLAlchemy 2.0（Async/Sync 混用）+ PostgreSQL + Vanilla JS + Tailwind CSS + APScheduler + LINE Login + JWT + Railway
- **入口點：** `app/main.py` → `app = FastAPI(...)` + APScheduler 排程

---

## 一、技術棧決策（為什麼這樣選）

| 選擇 | 替代品 | 選這個的理由 |
|------|--------|------------|
| FastAPI | Django / Flask | async 原生支援、Pydantic 驗證、自動 OpenAPI |
| SQLAlchemy 2.0 Async | Tortoise ORM | 成熟穩定、支援 async + sync 混用（排程需要同步）|
| Vanilla JS + Tailwind | React / Vue | 不需要 build step，直接部署，Railway 成本低 |
| LINE Login | Google OAuth | 目標用戶（台灣）LINE 普及率高 |
| Railway + PostgreSQL | Heroku / Render | 免費額度夠、PostgreSQL plugin 內建、部署快 |
| APScheduler | Celery / RQ | 不需要額外 Redis，Railway 單服務即可跑排程 |

> SQLAlchemy 混用 Async（router）與 Sync（排程）是刻意設計，不是技術債。

---

## 二、業務對映表

> 同一業務概念散在多處，改一處必須同步以下所有點。

### 版本號（最常漏改）

| 位置 | 格式 |
|------|------|
| `app/config.py` → `APP_VERSION` | `"1.13.0"` |
| `CLAUDE.md` 〇章「當前版本」| `V1.13.0` |
| `README.md` 「目前版本」| `V1.13.0` |
| `app/main.py` features list | `"V1.13.0: ..."` |

**改版本 = 動以上 4 個地方**

### 情緒指數資料路徑（V1.12.3 血淚教訓）

| 層次 | 欄位 | 說明 |
|------|------|------|
| `routers/market.py` 回傳 | `{success, stock, crypto}` | **頂層欄位，不是 `data.xxx`** |
| `services/market_service.py` | `result["stock"]`, `result["crypto"]` | dict key |
| `static/js/dashboard.js` | `data.stock`, `data.crypto` | **絕對不是 `data.data?.stock`** |

### 認證依賴（統一出口）

```python
# 一律從這裡 import，不要各 router 自己實作
from app.dependencies import get_current_user, get_admin_user, get_optional_user
```

### 技術指標欄位名（全小寫）

`ma5`, `ma10`, `ma20`, `ma60`, `ma120`, `ma240`, `rsi`, `macd_dif`, `macd_dea`, `macd_hist`, `kd_k`, `kd_d`, `bb_upper`, `bb_middle`, `bb_lower`, `obv`

---

## 三、關鍵檔案路徑

| 想改什麼 | 動哪些檔 |
|---------|---------|
| 版本號 | `app/config.py`, `CLAUDE.md`, `README.md`, `app/main.py` |
| 認證邏輯 | `app/dependencies/auth.py`（唯一出口）|
| 排程任務 | `app/main.py` 的 `setup_scheduler()` + 各任務函數 |
| DB session（排程用）| `app/main.py` 的 `sync_db_session()` context manager |
| 情緒指數資料 | `app/data_sources/fear_greed.py` + `app/services/market_service.py` |
| 前端認證 / session | `static/js/core.js` 的 `checkAuth()` + `updateUserUI()` |
| 版本號顯示（前端）| `static/js/core.js` 的 `loadAppVersion()` → 4 個 element |
| LINE Login callback | `app/routers/auth.py` 的 `/auth/line/callback` |
| 管理後台 | `static/admin.html` + `app/routers/admin.py` |

---

## 四、踩過的坑（編號累積，永不重排）

> 對應 Kit 全域坑編號標 `[Kit #N]`。

**#1. 情緒指數永遠顯示 50/Neutral（資料路徑誤改）**
- 症狀：兩個情緒指數都固定顯示 50，Neutral，DB 明明有正確資料
- 原因：重構括號修復時把 `data.stock` 誤改成 `data.data?.stock`；`/api/market/sentiment` 回傳頂層欄位，不是 `data` 包一層 `[Kit #3]`
- 做法：每次改 API 解析前先用 DevTools Network tab 看實際回傳結構

**#2. JS 多個函數缺結尾 `}`，整個模組無法載入**
- 症狀：`window.apiRequest`, `window.$` 全是 undefined；SyntaxError
- 原因：手動修 JS 留注釋殘留破壞縮排對齊，`}` 歸屬混亂；`dashboard.js` 共 4 個函數缺結尾 `[Kit #23]`
- 做法：改完 JS 必跑 `node --check 檔案.js`，不靠人工數括號

**#3. `auth.py NameError: User is not defined`（啟動即 crash）**
- 症狀：Railway 部署後整個服務無法啟動，所有 API 回 502
- 原因：`debug-logs` endpoint 用了 `User` 型別，但 `routers/auth.py` 沒 import `User`
- 做法：打包前跑 `python -c "from app.main import app"` 驗證所有 import

**#4. Bearer token 解析在 3 個地方各自重複**
- 症狀：修認證邏輯時要改 3 個地方，漏改一個就行為不一致 `[Kit #5]`
- 原因：早期各 router 各自實作 `get_current_user`，沒統一出口
- 做法：V1.12.2 起統一到 `app/dependencies/auth.py`，router 全部 Depends 這裡

**#5. 排程 DB session 6 個函數各自開關，有一個漏了 `finally`**
- 症狀：服務跑一陣子後 connection pool 漸耗盡 `[Kit #24]`
- 原因：複製貼上的樣板程式，其中一個加了 `with sync_db_session()` 卻殘留舊的 `finally: db.close()`
- 做法：V1.12.2 起用 `sync_db_session()` context manager 統一管理

**#6. XSS via LINE 用戶名稱字串插值 `[Kit #18]`**
- 症狀：用戶名稱含 `"` 或 `</script>` 可執行任意 JS
- 原因：`html_content = f"""... "{user.display_name}" ..."""` 直接插入
- 做法：`json.dumps()` 整包序列化 + display 用 HTML escape

**#7. CNN Fear & Greed API 單一來源，Railway IP 被封就全壞 `[Kit #15]`**
- 症狀：美股情緒指數永遠顯示 fallback 值 50
- 原因：`_get_fear_greed_alternative()` 直接 `return None`，沒實作任何備用
- 做法：V1.12.2 加了 feargreedmeter.com + alternative.me 兩個備用來源

**#8. DB 情緒資料無新鮮度檢查，讀到過期舊值**
- 症狀：指數更新後前端仍顯示舊資料，必須手動觸發排程才更新
- 原因：`get_latest_sentiment()` 不管資料是幾天前的都直接回傳
- 做法：V1.12.2 加 12 小時新鮮度檢查，過期自動呼叫外部 API

**#9. State token 完整印到 Railway log**
- 症狀：log 中可見完整 state token，若 log 被第三方取得可被 CSRF 攻擊
- 原因：`logger.info(f"Created state: {state}")` 把完整 64 位元 token 印出
- 做法：改為 `{state[:8]}...{state[-4:]}`，只印前後識別碼

---

## 五、煙霧測試（可貼上執行）

```bash
# Python 語法驗證
python3 -c "
import ast, os
for root, dirs, files in os.walk('app'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            ast.parse(open(path, encoding='utf-8').read())
print('✅ Python 語法全通過')
"

# JS 語法驗證
node --check static/js/*.js && echo "✅ JS 語法全通過"

# FastAPI 路由確認（啟動驗證）
python -c "from app.main import app; print(len(app.routes), 'routes')"

# 版本號一致性
python -c "
from app.config import settings
print('APP_VERSION:', settings.APP_VERSION)
" 
# 預期：1.13.0

# 找漏掉的 debug 輸出
grep -rn "print(" app/ | grep -v "logger\|# " || true
```

---

## 六、版本歷程（最近 10 版）

| 版本 | 重點 |
|------|------|
| V1.13.0 | Kit 首次對齊：SELA 真實 favicon 套組、CLAUDE.md 改為九章章法格式、README 補 SELA logo、SELA-handoff.md 產出 |
| V1.12.3 | 修復情緒指數顯示：`data.data?.stock` 改回 `data.stock` |
| V1.12.2 | JS 語法修復（core.js try/catch、dashboard.js 4 處缺 `}`）；資安強化（XSS、rate limit）；重構（Bearer 解析、sync_db_session）；情緒指數多來源 |
| V1.12.1 | 修復啟動 crash（`NameError: User`）|
| V1.12 | 前端診斷日誌（`/auth/debug-log`）；管理後台診斷區塊 |
| V1.11 | 前端 JS 性能優化（DOM 快取、批量更新、命名空間）|
| V1.10 | 版本號動態顯示（4 個 element）；cache-only 市場指數 |
| V1.05 | 技術指標預計算排程；清除過期快取 |
| V1.02 | 極簡排程：只在交易時段更新（Railway 省費）|
| V1.01 | 內存快取：非交易時段直接回 DB，10–40x 性能提升 |

---

## 七、下版候選工作（按優先序）

1. **追蹤清單載入性能診斷** — 用戶反映追蹤清單開啟慢，需查清楚是 API 回應慢還是前端渲染瓶頸
2. 券商功能部署驗證 — broker 相關 API 已開發，確認 Railway 上正常運作
3. 訂閱精選排程驗證 — scheduler 是否確實有觸發 RSS 抓取
4. 前端整體性能優化（P2）— 減少不必要的重渲染
5. `compare.html` 走勢比較頁的 LINE Login 狀態同步

---

## 八、升版必讀

### Railway 部署流程

```
□ 更新版本號（4 個地方，見業務對映表）
□ node --check static/js/*.js 全綠
□ python3 -c "from app.main import app" 確認無 ImportError
□ 打包 zip：排除 .git, __pycache__, .env, venv/, *.log, .DS_Store
□ Railway：推送新版，等待 cold start（約 30–60 秒）
□ 部署後驗證：登入流程、追蹤清單、情緒指數數值是否正確
```

### 環境變數（新環境必設）

| 變數 | 說明 |
|------|------|
| `DATABASE_URL` | PostgreSQL（Railway 自動提供）|
| `JWT_SECRET_KEY` | 隨機長字串 |
| `LINE_LOGIN_CHANNEL_ID` | LINE Login Channel ID |
| `LINE_LOGIN_CHANNEL_SECRET` | LINE Login Channel Secret |
| `LINE_LOGIN_CALLBACK_URL` | `https://你的網域/auth/line/callback` |
| `APP_ENV` | `production` |
| `ADMIN_LINE_IDS` | 管理員 LINE User ID（逗號分隔）|

> LINE Developers Console 必須把 Callback URL 加入（每個環境各一條）。

---

## 九、一句話總結

V1.13.0 完成首次 Kit 對齊（SELA 真實 favicon、CLAUDE.md 九章格式），累積了 9 條專案坑與 Kit 編號交叉對照；下版第一優先是追蹤清單載入性能診斷。
