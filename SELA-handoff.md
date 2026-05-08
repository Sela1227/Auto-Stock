# SELA-handoff.md — AutoStock（SELA 自動選股系統）

> 產出時機：首次對齊 Kit（V1.13.0）= 重大里程碑必產出
> 完成版本：V1.13.0（2026-04-12）

---

## 〇、專案速覽

- **專案名稱：** AutoStock（SELA 自動選股分析系統）
- **專案類型：** FastAPI 後端 + Vanilla JS 前端 + PostgreSQL，Railway 部署
- **技術棧：** Python 3.11 + FastAPI + SQLAlchemy 2.0 + PostgreSQL + Vanilla JS + Tailwind CSS + APScheduler + LINE Login + JWT
- **規模：** ~30 個 Python 檔、~20 個 JS 檔、~15,000 行
- **使用 Kit 版本：** V1.8.1（首次對齊）
- **完成版本：** V1.13.0
- **完成日期：** 2026-04-12

---

## 一、用 Kit 的整體感受

### 預期外的順利

- `cross-project-pitfalls.md` 的坑 #3、#5、#18、#23、#24 全部在這個專案出現過，Kit 的診斷描述非常準確，對照後馬上找到原因

### 預期外的卡住

- 本專案是「已有 13 個版本的成熟專案」，Kit 的 SOP 預設「從零建立」，第一次套用時很多步驟不適用（坑 #40 的情境）
- `CLAUDE.md` 結構改為九章格式時，累積的踩坑紀錄需要重新整理，花了一些時間

### 整體評價

- ✓ 坑庫的三段式（症狀/原因/做法）+ 全域編號對交叉引用非常有用
- ✓ 業務對映表讓「版本號漏改 4 個地方」這個問題有了系統性的防範
- ✗ 既有成熟專案首次對齊，Kit 的「鐵律/建議/順便/不做四級分類」（坑 #40）非常必要，但在 CLAUDE.md 主入口看不到明確提示

---

## 二、發現的「跨專案通用坑」

### 強烈建議（已在 Kit 有對應坑，屬確認）

以下坑在 Kit 已有對應編號，AutoStock 是確認案例（加強通用性證據）：

- **Kit #3（資料 vs 顯示混用）**：`data.stock` 被誤改成 `data.data?.stock`，一個字元的差異造成整個功能靜默失敗，前端無任何報錯
  - 證據：本專案 CLAUDE.md 坑 #1
  - **特別值得加到 #3 的說明**：「改前端 API 解析前先用 DevTools Network tab 看實際格式」這個做法很有效，值得補進 #3 的做法段

- **Kit #15（外部 API 單一來源）**：CNN Fear & Greed API 在 Railway 部署環境被封，備用方案直接 `return None`
  - 證據：本專案 CLAUDE.md 坑 #7
  - 本案的修法：`find_with_fallback` 模式，依序試多個來源

### 可加的新坑（Kit 目前沒有完整對應）

#### N1. 市場感知快取（按交易時段決定是否呼叫外部 API）

- **症狀**：非交易時段的每次 API 請求都打外部 API（如 Yahoo Finance），Railway 費用快速上升
- **原因**：沒有區分「交易時段需要即時資料」和「非交易時段用 DB 快取即可」兩種場景
- **做法**：
  ```python
  def is_tw_market_open() -> bool:
      now = datetime.now(TW_TZ)
      weekday = now.weekday()
      if weekday >= 5:
          return False
      return time(9, 0) <= now.time() <= time(13, 30)
  ```
  非交易時段直接回 DB 快取，交易時段才打外部 API
- **影響範圍**：所有有排程 + 外部 API 的 FastAPI 專案，特別是 Railway 計費環境
- **效果**：非交易時段 10–40x 性能提升，Railway 費用大幅降低
- **檢查 1 結果**：grep Kit「market hours」「cache strategy」→ 無完整對應

#### N2. FastAPI startup 中 import 型別未定義導致整服務無法啟動

- **症狀**：Railway 部署後整服務 502，log 顯示 `NameError: name 'User' is not defined`，但 Python import 鏈上所有語法都正確
- **原因**：FastAPI 在啟動時就會解析所有 Depends() 的型別提示，某個函數的 type hint 引用了未 import 的類別
- **做法**：打包前必跑 `python -c "from app.main import app; print(len(app.routes), 'routes')"` 強制觸發所有 import
- **影響範圍**：所有 FastAPI 專案，特別是 Depends() 型別提示很多的情況
- **檢查 1 結果**：grep Kit「startup」「NameError」→ 坑 #7 的煙霧測試提到了驗證指令，但沒有特別針對 FastAPI Depends 型別提示這個場景

---

## 三、發現的「跨專案設計模式」

### 1. 單一認證出口（從第 N 個版本才建立，代價昂貴）

- **本案情境**：早期各 router 各自實作 `get_current_user`，到 V1.12.2 才統一到 `dependencies/auth.py`
- **可推廣原則**：FastAPI 專案第一天就建 `dependencies/auth.py`，所有 router 只 import，不自己實作。即使 V0.1.0 只有 1 個 router 也要這樣做
- **代價**：多一個檔案，但省去日後重構的成本
- **建議寫入**：`start-project-decisions.md` 的 FastAPI 起始決策，Kit 坑 #5 已有，但可以加強「第一天就做」的時機說明

### 2. Context Manager 統一管理同步 DB Session

- **本案情境**：6 個排程任務各自 `db = SyncSessionLocal() / try / finally db.close()`，其中一個漏了 `finally`，connection pool 漸耗盡
- **可推廣原則**：只要有超過 2 個地方手動開關同一種 session，就應該抽出 context manager
- **代價**：需要重構，建議在第 3 個函數出現時就做
- **建議寫入**：`tech-stack-lessons.md` FastAPI + SQLAlchemy 段落

---

## 四、Kit 該調整的地方

### Kit 規範修改建議

#### 1. `CLAUDE.md` 主入口補「既有專案首次對齊」快速入口

- **現狀**：CLAUDE.md 的第 2.2 節只有技術棧的路由表，沒有「我是帶著成熟專案來對齊 Kit」的入口
- **建議改成**：在第 2.2 節加一行「**如果你是帶著 N 個版本的既有專案來對齊 Kit，先讀 `conventions/cross-project-pitfalls.md` 的坑 #40**」
- **理由**：坑 #40 的四級分類是正確做法，但 CLAUDE.md 主入口看不到這條

#### 2. `cross-project-pitfalls.md` 坑 #3 補「先看 Network tab 再改」

- **現狀**：做法是「API 回應結構統一」，沒有具體的「診斷步驟」
- **建議補充**：做法段加一句「改前端 API 解析前，先用 DevTools Network tab 確認實際回傳格式，不依賴記憶或推論」

---

## 五、留在這個專案、不要回流 Kit 的東西

- LINE Login 完整 callback 流程（業務特定）
- 台股 / 美股 / 加密貨幣交易時段判斷邏輯（業務模型）
- 情緒指數的多來源備用具體實作（feargreedmeter + alternative.me，業務特定）
- 技術指標計算邏輯（MA / RSI / MACD / KD / BB / OBV，業務模型）
- 追蹤清單 / 投資記錄 / 訂閱精選的業務邏輯
- Railway 的具體部署設定（`railway.json` / `Procfile`）

---

## 六、Kit Claude 的建議行動清單

### 建議升 Kit 版本

V1.9.0（b+1）— 有新坑提案（N1、N2）+ 修改建議 + 補強現有坑 #3

### 必做

- [ ] 坑 #3 做法段補：「改前端 API 解析前，先用 DevTools Network tab 確認實際格式」
- [ ] `CLAUDE.md` 第 2.2 節加既有專案首次對齊的快速入口，指向坑 #40
- [ ] 評估 N1（市場感知快取）是否進坑庫（影響範圍：排程 + 外部 API + 計費環境）
- [ ] 評估 N2（FastAPI startup NameError）是否進坑庫，或補強坑 #7 的煙霧測試指令

### 暫緩

- [ ] `tech-stack-lessons.md` FastAPI + SQLAlchemy 段落補 context manager 模式 — 等更多專案確認

### 不做

- [ ] LINE Login 業務流程進 Kit（業務特定，不通用）
- [ ] 台股交易時段判斷邏輯進 Kit（業務模型）

---

## 七、給 Kit Claude 的最後備註

AutoStock 是 Kit 建立以前就存在的成熟專案，是首個對齊 Kit 的「既有成熟 FastAPI 專案」。坑 #40 的四級分類做法在這個案例完整驗證過，非常適用。

N1（市場感知快取）是這個專案最有商業價值的技術決策，但它的「跨專案通用性」取決於是否有其他用到排程 + 外部 API 的專案 — 建議觀察下一個同類型專案後再決定是否進坑庫。
