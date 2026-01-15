# 🚀 SELA P1 功能包

**建立日期**: 2026-01-16  
**版本**: 1.0.0

---

## 📋 功能清單

| # | 功能 | 狀態 | 說明 |
|---|------|------|------|
| 1 | 訂閱精選前端 Tab | ✅ 已存在 | subscription.js 已實作 |
| 2 | 追蹤清單匯出匯入 | ✅ 已存在 | watchlist.js 已實作 |
| 3 | 持股交易匯出匯入 | 🆕 新增 | portfolio-export-import.js |
| 4 | 追蹤清單分組 Tag | 🆕 新增 | tags.js + tags router |
| 5 | 到價提醒變色 | ✅ 已存在 | watchlist.js 已實作 |
| 6 | stock_info 種子表 | 🆕 新增 | stock_info model + router |

---

## 📁 檔案結構

```
sela_p1/
├── app/
│   ├── models/
│   │   ├── stock_info.py          ← 🆕 股票基本資訊表
│   │   └── watchlist_tag.py       ← 🆕 追蹤清單標籤
│   ├── routers/
│   │   ├── tags.py                ← 🆕 標籤管理 API
│   │   └── stock_info.py          ← 🆕 股票資訊 API
│   └── utils/
│       └── p1_migrations.py       ← 🆕 資料庫遷移
├── static/
│   ├── js/
│   │   ├── tags.js                ← 🆕 標籤前端模組
│   │   └── portfolio-export-import.js ← 🆕 交易匯出匯入
│   └── p1-html-fragments.html     ← 🆕 HTML Modal 片段
├── migrations/
│   └── (遷移腳本整合在 p1_migrations.py)
└── README.md
```

---

## 🚀 部署步驟

### 步驟 1: 複製檔案

```bash
# 解壓縮
unzip sela_p1.zip

# 複製後端檔案
cp sela_p1/app/models/stock_info.py app/models/
cp sela_p1/app/models/watchlist_tag.py app/models/
cp sela_p1/app/routers/tags.py app/routers/
cp sela_p1/app/routers/stock_info.py app/routers/
mkdir -p app/utils
cp sela_p1/app/utils/p1_migrations.py app/utils/

# 複製前端檔案
cp sela_p1/static/js/tags.js static/js/
cp sela_p1/static/js/portfolio-export-import.js static/js/
```

### 步驟 2: 更新 models/__init__.py

在 `app/models/__init__.py` 加入：

```python
from app.models.stock_info import StockInfo
from app.models.watchlist_tag import UserTag, watchlist_tags
```

### 步驟 3: 更新 main.py 路由

在 `app/main.py` 中加入：

```python
from app.routers import tags, stock_info

app.include_router(tags.router)
app.include_router(stock_info.router)
```

### 步驟 4: 更新 database.py 遷移

在 `app/database.py` 的 `run_migrations()` 函數中加入：

```python
# P1 遷移
try:
    from app.utils.p1_migrations import run_p1_migrations
    p1_result = run_p1_migrations(db)
    if p1_result["success"]:
        logger.info(f"P1 遷移成功: {p1_result}")
except Exception as e:
    logger.warning(f"P1 遷移跳過: {e}")
```

### 步驟 5: 更新 dashboard.html

1. **加入 JS 引用** (在 `</body>` 前)：
```html
<script src="/static/js/tags.js"></script>
<script src="/static/js/portfolio-export-import.js"></script>
```

2. **加入 Modal HTML** (從 `p1-html-fragments.html` 複製)：
- 標籤編輯 Modal
- 標籤指派 Modal
- 交易記錄匯入 Modal

3. **在設定頁加入標籤管理區塊**

4. **在持股頁加入匯出匯入按鈕**

### 步驟 6: 初始化種子資料

部署後，管理員可以透過 API 初始化：

```bash
# 初始化股票資訊
POST /api/stock-info/admin/init

# 初始化預設標籤 (每個用戶各自)
POST /api/tags/init-defaults
```

---

## 📖 API 文件

### 標籤 API

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/tags` | 取得我的標籤 |
| POST | `/api/tags` | 建立標籤 |
| PUT | `/api/tags/{id}` | 更新標籤 |
| DELETE | `/api/tags/{id}` | 刪除標籤 |
| POST | `/api/tags/init-defaults` | 初始化預設標籤 |
| GET | `/api/tags/watchlist/{id}` | 取得追蹤項目標籤 |
| PUT | `/api/tags/watchlist/{id}` | 設定追蹤項目標籤 |

### 股票資訊 API

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/stock-info/search?q=xxx` | 搜尋股票 |
| GET | `/api/stock-info/popular` | 熱門股票 |
| GET | `/api/stock-info/by-market/{market}` | 依市場取得 |
| GET | `/api/stock-info/sectors` | 取得產業分類 |
| GET | `/api/stock-info/{symbol}` | 取得單一股票資訊 |
| POST | `/api/stock-info/admin/init` | [管理員] 初始化種子 |
| POST | `/api/stock-info/admin/add` | [管理員] 新增股票 |

### 交易記錄匯出匯入 (現有 API)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/portfolio/export?format=json&market=tw` | 匯出交易記錄 |
| POST | `/api/portfolio/import` | 匯入交易記錄 |

---

## 🗃️ 資料庫變更

### 新增表格

1. **stock_info** - 股票基本資訊種子表
   - symbol (PK)
   - name, name_zh
   - market, exchange, sector
   - is_popular, is_active

2. **user_tags** - 用戶自訂標籤
   - user_id (FK)
   - name, color, icon
   - sort_order

3. **watchlist_tags** - 追蹤項目標籤關聯表
   - watchlist_id (FK)
   - tag_id (FK)

---

## 💡 使用說明

### 標籤功能

1. **建立標籤**：設定頁 → 標籤管理 → 新增標籤
2. **指派標籤**：追蹤清單 → 點擊標籤圖示 → 勾選標籤
3. **篩選**：追蹤清單頂部會顯示標籤篩選按鈕

### 交易記錄匯出匯入

1. **匯出**：持股頁 → 匯出匯入按鈕 → 選擇格式
2. **匯入**：持股頁 → 匯出匯入按鈕 → 匯入記錄 → 選擇檔案

### 股票搜尋自動完成

股票資訊種子表可用於：
- 搜尋框自動完成
- 新增追蹤時的建議
- 顯示中文名稱

---

## ✅ 驗證清單

部署後請驗證：

- [ ] `/api/tags` 回傳空陣列（新用戶）
- [ ] `/api/tags/init-defaults` 建立預設標籤
- [ ] `/api/stock-info/search?q=AAPL` 回傳搜尋結果
- [ ] `/api/stock-info/admin/init` 初始化種子資料
- [ ] 前端標籤管理區塊正常顯示
- [ ] 持股匯出匯入功能正常

---

## 📊 預設種子資料

### 熱門股票 (33 支)
- 美股科技：AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA
- 美股金融：JPM, V, MA
- 美股半導體：AMD, INTC, AVGO
- 台股半導體：2330.TW, 2454.TW, 2303.TW, 3711.TW
- 台股電子：2317.TW, 2382.TW, 2357.TW
- 台股金融：2881.TW, 2882.TW, 2884.TW
- 台股 ETF：0050.TW, 0056.TW, 00878.TW
- 加密貨幣：BTC, ETH, SOL
- 指數：^GSPC, ^DJI, ^IXIC, ^TWII

### 預設標籤 (5 個)
- 長期持有 (綠色)
- 觀望中 (黃色)
- 短線交易 (紅色)
- ETF (藍色)
- 高股息 (紫色)

---

## 🔧 注意事項

1. **P0 依賴**：此功能包依賴 P0 的統一認證模組 (`app/dependencies/auth.py`)

2. **Railway 環境**：遷移會自動執行，無需手動 SQL

3. **標籤限制**：每個用戶最多 20 個標籤

4. **匯入格式**：支援 JSON 和 CSV，必須包含必要欄位
