# 🚀 SELA 功能整合指南

> 版本: v0.9.1  
> 最後更新: 2026-01-12  
> 適用專案: SELA 多用戶選股分析系統

---

## 📋 功能清單總覽

| # | 功能名稱 | 優先級 | 複雜度 | 預估工時 | 狀態 |
|---|---------|--------|--------|---------|------|
| 1 | 設定頁面 UI | P0 | 中 | 4h | 待整合 |
| 2 | 儀表板比特幣價格 | P2 | 低 | 1h | 待整合 |
| 3 | 管理員登入自動更新 | P1 | 低 | 2h | 待開發 |
| 4 | 個人買賣股票管理 | P0 | 高 | 8h | 待開發 |
| 5 | 列表清單排序 | P1 | 中 | 3h | 待開發 |

---

# 功能 1: 設定頁面 UI

## 1.1 功能概述

新增用戶設定頁面 UI，包含：
- 快速模板（極簡/標準/完整/短線）
- 指標顯示開關（7 種技術指標）
- 通知設定開關（8 種 LINE 推播警報）
- 進階參數調整（14 種可自訂參數）

## 1.2 新增檔案

| 檔案 | 位置 | 說明 |
|------|------|------|
| `settings.css` | `static/css/` | 設定頁面樣式 |
| `settings.js` | `static/js/` | 設定頁面邏輯 |
| `settings-section.html` | `static/` | HTML 片段 |

## 1.3 整合步驟

### 步驟 1: 複製靜態資源

```bash
cp -r settings-ui-update/static/css /path/to/project/static/
cp -r settings-ui-update/static/js /path/to/project/static/
```

### 步驟 2: 在 dashboard.html 引入資源

在 `<head>` 區塊內加入 CSS：

```html
<!-- 設定頁面樣式 -->
<link rel="stylesheet" href="/static/css/settings.css">
```

在 `</body>` 標籤之前加入 JavaScript：

```html
<!-- 設定頁面腳本 -->
<script src="/static/js/settings.js"></script>
```

### 步驟 3: 加入 HTML 結構

將 `settings-section.html` 的內容複製到 dashboard.html 中，放在其他 section 之後：

```html
<!-- 現有的 sections -->
<section id="section-dashboard" class="section">...</section>
<section id="section-watchlist" class="section hidden">...</section>
<section id="section-compare" class="section hidden">...</section>

<!-- 新增：設定頁面 section -->
<section id="section-settings" class="section hidden">
    <!-- 從 settings-section.html 複製內容 -->
</section>
```

### 步驟 4: 新增導航連結

**桌面版導航列：**

```html
<a onclick="showSection('settings', event)" 
   class="nav-link flex items-center px-4 py-2 text-gray-600 hover:bg-blue-50 hover:text-gray-700 rounded-lg transition-colors cursor-pointer">
    <i class="fas fa-cog mr-2"></i>
    設定
</a>
```

**手機版底部導航：**

```html
<button onclick="showSection('settings', event)" 
        class="nav-tab flex flex-col items-center py-2 px-3 text-gray-500 hover:text-orange-500 transition-colors">
    <i class="fas fa-cog text-lg"></i>
    <span class="text-xs mt-1">設定</span>
</button>
```

### 步驟 5: 更新 showSection 函數

在現有的 `showSection` 函數中加入：

```javascript
function showSection(name, evt) {
    // ... 原有的 section 切換邏輯 ...
    
    // 切換到設定頁時載入設定
    if (name === 'settings') {
        if (typeof initSettingsPage === 'function') {
            initSettingsPage();
        }
    }
}
```

### 步驟 6: 更新用戶資訊顯示

在登入成功後，更新設定頁面的用戶資訊：

```javascript
function updateSettingsUserInfo() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    const avatar = document.getElementById('settings-user-avatar');
    const name = document.getElementById('settings-user-name');
    const level = document.getElementById('settings-user-level');
    
    if (avatar && user.avatar_url) {
        avatar.src = user.avatar_url;
    }
    if (name) {
        name.textContent = user.display_name || '用戶';
    }
    if (level) {
        level.textContent = user.is_admin ? '管理員' : '免費會員';
    }
}

// 在 checkAuth() 成功後調用
updateSettingsUserInfo();
```

## 1.4 API 依賴

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/settings/indicators` | GET/PUT | 指標顯示設定 |
| `/api/settings/alerts` | GET/PUT | 通知設定 |
| `/api/settings/params` | GET/PUT | 參數設定 |
| `/api/settings/template/{name}` | POST | 套用預設模板 |

## 1.5 驗證清單

- [ ] CSS 檔案已複製到 `/static/css/`
- [ ] JS 檔案已複製到 `/static/js/`
- [ ] dashboard.html 已引入 CSS
- [ ] dashboard.html 已引入 JS
- [ ] HTML section 已加入
- [ ] 導航連結已加入（桌面版 + 手機版）
- [ ] showSection 函數已更新
- [ ] 測試：可以切換到設定頁面
- [ ] 測試：設定可以正常載入/儲存
- [ ] 測試：模板可以正常套用

---

# 功能 2: 儀表板比特幣價格

## 2.1 功能概述

在儀表板頁面新增比特幣價格卡片，位置在恐懼貪婪指數下方。

**功能特色：**
- 即時 BTC 價格（美元）
- 24h 漲跌幅 + 週/月漲跌
- 動態背景色（大漲綠、大跌紅、平盤橘）
- 每 60 秒自動更新
- 點擊跳轉查詢 BTC 詳情

## 2.2 UI 設計

| 狀態 | 背景色 |
|------|--------|
| 大漲 (≥3%) | 綠色漸層 |
| 大跌 (≤-3%) | 紅色漸層 |
| 平盤 | 橘黃漸層（預設） |

## 2.3 整合方式

直接用更新包中的 `static/dashboard.html` 替換專案中的同名檔案。

**或手動加入以下程式碼：**

### HTML 部分

在儀表板區塊加入：

```html
<!-- 比特幣價格卡片 -->
<div id="btc-price-card" 
     onclick="searchStock('BTC')" 
     class="bg-gradient-to-br from-orange-500 to-yellow-500 rounded-xl p-4 text-white cursor-pointer hover:shadow-lg transition-shadow">
    <div class="flex items-center justify-between">
        <div>
            <div class="text-sm opacity-80">Bitcoin</div>
            <div class="text-2xl font-bold" id="btc-price">$--,---</div>
        </div>
        <div class="text-right">
            <div class="text-lg font-semibold" id="btc-change-24h">--%</div>
            <div class="text-xs opacity-80">24h</div>
        </div>
        <i class="fab fa-bitcoin text-4xl opacity-50"></i>
    </div>
    <div class="mt-2 flex justify-between text-xs opacity-80">
        <span>週: <span id="btc-change-week">--%</span></span>
        <span>月: <span id="btc-change-month">--%</span></span>
    </div>
</div>
```

### JavaScript 部分

```javascript
async function loadBtcPrice() {
    try {
        const res = await fetch(`${API_BASE}/api/crypto/BTC`);
        const data = await res.json();
        
        if (data.success) {
            const price = data.price.current;
            const change24h = data.change.day;
            const changeWeek = data.change.week;
            const changeMonth = data.change.month;
            
            // 更新價格
            document.getElementById('btc-price').textContent = 
                `$${price.toLocaleString('en-US', {minimumFractionDigits: 0})}`;
            
            // 更新漲跌幅
            const change24hEl = document.getElementById('btc-change-24h');
            change24hEl.textContent = `${change24h >= 0 ? '+' : ''}${change24h.toFixed(2)}%`;
            
            document.getElementById('btc-change-week').textContent = 
                `${changeWeek >= 0 ? '+' : ''}${changeWeek.toFixed(1)}%`;
            document.getElementById('btc-change-month').textContent = 
                `${changeMonth >= 0 ? '+' : ''}${changeMonth.toFixed(1)}%`;
            
            // 動態背景色
            const card = document.getElementById('btc-price-card');
            card.className = card.className.replace(/from-\w+-\d+ to-\w+-\d+/g, '');
            
            if (change24h >= 3) {
                card.classList.add('from-green-500', 'to-emerald-600');
            } else if (change24h <= -3) {
                card.classList.add('from-red-500', 'to-rose-600');
            } else {
                card.classList.add('from-orange-500', 'to-yellow-500');
            }
        }
    } catch (e) {
        console.error('載入 BTC 價格失敗:', e);
    }
}

// 頁面載入時執行
document.addEventListener('DOMContentLoaded', () => {
    loadBtcPrice();
    // 每 60 秒更新
    setInterval(loadBtcPrice, 60000);
});
```

## 2.4 API 依賴

```
GET /api/crypto/BTC

Response:
{
    "success": true,
    "price": { "current": 97000 },
    "change": { "day": 2.5, "week": 5.2, "month": 10.3 }
}
```

## 2.5 驗證清單

- [ ] BTC 價格卡片顯示在儀表板
- [ ] 價格格式化（千分位）
- [ ] 漲跌幅正確顯示
- [ ] 顏色正確（綠漲紅跌）
- [ ] 背景色動態變化
- [ ] 60 秒自動更新
- [ ] 點擊跳轉查詢 BTC
- [ ] 響應式設計（手機/桌面）

---

# 功能 3: 管理員登入自動更新

## 3.1 功能概述

管理員登入後，自動在背景觸發系統更新，不阻塞登入流程。

## 3.2 觸發時機

- 管理員成功登入時（`is_admin=True`）
- 僅觸發一次

## 3.3 更新項目

```python
AUTO_UPDATE_TASKS = [
    "update_stock_prices",      # 更新股票價格快取
    "update_crypto_prices",     # 更新加密貨幣價格
    "update_market_sentiment",  # 更新恐懼貪婪指數
    "cleanup_old_data",         # 清理過期數據
]
```

## 3.4 技術設計

### 後端修改

**檔案:** `app/routers/auth.py`

```python
# 在 LINE callback 處理成功登入後加入

@router.get("/callback")
async def line_callback(..., background_tasks: BackgroundTasks):
    # ... 現有登入邏輯 ...
    
    # 管理員登入觸發自動更新
    if user.is_admin:
        background_tasks.add_task(trigger_admin_updates, db)
    
    return RedirectResponse(...)


async def trigger_admin_updates(db: Session):
    """管理員登入觸發的背景更新"""
    from app.services.price_cache_service import PriceCacheService
    
    logger.info("🔄 管理員登入，觸發自動更新...")
    
    try:
        cache_service = PriceCacheService(db)
        
        # 1. 更新所有追蹤股票價格
        result = cache_service.update_all_prices()
        logger.info(f"股票價格更新: {result}")
        
        # 2. 更新市場情緒
        from app.services.market_service import market_service
        market_service.update_fear_greed()
        
        logger.info("✅ 自動更新完成")
        
    except Exception as e:
        logger.error(f"自動更新失敗: {e}")
```

### API 端點（可選）

```
POST /api/admin/trigger-update
Authorization: Bearer {admin_token}

Response:
{
    "success": true,
    "message": "更新已觸發",
    "tasks": ["stock_prices", "crypto_prices", "market_sentiment"]
}
```

## 3.5 前端提示（可選）

登入後在儀表板顯示 Toast 提示：

```javascript
if (user.is_admin) {
    showToast('🔄 系統正在背景更新數據...', 'info');
}
```

## 3.6 驗證清單

- [ ] 管理員登入後自動觸發更新
- [ ] 更新在背景執行，不影響登入
- [ ] 更新日誌正確記錄

---

# 功能 4: 個人買賣股票管理

## 4.1 功能概述

用戶可記錄個人股票買賣交易，追蹤持股和損益。

## 4.2 資料庫設計

### 新增檔案

**檔案:** `app/models/portfolio.py`

```python
"""
個人投資組合模型
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class PortfolioTransaction(Base):
    """交易紀錄"""
    
    __tablename__ = "portfolio_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 股票資訊
    symbol = Column(String(20), nullable=False)           # 股票代碼
    name = Column(String(100))                            # 股票名稱
    market = Column(String(10), nullable=False)           # tw / us
    
    # 交易資訊
    transaction_type = Column(String(10), nullable=False) # buy / sell
    quantity = Column(Integer, nullable=False)            # 股數
    price = Column(Numeric(12, 4), nullable=False)        # 成交價
    fee = Column(Numeric(10, 2), default=0)               # 手續費
    tax = Column(Numeric(10, 2), default=0)               # 交易稅（賣出時）
    transaction_date = Column(Date, nullable=False)       # 交易日期
    
    # 備註
    note = Column(String(500))
    
    # 時間戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_portfolio_user', 'user_id'),
        Index('idx_portfolio_symbol', 'symbol'),
        Index('idx_portfolio_market', 'market'),
        Index('idx_portfolio_date', 'transaction_date'),
    )
    
    @property
    def total_cost(self) -> float:
        """總成本（含手續費）"""
        base = float(self.quantity) * float(self.price)
        if self.transaction_type == "buy":
            return base + float(self.fee or 0)
        else:  # sell
            return base - float(self.fee or 0) - float(self.tax or 0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "transaction_type": self.transaction_type,
            "quantity": self.quantity,
            "price": float(self.price),
            "fee": float(self.fee or 0),
            "tax": float(self.tax or 0),
            "total_cost": self.total_cost,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PortfolioHolding(Base):
    """持股彙總"""
    
    __tablename__ = "portfolio_holdings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100))
    market = Column(String(10), nullable=False)
    
    # 持股資訊
    total_shares = Column(Integer, default=0)              # 總持股
    avg_cost = Column(Numeric(12, 4), default=0)           # 平均成本
    total_invested = Column(Numeric(14, 2), default=0)     # 總投入金額
    realized_profit = Column(Numeric(14, 2), default=0)    # 已實現損益
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_holding_user_symbol', 'user_id', 'symbol', 'market', unique=True),
    )
```

## 4.3 API 設計

**檔案:** `app/routers/portfolio.py`

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/portfolio/transactions` | 取得交易紀錄 |
| POST | `/api/portfolio/transactions` | 新增交易 |
| PUT | `/api/portfolio/transactions/{id}` | 修改交易 |
| DELETE | `/api/portfolio/transactions/{id}` | 刪除交易 |
| GET | `/api/portfolio/holdings` | 取得持股總覽 |
| GET | `/api/portfolio/holdings/{market}` | 取得特定市場持股 |
| GET | `/api/portfolio/summary` | 取得投資摘要 |

### 請求格式

```python
# POST /api/portfolio/transactions
class TransactionCreate(BaseModel):
    symbol: str                     # "2330" 或 "AAPL"
    name: Optional[str] = None      # "台積電" 或 "Apple"
    market: str                     # "tw" 或 "us"
    transaction_type: str           # "buy" 或 "sell"
    quantity: int                   # 股數
    price: float                    # 成交價
    fee: Optional[float] = 0        # 手續費
    tax: Optional[float] = 0        # 交易稅
    transaction_date: date          # 交易日期
    note: Optional[str] = None      # 備註
```

### 回應格式

```python
# GET /api/portfolio/summary
{
    "success": true,
    "data": {
        "total_invested": 100000,     # 總投入
        "current_value": 120000,      # 現值
        "unrealized_profit": 20000,   # 未實現損益
        "realized_profit": 5000,      # 已實現損益
        "total_profit": 25000,        # 總損益
        "return_rate": 25.0,          # 報酬率 %
        "tw_count": 5,                # 台股持股數
        "us_count": 3,                # 美股持股數
    }
}
```

## 4.4 前端頁面結構

```
📊 投資組合
├── 📈 總覽卡片
│   ├── 總資產
│   ├── 總損益
│   └── 報酬率
├── 🔄 Tab 切換
│   ├── 台股
│   └── 美股
├── 📋 持股列表
│   ├── 股票名稱
│   ├── 持股數
│   ├── 平均成本
│   ├── 現價
│   └── 損益
└── ➕ 新增交易按鈕
```

## 4.5 新增檔案清單

| 檔案 | 說明 |
|------|------|
| `app/models/portfolio.py` | 投資組合資料模型 |
| `app/routers/portfolio.py` | 投資組合 API |
| `app/services/portfolio_service.py` | 投資組合業務邏輯 |
| `static/js/portfolio.js` | 投資組合前端 |
| `static/css/portfolio.css` | 投資組合樣式 |

## 4.6 驗證清單

- [ ] 可新增/編輯/刪除交易紀錄
- [ ] 台股/美股分開顯示
- [ ] 持股和損益計算正確
- [ ] 手機版顯示正常

---

# 功能 5: 列表清單排序

## 5.1 功能概述

各種列表支援點擊欄位標題排序。

## 5.2 適用頁面

1. 自選股列表（`watchlist`）
2. 比較頁面（`compare`）
3. 投資組合（`portfolio`）

## 5.3 通用排序模組

**檔案:** `static/js/table-sort.js`

```javascript
/**
 * 表格排序模組
 */
class TableSorter {
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        this.data = [];
        this.currentSort = { column: null, direction: 'asc' };
        this.options = {
            onSort: options.onSort || null,
            savePreference: options.savePreference !== false,
            storageKey: options.storageKey || `sort_${tableId}`,
        };
        
        this.init();
    }
    
    init() {
        // 載入儲存的偏好
        if (this.options.savePreference) {
            const saved = localStorage.getItem(this.options.storageKey);
            if (saved) {
                this.currentSort = JSON.parse(saved);
            }
        }
        
        // 綁定標題點擊事件
        this.bindHeaders();
    }
    
    bindHeaders() {
        const headers = this.table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sort(header.dataset.sort);
            });
            
            // 加入排序圖示
            const icon = document.createElement('i');
            icon.className = 'fas fa-sort ml-1 opacity-30';
            header.appendChild(icon);
        });
    }
    
    setData(data) {
        this.data = [...data];
        if (this.currentSort.column) {
            this.applySort();
        }
    }
    
    sort(column) {
        // 切換方向
        if (this.currentSort.column === column) {
            this.currentSort.direction = 
                this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.column = column;
            this.currentSort.direction = 'asc';
        }
        
        // 儲存偏好
        if (this.options.savePreference) {
            localStorage.setItem(
                this.options.storageKey, 
                JSON.stringify(this.currentSort)
            );
        }
        
        this.applySort();
        this.updateIcons();
    }
    
    applySort() {
        const { column, direction } = this.currentSort;
        
        this.data.sort((a, b) => {
            let valA = a[column];
            let valB = b[column];
            
            // 處理數字
            if (typeof valA === 'string' && !isNaN(parseFloat(valA))) {
                valA = parseFloat(valA);
                valB = parseFloat(valB);
            }
            
            // 處理 null/undefined
            if (valA == null) return 1;
            if (valB == null) return -1;
            
            // 比較
            let result = 0;
            if (typeof valA === 'string') {
                result = valA.localeCompare(valB, 'zh-TW');
            } else {
                result = valA - valB;
            }
            
            return direction === 'asc' ? result : -result;
        });
        
        // 觸發回調
        if (this.options.onSort) {
            this.options.onSort(this.data, this.currentSort);
        }
    }
    
    updateIcons() {
        const headers = this.table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            const icon = header.querySelector('i');
            const column = header.dataset.sort;
            
            if (column === this.currentSort.column) {
                icon.className = this.currentSort.direction === 'asc' 
                    ? 'fas fa-sort-up ml-1' 
                    : 'fas fa-sort-down ml-1';
                icon.classList.remove('opacity-30');
            } else {
                icon.className = 'fas fa-sort ml-1 opacity-30';
            }
        });
    }
    
    getData() {
        return this.data;
    }
}

// 導出
window.TableSorter = TableSorter;
```

## 5.4 使用範例

### 自選股列表

```html
<table id="watchlist-table">
    <thead>
        <tr>
            <th data-sort="symbol">代碼</th>
            <th data-sort="name">名稱</th>
            <th data-sort="price">現價</th>
            <th data-sort="change_pct">漲跌幅</th>
            <th data-sort="volume">成交量</th>
        </tr>
    </thead>
    <tbody id="watchlist-body"></tbody>
</table>

<script>
const watchlistSorter = new TableSorter('watchlist-table', {
    onSort: (sortedData) => {
        renderWatchlistTable(sortedData);
    },
    storageKey: 'watchlist_sort'
});

// 載入數據時
function loadWatchlist(data) {
    watchlistSorter.setData(data);
    renderWatchlistTable(watchlistSorter.getData());
}
</script>
```

### 比較頁面

```html
<table id="compare-table">
    <thead>
        <tr>
            <th>排名</th>
            <th data-sort="symbol">標的</th>
            <th data-sort="price">現價</th>
            <th data-sort="return_1y">1年</th>
            <th data-sort="return_3y">3年</th>
            <th data-sort="return_5y">5年</th>
        </tr>
    </thead>
</table>
```

## 5.5 驗證清單

- [ ] 點擊標題可排序
- [ ] 升降序切換正常
- [ ] 排序偏好被記住
- [ ] 排序圖示正確顯示

---

# 📅 實作順序建議

```
Week 1:
├── Day 1: 功能 2 (BTC 價格) - 簡單，快速見效
├── Day 2: 功能 3 (管理員更新) - 後端為主
└── Day 3: 功能 5 (排序) - 通用模組 + 功能 1 (設定頁面)

Week 2:
├── Day 1-2: 功能 4 後端 (Model + API)
├── Day 3-4: 功能 4 前端 (UI + 整合)
└── Day 5: 測試 + 修復
```

---

# 📁 新增/修改檔案總覽

## 新增檔案

| 檔案 | 說明 |
|------|------|
| `app/models/portfolio.py` | 投資組合資料模型 |
| `app/routers/portfolio.py` | 投資組合 API |
| `app/services/portfolio_service.py` | 投資組合業務邏輯 |
| `static/js/portfolio.js` | 投資組合前端 |
| `static/css/portfolio.css` | 投資組合樣式 |
| `static/js/settings.js` | 設定頁面邏輯 |
| `static/css/settings.css` | 設定頁面樣式 |
| `static/js/table-sort.js` | 通用排序模組 |

## 修改檔案

| 檔案 | 修改內容 |
|------|----------|
| `app/routers/auth.py` | 加入管理員自動更新 |
| `app/routers/__init__.py` | 註冊 portfolio router |
| `app/models/__init__.py` | 匯出新模型 |
| `static/dashboard.html` | 加入 BTC 價格、設定導航、投資組合導航 |
| `static/js/watchlist.js` | 整合排序功能 |
