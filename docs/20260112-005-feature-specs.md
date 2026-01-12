# 🚀 SELA 系統功能規劃書

> 文件編號: 20260112-005-feature-specs  
> 建立日期: 2026-01-12  
> 版本: 1.0

---

## 📋 功能總覽

| # | 功能名稱 | 優先級 | 複雜度 | 預估工時 |
|---|---------|--------|--------|---------|
| 1 | 管理員登入自動更新 | P1 | 低 | 2h |
| 2 | 個人買賣股票管理 | P0 | 高 | 8h |
| 3 | 儀表板比特幣價格 | P2 | 低 | 1h |
| 4 | 列表清單排序 | P1 | 中 | 3h |

---

# 功能 1: 管理員登入自動更新

## 1.1 需求描述

管理員登入後，自動在背景觸發系統更新。

## 1.2 觸發時機

- 管理員成功登入時（`is_admin=True`）
- 僅觸發一次，不阻塞登入流程

## 1.3 更新項目

```python
AUTO_UPDATE_TASKS = [
    "update_stock_prices",      # 更新股票價格快取
    "update_crypto_prices",     # 更新加密貨幣價格
    "update_market_sentiment",  # 更新恐懼貪婪指數
    "cleanup_old_data",         # 清理過期數據
]
```

## 1.4 技術設計

### 後端修改

**檔案:** `app/routers/auth.py`

```python
# 在 LINE callback 處理成功登入後加入

@router.get("/callback")
async def line_callback(...):
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

## 1.5 前端提示（可選）

登入後在儀表板顯示 Toast 提示：
```
🔄 系統正在背景更新數據...
```

---

# 功能 2: 個人買賣股票管理

## 2.1 需求描述

用戶可記錄個人股票買賣交易，追蹤持股和損益。

## 2.2 資料庫設計

### 新增資料表

**檔案:** `app/models/portfolio.py`

```python
"""
個人投資組合模型
"""
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, Index, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MarketType(enum.Enum):
    """市場類型"""
    TW = "tw"      # 台股
    US = "us"      # 美股


class TransactionType(enum.Enum):
    """交易類型"""
    BUY = "buy"    # 買入
    SELL = "sell"  # 賣出


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
    """持股彙總（計算用，可由交易紀錄推導）"""
    
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
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "total_shares": self.total_shares,
            "avg_cost": float(self.avg_cost),
            "total_invested": float(self.total_invested),
            "realized_profit": float(self.realized_profit),
        }
```

## 2.3 API 設計

**檔案:** `app/routers/portfolio.py`

### 端點列表

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/api/portfolio/transactions` | 取得交易紀錄 |
| POST | `/api/portfolio/transactions` | 新增交易 |
| PUT | `/api/portfolio/transactions/{id}` | 修改交易 |
| DELETE | `/api/portfolio/transactions/{id}` | 刪除交易 |
| GET | `/api/portfolio/holdings` | 取得持股總覽 |
| GET | `/api/portfolio/holdings/{market}` | 取得特定市場持股 |
| GET | `/api/portfolio/summary` | 取得投資摘要 |

### 請求/回應格式

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

# GET /api/portfolio/holdings
class HoldingsResponse(BaseModel):
    success: bool
    data: dict  # { "tw": [...], "us": [...] }
    summary: dict  # { "total_value", "total_profit", ... }

# GET /api/portfolio/summary
class SummaryResponse(BaseModel):
    success: bool
    data: {
        "total_invested": float,     # 總投入
        "current_value": float,      # 現值
        "unrealized_profit": float,  # 未實現損益
        "realized_profit": float,    # 已實現損益
        "total_profit": float,       # 總損益
        "return_rate": float,        # 報酬率 %
        "tw_count": int,             # 台股持股數
        "us_count": int,             # 美股持股數
    }
```

## 2.4 前端設計

### 頁面結構

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

### 新增交易表單

```html
<form id="transaction-form">
    <!-- 市場選擇 -->
    <select name="market">
        <option value="tw">台股</option>
        <option value="us">美股</option>
    </select>
    
    <!-- 股票代碼（可搜尋） -->
    <input type="text" name="symbol" placeholder="股票代碼">
    
    <!-- 交易類型 -->
    <select name="transaction_type">
        <option value="buy">買入</option>
        <option value="sell">賣出</option>
    </select>
    
    <!-- 數量、價格、日期 -->
    <input type="number" name="quantity" placeholder="股數">
    <input type="number" name="price" step="0.01" placeholder="成交價">
    <input type="date" name="transaction_date">
    
    <!-- 手續費（可選） -->
    <input type="number" name="fee" step="0.01" placeholder="手續費">
    
    <!-- 備註 -->
    <textarea name="note" placeholder="備註"></textarea>
</form>
```

## 2.5 導航整合

在 `dashboard.html` 側邊欄新增：

```html
<a onclick="showSection('portfolio', event)" class="nav-link">
    <i class="fas fa-briefcase mr-2"></i>投資組合
</a>
```

---

# 功能 3: 儀表板比特幣價格

## 3.1 需求描述

在儀表板首頁顯示比特幣即時價格。

## 3.2 顯示內容

- 當前價格 (USD)
- 24 小時漲跌幅
- 漲跌顏色標示（綠漲紅跌）

## 3.3 技術設計

### 後端

已有 API：`GET /api/crypto/BTC`

### 前端

**檔案:** `static/dashboard.html`

在儀表板區塊加入：

```html
<!-- 比特幣價格卡片 -->
<div id="btc-price-card" class="bg-gradient-to-br from-orange-500 to-yellow-500 rounded-xl p-4 text-white">
    <div class="flex items-center justify-between">
        <div>
            <div class="text-sm opacity-80">Bitcoin</div>
            <div class="text-2xl font-bold" id="btc-price">$--,---</div>
        </div>
        <div class="text-right">
            <div class="text-lg font-semibold" id="btc-change">--%</div>
            <div class="text-xs opacity-80">24h</div>
        </div>
        <i class="fab fa-bitcoin text-4xl opacity-50"></i>
    </div>
</div>
```

**JavaScript:**

```javascript
async function loadBtcPrice() {
    try {
        const res = await fetch(`${API_BASE}/api/crypto/BTC`);
        const data = await res.json();
        
        if (data.success) {
            const price = data.data.current_price;
            const change = data.data.change_24h;
            
            document.getElementById('btc-price').textContent = 
                `$${price.toLocaleString('en-US', {minimumFractionDigits: 0})}`;
            
            const changeEl = document.getElementById('btc-change');
            changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
            changeEl.classList.add(change >= 0 ? 'text-green-200' : 'text-red-200');
        }
    } catch (e) {
        console.error('載入 BTC 價格失敗:', e);
    }
}

// 頁面載入時執行
document.addEventListener('DOMContentLoaded', loadBtcPrice);
```

---

# 功能 4: 列表清單排序

## 4.1 需求描述

各種列表支援點擊欄位標題排序。

## 4.2 適用頁面

1. 自選股列表（`watchlist`）
2. 比較頁面（`compare`）
3. 投資組合（`portfolio`）- 新功能

## 4.3 技術設計

### 通用排序模組

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

### 使用範例

**自選股列表:**

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

**比較頁面:**

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

---

# 📁 檔案清單

## 新增檔案

| 檔案 | 說明 |
|------|------|
| `app/models/portfolio.py` | 投資組合資料模型 |
| `app/routers/portfolio.py` | 投資組合 API |
| `app/services/portfolio_service.py` | 投資組合業務邏輯 |
| `static/js/portfolio.js` | 投資組合前端 |
| `static/css/portfolio.css` | 投資組合樣式 |
| `static/js/table-sort.js` | 通用排序模組 |

## 修改檔案

| 檔案 | 修改內容 |
|------|----------|
| `app/routers/auth.py` | 加入管理員自動更新 |
| `app/routers/__init__.py` | 註冊 portfolio router |
| `app/models/__init__.py` | 匯出新模型 |
| `static/dashboard.html` | 加入 BTC 價格、投資組合導航 |
| `static/js/watchlist.js` | 整合排序功能 |
| `static/compare.html` | 整合排序功能 |

---

# 📅 實作順序建議

```
Week 1:
├── Day 1: 功能 3 (BTC 價格) - 簡單，快速見效
├── Day 2: 功能 1 (管理員更新) - 後端為主
└── Day 3: 功能 4 (排序) - 通用模組

Week 2:
├── Day 1-2: 功能 2 後端 (Model + API)
├── Day 3-4: 功能 2 前端 (UI + 整合)
└── Day 5: 測試 + 修復
```

---

# ✅ 驗收標準

## 功能 1: 管理員登入自動更新
- [ ] 管理員登入後自動觸發更新
- [ ] 更新在背景執行，不影響登入
- [ ] 更新日誌正確記錄

## 功能 2: 個人買賣股票管理
- [ ] 可新增/編輯/刪除交易紀錄
- [ ] 台股/美股分開顯示
- [ ] 持股和損益計算正確
- [ ] 手機版顯示正常

## 功能 3: 儀表板比特幣價格
- [ ] 首頁顯示 BTC 價格
- [ ] 漲跌顏色正確
- [ ] 價格格式化正確

## 功能 4: 列表清單排序
- [ ] 點擊標題可排序
- [ ] 升降序切換正常
- [ ] 排序偏好被記住
- [ ] 排序圖示正確顯示
