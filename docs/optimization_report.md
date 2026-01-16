# 🔧 SELA 系統 - 程式碼優化分析報告

> 分析日期：2026-01-16  
> 專案：自動選股系統 (SELA)

---

## 📊 超過 500 行的程式檔案統計

| 優先級 | 檔案 | 行數 | 主要問題 |
|--------|------|------|----------|
| 🔴 P0 | `static/dashboard.html` | 1908 | 單一 HTML 包含所有頁面，難以維護 |
| 🔴 P0 | `static/dashboard-mobile.html` | 1333 | 與 dashboard.html 高度重複 |
| 🟠 P1 | `static/js/search.js` | 888 | 功能過於集中，缺乏模組化 |
| 🟠 P1 | `app/services/indicator_service.py` | 830 | 單一 class 包含所有指標計算 |
| 🟠 P1 | `static/js/watchlist.js` | 811 | 功能過於集中 |
| 🟡 P2 | `app/routers/admin.py` | 690 | Router 過於龐大 |
| 🟡 P2 | `app/cli.py` | 688 | CLI 命令過多 |
| 🟡 P2 | `static/admin.html` | 677 | 單一頁面過大 |
| 🟡 P2 | `static/js/dashboard.js` | 654 | 功能過於集中 |
| 🟡 P2 | `app/tasks/scheduler.py` | 642 | 排程任務混雜 |
| 🟡 P2 | `app/data_sources/yahoo_finance.py` | 621 | 資料源過於龐大 |
| 🟡 P2 | `app/services/compare_service.py` | 601 | 比較服務過於複雜 |
| 🟡 P2 | `static/compare.html` | 597 | 頁面過大 |
| 🟡 P2 | `app/routers/watchlist.py` | 591 | Router 過於龐大 |
| 🟢 P3 | `app/services/signal_service.py` | 551 | 可接受，但建議拆分 |
| 🟢 P3 | `app/services/price_cache_service.py` | 545 | 可接受，但建議拆分 |
| 🟢 P3 | `app/services/chart_service.py` | 543 | 可接受 |
| 🟢 P3 | `app/services/auth_service.py` | 531 | 可接受 |
| 🟢 P3 | `app/services/stock_service.py` | 501 | 可接受 |

---

## 🔴 P0 - 緊急優化（嚴重影響維護性）

### 1. `static/dashboard.html` (1908 行)

**問題分析：**
- 單一 HTML 檔案包含 10+ 個不同頁面區塊
- 內嵌大量 JavaScript 和 CSS
- 桌面版和手機版 UI 混雜
- 每次修改需要搜尋整個檔案

**優化建議：**
```
static/
├── templates/
│   ├── base.html              # 基礎模板（head, 導航, 腳本引入）
│   ├── sections/
│   │   ├── dashboard.html     # 儀表板區塊
│   │   ├── search.html        # 搜尋區塊
│   │   ├── watchlist.html     # 追蹤清單區塊
│   │   ├── portfolio.html     # 投資組合區塊
│   │   ├── compare.html       # 比較區塊
│   │   ├── settings.html      # 設定區塊
│   │   └── modals/            # Modal 對話框
│   │       ├── add-stock.html
│   │       ├── tag-edit.html
│   │       └── ...
│   └── components/
│       ├── sidebar.html       # 側邊欄元件
│       ├── navbar.html        # 頂部導航
│       └── stock-card.html    # 股票卡片元件
```

**實作方式：**
- 使用 FastAPI 的 Jinja2 模板引擎
- 透過 `{% include %}` 組合頁面
- 或使用前端框架如 Alpine.js 的元件系統

---

### 2. `static/dashboard-mobile.html` (1333 行)

**問題分析：**
- 與 `dashboard.html` 有 70%+ 的重複代碼
- 手機版應該是響應式設計，不是獨立檔案
- 修改功能需要同步兩個檔案

**優化建議：**
- **刪除此檔案**
- 將響應式設計整合到 `dashboard.html`
- 使用 Tailwind CSS 的響應式類別 (`md:`, `lg:`)
- 使用 CSS Media Queries 處理差異

```html
<!-- 桌面版側邊欄 -->
<aside class="hidden md:block w-64">...</aside>

<!-- 手機版底部導航 -->
<nav class="fixed bottom-0 md:hidden">...</nav>
```

---

## 🟠 P1 - 重要優化（影響開發效率）

### 3. `static/js/search.js` (888 行)

**問題分析：**
- 包含：搜尋、結果渲染、全螢幕圖表、成交量圖表、MA 進階分析
- 單一 IIFE 包含所有功能
- 難以獨立測試和複用

**優化建議：**
```
static/js/
├── modules/
│   ├── search-core.js         # 搜尋邏輯 (~150行)
│   ├── search-render.js       # 結果渲染 (~200行)
│   ├── chart-fullscreen.js    # 全螢幕圖表 (~150行)
│   ├── chart-volume.js        # 成交量圖表 (~100行)
│   └── ma-analysis.js         # MA 進階分析 (~200行)
└── search.js                  # 整合入口 (~50行)
```

---

### 4. `app/services/indicator_service.py` (830 行)

**問題分析：**
- 單一 class `IndicatorService` 包含所有指標
- MA、RSI、MACD、KD、布林通道、OBV 全部混在一起
- 新增指標需要修改此巨型檔案

**優化建議：**
```
app/services/indicators/
├── __init__.py               # 統一導出
├── base.py                   # 基礎類別和共用工具 (~100行)
├── ma_indicator.py           # 移動平均線 (~150行)
├── rsi_indicator.py          # RSI 指標 (~100行)
├── macd_indicator.py         # MACD 指標 (~100行)
├── kd_indicator.py           # KD 指標 (~100行)
├── bollinger_indicator.py    # 布林通道 (~100行)
├── obv_indicator.py          # OBV 指標 (~80行)
└── composite_service.py      # 組合服務（調用各指標）(~100行)
```

**範例程式碼：**
```python
# app/services/indicators/base.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseIndicator(ABC):
    """指標基礎類別"""
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def get_signal(self, df: pd.DataFrame) -> dict:
        pass


# app/services/indicators/rsi_indicator.py
class RSIIndicator(BaseIndicator):
    def __init__(self, period: int = 14, overbought: int = 70, oversold: int = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        # RSI 計算邏輯
        ...
```

---

### 5. `static/js/watchlist.js` (811 行)

**優化建議：**
```
static/js/
├── watchlist/
│   ├── index.js              # 入口
│   ├── list-manager.js       # 清單管理 CRUD
│   ├── price-display.js      # 價格顯示和更新
│   ├── tag-manager.js        # 標籤管理
│   └── export-import.js      # 匯出匯入功能
```

---

## 🟡 P2 - 建議優化（改善代碼品質）

### 6. `app/routers/admin.py` (690 行)

**優化建議：**
```
app/routers/admin/
├── __init__.py              # 主路由整合
├── user_management.py       # 用戶管理 API
├── system_config.py         # 系統設定 API
├── data_management.py       # 資料管理 API
└── statistics.py            # 統計報表 API
```

---

### 7. `app/tasks/scheduler.py` (642 行)

**問題分析：**
- 包含台股名稱對照表（約 200 行）
- 混雜多種排程任務
- 台股名稱應該在資料庫或獨立設定檔

**優化建議：**
```
app/
├── data/
│   └── taiwan_stock_names.json  # 台股名稱對照（移出代碼）
├── tasks/
│   ├── scheduler.py              # 排程器設定 (~100行)
│   ├── price_tasks.py            # 價格更新任務
│   ├── notification_tasks.py     # 通知任務
│   └── cleanup_tasks.py          # 清理任務
```

---

### 8. `app/data_sources/yahoo_finance.py` (621 行)

**優化建議：**
```
app/data_sources/
├── yahoo_finance/
│   ├── __init__.py
│   ├── fetcher.py           # 資料抓取
│   ├── parser.py            # 資料解析
│   ├── cache.py             # 快取處理
│   └── taiwan_handler.py    # 台股特殊處理
```

---

## 🟢 P3 - 可選優化

以下檔案行數在 500-560 行之間，結構尚可接受，但長期維護建議拆分：

- `app/services/signal_service.py` (551行) - 可拆分為多個信號類型
- `app/services/price_cache_service.py` (545行) - 可拆分快取策略
- `app/services/chart_service.py` (543行) - 可按圖表類型拆分

---

## 📝 優化執行順序建議

### 第一階段（1-2 週）
1. ✅ 刪除 `dashboard-mobile.html`，整合響應式設計
2. ✅ 將台股名稱移出 `scheduler.py` 到 JSON 設定檔
3. ✅ 刪除 `__init__ (1).py`、`.bak` 檔案

### 第二階段（2-3 週）
4. 🔄 拆分 `indicator_service.py` 為獨立指標模組
5. 🔄 拆分 `search.js` 為功能模組

### 第三階段（3-4 週）
6. 📋 重構 `dashboard.html` 為模板系統
7. 📋 拆分 `admin.py` 路由

### 第四階段（持續改進）
8. 📋 逐步優化其他 P2、P3 檔案

---

## 💡 重構原則

1. **單一職責原則**：每個檔案只做一件事
2. **300 行規則**：單一檔案盡量不超過 300 行
3. **模組化**：相關功能組織在同一資料夾
4. **可測試性**：拆分後的模組應該可以獨立測試
5. **漸進式**：每次只改一個檔案，確保不破壞功能

---

*報告結束*
