# 🔧 SELA 開發指南

> 版本: 2.0  
> 最後更新: 2026-01-17  
> 整合自: Bug修復指南、功能整合指南、前端優化報告、Router修改、UI統一指南

---

## 目錄

1. [已知 Bug 與修復](#1-已知-bug-與修復)
2. [前端優化架構](#2-前端優化架構)
3. [市場感知快取](#3-市場感知快取)
4. [圖表功能修復](#4-圖表功能修復)
5. [Router 統一認證](#5-router-統一認證)
6. [UI 統一修復](#6-ui-統一修復)
7. [後端功能擴充](#7-後端功能擴充)
8. [常見開發問題](#8-常見開發問題)

---

## 1. 已知 Bug 與修復

### 1.1 前端 Bug

#### Bug 1: showSection 函數 event 未定義

**問題**: 從非導航處調用 `showSection` 時沒有 event 對象

**修復**:
```javascript
// ❌ 錯誤
function showSection(name) {
    event.target.closest('.nav-link').classList.add('bg-blue-50');
}

// ✅ 正確 - event 改為可選參數
function showSection(name, evt) {
    // ...
    if (evt && evt.target) {
        const navLink = evt.target.closest('.nav-link');
        if (navLink) {
            navLink.classList.add('bg-blue-50', 'text-gray-700');
        }
    }
}
```

**HTML 也需修改**:
```html
<a onclick="showSection('dashboard', event)">
```

#### Bug 2: API 資料格式不符

**問題**: 前端期望 `data.data.stock`，但 API 返回 `data.stock`

**修復**:
```javascript
// ❌ 錯誤
updateSentimentCard('stock', data.data.stock);

// ✅ 正確 - 符合 API 實際返回格式
updateSentimentCard('stock', data.stock);
```

#### Bug 3: 訂閱按鈕沒反應

**問題**: 點擊訂閱/取消訂閱按鈕無反應
**原因**: `onclick` 未正確綁定到全域函數
**修復**: 改用 `window.toggleSubscription` 確保函數可被呼叫
**檔案**: `static/js/subscription.js`

#### Bug 4: 訂閱精選日期顯示錯誤

**問題**: 顯示的是抓取日期而非文章發佈日期
**修復**: 優先使用 `article_date`（文章發佈日），而非 `first_seen_at`
**檔案**: `static/js/subscription.js`

### 1.2 後端 Bug

#### Bug 5: 技術指標欄位名大小寫不一致（重要⚠️）

**問題**: `indicator_service.py` 用小寫，但 `routers` 讀取用大寫

**修復**:
```python
# ❌ 錯誤 (routers/stock.py)
ma20 = float(latest.get('MA20', 0))
rsi_value = float(latest.get('RSI', 50))
macd_dif = float(latest.get('MACD_DIF', 0))

# ✅ 正確 - 使用小寫
ma20 = float(latest.get('ma20', 0)) if 'ma20' in latest else None
rsi_value = float(latest.get('rsi', 50)) if 'rsi' in latest else 50
macd_dif = float(latest.get('macd_dif', 0)) if 'macd_dif' in latest else 0
```

**indicator_service.py 欄位對照**:
| 指標 | 欄位名 |
|------|--------|
| MA | `ma20`, `ma50`, `ma200` |
| RSI | `rsi` |
| MACD | `macd_dif`, `macd_dea`, `macd_hist` |
| KD | `kd_k`, `kd_d` |

#### Bug 6: data_sources 方法名稱錯誤

```python
# ❌ 錯誤
df = yahoo_finance.get_stock_data(symbol)      # 不存在
df = coingecko.get_historical_data(symbol)     # 不存在

# ✅ 正確
df = yahoo_finance.get_stock_history(symbol, period="1y")
df = coingecko.get_ohlc(symbol, days=365)
```

**可用方法參考**:
| 檔案 | 方法 |
|------|------|
| yahoo_finance.py | `get_stock_info()`, `get_stock_history()`, `get_current_price()` |
| coingecko.py | `get_coin_info()`, `get_market_chart()`, `get_ohlc()`, `get_current_price()` |

#### Bug 7: AsyncSession 缺少 await

```python
# ❌ 錯誤
settings = db.execute(stmt).scalar_one_or_none()
db.commit()

# ✅ 正確
result = await db.execute(stmt)
settings = result.scalar_one_or_none()
await db.commit()
```

#### Bug 8: 台股名稱編碼亂碼

**問題**: `TAIWAN_STOCK_NAMES` 字典中文字變亂碼
**位置**: `app/data_sources/yahoo_finance.py` 和 `app/services/price_cache_service.py`
**修復**: 確保檔案以 **UTF-8 without BOM** 編碼儲存

#### Bug 9: BRK.B 等含點號股票搜尋失敗

**修復步驟**:

1. 修改路由定義:
```python
# ❌ 原本
@router.get("/{symbol}", summary="查詢股票")

# ✅ 改為
@router.get("/{symbol:path}", summary="查詢股票")
```

2. 新增變體函數:
```python
def get_symbol_variants(symbol: str) -> list:
    """BRK.B -> ["BRK.B", "BRK-B"]"""
    variants = [symbol]
    if '.' in symbol and not symbol.endswith('.TW'):
        variants.append(symbol.replace('.', '-'))
    if '-' in symbol:
        variants.append(symbol.replace('-', '.'))
    return variants
```

#### Bug 10: 新股 (FIG) 找不到數據

**原因**: 新 IPO 只有 1 年數據，但系統預設要求 10 年

**修復**: 嘗試不同期間
```python
periods = ["10y", "5y", "2y", "1y", "6mo", "3mo"]
for period in periods:
    df = yahoo_finance.get_stock_history(symbol, period=period)
    if df is not None and len(df) >= 20:
        break
```

#### Bug 11: 股票詳情技術指標消失

**問題**: 查詢股票時只返回快取的簡化資料，沒有圖表和完整指標
**原因**: `stock.py` 的快取邏輯錯誤，快取命中時直接返回簡化資料
**修正**: 
- 移除股票詳情查詢的快取返回邏輯
- 永遠從 Yahoo Finance 取得完整資料（含圖表、所有指標）
- 查詢完成後自動更新價格快取（供追蹤清單使用）
**檔案**: `app/routers/stock.py`

#### Bug 12: index_service 模組不存在

```
ModuleNotFoundError: No module named 'app.services.index_service'
```
- 位置: `app/routers/admin.py` 第 967 行
- 影響: `/api/admin/update-indices` API 會報錯
- 建議: 確認是否需要此功能，若不需要可移除相關 import

---

## 2. 前端優化架構

### 2.1 優化層級

| 層級 | 內容 | 檔案 |
|------|------|------|
| P0 | DOM 快取 + 批量更新 | `core.js` |
| P1 | 統一狀態管理 (AppState) | `state.js` |
| P2 | 搜尋模組拆分 + 事件委託 | `search/*.js` |
| P3 | watchlist/portfolio 事件委託 | `watchlist.js`, `portfolio.js` |
| P4 | tags/transaction 優化 | `tags.js`, `transaction.js` |

### 2.2 DOM 快取查詢 (P0)

```javascript
// ❌ 舊寫法 - 每次都查詢 DOM
const el = document.getElementById('userName');

// ✅ 新寫法 - 快取查詢結果
const el = $('userName');

// 強制重新查詢（DOM 結構變化後）
const el = $('userName', true);

// CSS 選擇器快取
const el = $q('.my-class');
```

### 2.3 批量更新 (P0)

```javascript
// ❌ 舊寫法 - 多次觸發重排
document.getElementById('price').textContent = '100';
document.getElementById('price').classList.add('green');
document.getElementById('change').textContent = '+5%';

// ✅ 新寫法 - 一次 requestAnimationFrame 內完成
batchUpdate([
    { id: 'price', prop: 'textContent', value: '100' },
    { id: 'price', classList: { add: ['green'] } },
    { id: 'change', prop: 'textContent', value: '+5%' }
]);
```

### 2.4 狀態管理 (P1)

```javascript
// 讀取狀態
const user = AppState.user;
const watchlist = AppState.watchlist;

// 設置狀態
AppState.set('isLoading', true);
AppState.setWatchlist(list);
AppState.setCurrentStock(stockData);

// 監聽變化
AppState.on('currentStock', (newStock, oldStock) => {
    updateStockUI(newStock);
});
```

**可用狀態**:
| 狀態 | 類型 | 說明 |
|------|------|------|
| `user` | Object | 當前用戶 |
| `isAdmin` | Boolean | 是否管理員 |
| `currentSection` | String | 當前頁面 |
| `currentStock` | Object | 當前股票 |
| `watchlist` | Array | 追蹤清單 |
| `watchlistLoaded` | Boolean | 清單是否已載入 |
| `portfolio` | Object | 持股 {tw, us, summary} |
| `tags` | Array | 標籤列表 |
| `isLoading` | Boolean | 全域載入狀態 |

### 2.5 事件委託 (P2-P4)

```html
<!-- ❌ 舊寫法 - 每個按鈕都有 onclick -->
<button onclick="removeFromWatchlist('AAPL')">刪除</button>

<!-- ✅ 新寫法 - 使用 data-action -->
<button data-action="remove" data-symbol="AAPL">刪除</button>
```

```javascript
// 父容器統一處理
container.addEventListener('click', (e) => {
    const target = e.target.closest('[data-action]');
    if (!target) return;
    
    switch (target.dataset.action) {
        case 'remove':
            removeFromWatchlist(target.dataset.symbol);
            break;
        case 'analyze':
            searchSymbol(target.dataset.symbol);
            break;
    }
});
```

### 2.6 SELA 命名空間

```javascript
SELA.$('userName')           // DOM 快取查詢
SELA.$q('.my-class')         // CSS 選擇器快取
SELA.batchUpdate([...])      // 批量更新
SELA.showToast('訊息')       // Toast 提示
SELA.apiRequest('/api/...')  // API 請求

SELA.search.searchSymbol('AAPL')
SELA.watchlist.load()
SELA.portfolio.loadSummary()
SELA.tags.load()
```

---

## 3. 市場感知快取

### 3.1 概述

**問題**: 原本每次查詢都呼叫 Yahoo Finance API，即使在非交易時間

**解決方案**: 實作智慧快取判斷
- 市場開盤中 → 正常呼叫 API
- 市場已收盤 → 直接使用本地快取

### 3.2 新增函數 (price_cache_service.py)

```python
def get_symbol_market(symbol: str) -> str:
    """判斷股票所屬市場 (tw/us/crypto)"""
    
def is_market_open_for_symbol(symbol: str) -> bool:
    """判斷該股票的市場是否開盤"""
    
def get_cached_price_smart(symbol: str) -> Tuple[dict, bool]:
    """智慧取得快取價格
    Returns: (cache_data, needs_update)
    - 市場關閉 + 有資料 → (data, False) 不需更新
    - 市場開盤 + 資料過期 → (data, True) 需要更新
    """
```

### 3.3 效能提升

| 場景 | 舊版 | 新版 | 提升 |
|-----|------|------|------|
| 非開盤查詢台股 | 1-3 秒 | < 100ms | **10-30x** |
| 非開盤載入追蹤清單 | 500ms-2s | < 50ms | **10-40x** |

---

## 4. 圖表功能修復

### 4.1 時間範圍按鈕無法點擊

**原因**: `chartFullscreen` 模板中的按鈕沒有 `onclick` 事件

**修復**:
```html
<button type="button" onclick="setChartRange(22)" class="chart-range-btn" data-days="22">1M</button>
```

**加上 capture 模式事件監聽**:
```javascript
document.addEventListener('click', function(e) {
    var btn = e.target.closest('.chart-range-btn');
    if (btn) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        var days = parseInt(btn.getAttribute('data-days'));
        setChartRange(days);
    }
}, true);  // true = capture 模式
```

### 4.2 MA 均線不顯示

**原因**: 直接對 `chartData.ma20` 呼叫 `.slice()` 但沒檢查是否存在

**修復**:
```javascript
// 安全切片函數
function safeSlice(arr, start) {
    if (!arr || !Array.isArray(arr)) return [];
    return arr.slice(start);
}

// 檢查是否有有效數據
function hasValid(arr) {
    if (!arr || arr.length === 0) return false;
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] !== null && arr[i] !== undefined && !isNaN(arr[i])) {
            return true;
        }
    }
    return false;
}

// 條件式加入數據集
var datasets = [{ label: '收盤價', data: prices, ... }];
if (hasValid(ma20)) {
    datasets.push({ label: 'MA20', data: ma20, borderColor: '#EF4444', ... });
}
```

### 4.3 圖例無法點擊切換

```javascript
plugins: {
    legend: {
        onClick: function(e, legendItem, legend) {
            var index = legendItem.datasetIndex;
            var ci = legend.chart;
            var meta = ci.getDatasetMeta(index);
            meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;
            ci.update();
        },
        onHover: function(e) {
            e.native.target.style.cursor = 'pointer';
        }
    }
}
```

### 4.4 多個 JS 檔案函數覆蓋

**問題**: `search-chart.js`、`search-render.js`、`chart-fix.js` 都定義相同函數

**修復**: 使用 `Object.defineProperty` 鎖定
```javascript
function install() {
    delete window.setChartRange;
    Object.defineProperty(window, 'setChartRange', {
        value: _setRange,
        writable: false,
        configurable: true
    });
}

// 多次執行確保成功
setTimeout(install, 100);
setTimeout(install, 500);
setTimeout(install, 1000);
```

**確保修復腳本最後載入**:
```html
<script src="/static/js/search.js"></script>
<!-- 修復腳本必須放最後 -->
<script src="/static/js/chart-fix-final.js"></script>
```

---

## 5. Router 統一認證

### 5.1 問題

多個 router 檔案重複定義 `get_current_user`、`get_current_admin` 等認證函數，導致維護困難。

### 5.2 解決方案

建立統一的 `app/dependencies.py`：

```python
# app/dependencies.py
from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.services.auth_service import AuthService
from app.models.user import User

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """依賴注入：取得當前用戶"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供認證 Token")
    
    token = auth_header.split(" ")[1]
    auth_service = AuthService(db)
    user = await auth_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="無效的 Token")
    
    return user

async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User | None:
    """可選的用戶認證"""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None

async def get_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    """必須是管理員"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理員權限")
    return user
```

### 5.3 各 Router 修改

**刪除重複的認證函數，改為 import**:

```python
# ❌ 刪除這整段
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> User:
    ...

# ✅ 加入這行
from app.dependencies import get_current_user, get_admin_user, get_optional_user
```

### 5.4 需要修改的檔案

| 檔案 | 需要的函數 |
|------|-----------|
| subscription.py | `get_current_user`, `get_admin_user` |
| portfolio.py | `get_current_user` |
| compare.py | `get_current_user`, `get_optional_user` |
| watchlist.py | `get_current_user` |
| market.py | `get_optional_user`, `get_admin_user` |
| admin.py | `get_admin_user` |

### 5.5 快速搜尋指令

```bash
# 找出所有定義 get_current_user 的檔案
grep -rn "async def get_current_user" app/routers/

# 找出所有定義 get_current_admin 的檔案  
grep -rn "async def get_current_admin" app/routers/
```

---

## 6. UI 統一修復

### 6.1 問題

點選「報酬率比較」、「後台管理」時會跳轉到獨立頁面，失去導航列。

### 6.2 目標

統一 UI 體驗，所有功能都在 dashboard.html 內以 section 方式切換。

### 6.3 側邊欄導航連結修改

**電腦版側邊欄**:
```html
<!-- 修改前 -->
<a href="/static/compare.html" class="nav-link ...">
    <i class="fas fa-trophy mr-3"></i>
    <span>報酬率比較</span>
</a>

<!-- 修改後 -->
<a href="#" onclick="showSection('cagr', event)" class="nav-link ..." data-section="cagr">
    <i class="fas fa-trophy mr-3"></i>
    <span>報酬率比較</span>
</a>
```

**管理後台連結**:
```html
<!-- 修改前 -->
<a id="adminSidebarLink" href="/static/admin.html" class="hidden ...">

<!-- 修改後 -->
<a id="adminSidebarLink" href="#" onclick="showSection('admin', event)" class="hidden nav-link ..." data-section="admin">
```

### 6.4 新增 Section HTML

在 `</main>` 之前新增：

```html
<!-- ===== 報酬率比較區塊 ===== -->
<section id="section-cagr" class="section hidden">
    <h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">
        <i class="fas fa-trophy text-yellow-500 mr-2"></i>
        報酬率比較
    </h2>
    <!-- 內容略 -->
</section>

<!-- ===== 管理後台區塊 ===== -->
<section id="section-admin" class="section hidden">
    <h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">
        <i class="fas fa-user-shield text-orange-500 mr-2"></i>
        管理後台
    </h2>
    <!-- 內容略 -->
</section>
```

### 6.5 更新 showSection 函數

```javascript
function showSection(name, evt) {
    if (evt) evt.preventDefault();
    
    // 隱藏所有 section
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    
    // 顯示目標 section
    const target = document.getElementById(`section-${name}`);
    if (target) {
        target.classList.remove('hidden');
    }
    
    // 更新導航狀態
    document.querySelectorAll('.nav-link, .mobile-nav-link, .bottom-nav-item').forEach(link => {
        link.classList.remove('bg-blue-50', 'text-gray-700', 'active');
        if (link.dataset.section === name) {
            link.classList.add('bg-blue-50', 'text-gray-700');
        }
    });
    
    // 載入特定 section 的資料
    switch(name) {
        case 'watchlist':
            loadWatchlist();
            break;
        case 'portfolio':
            loadPortfolioData();
            break;
        case 'admin':
            loadAdminStats();
            break;
        case 'cagr':
            // 初始化報酬率比較
            break;
    }
    
    // 關閉手機選單
    closeMobileSidebar();
}
```

---

## 7. 後端功能擴充

### 7.1 chart_data 增加 volumes

修改 `app/routers/stock.py` 的 `get_stock_analysis` 函數：

```python
"chart_data": {
    "dates": [str(d) for d in df['date'].tail(1500).tolist()],
    "prices": [float(p) for p in df['close'].tail(1500).tolist()],
    "volumes": [int(v) if not pd.isna(v) else 0 for v in df['volume'].tail(1500).tolist()] if 'volume' in df.columns else [],  # 🆕
    "ma20": [...],
    "ma50": [...],
    "ma200": [...],
    "ma250": [...],
},
```

### 7.2 MA 進階分析

新增函數計算均線距離和交叉訊號：

```python
def analyze_ma_advanced(df, current_price):
    """計算 MA 進階分析"""
    result = {}
    
    # 距離均線百分比
    if 'ma20' in df.columns and not pd.isna(df['ma20'].iloc[-1]):
        ma20 = df['ma20'].iloc[-1]
        result['dist_ma20'] = round((current_price - ma20) / ma20 * 100, 2)
    
    # 黃金交叉/死亡交叉偵測 (最近 30 天內)
    if 'ma20' in df.columns and 'ma50' in df.columns:
        for i in range(min(30, len(df) - 1), 0, -1):
            idx = -i
            prev_idx = idx - 1
            
            # 黃金交叉: MA20 由下往上穿越 MA50
            if df['ma20'].iloc[prev_idx] < df['ma50'].iloc[prev_idx] and df['ma20'].iloc[idx] >= df['ma50'].iloc[idx]:
                result['golden_cross_20_50'] = True
                result['golden_cross_20_50_days'] = i
                break
            
            # 死亡交叉
            if df['ma20'].iloc[prev_idx] > df['ma50'].iloc[prev_idx] and df['ma20'].iloc[idx] <= df['ma50'].iloc[idx]:
                result['death_cross_20_50'] = True
                result['death_cross_20_50_days'] = i
                break
    
    return result
```

### 7.3 熱門追蹤 API

新增 `app/routers/watchlist.py`：

```python
@router.get("/popular", summary="取得熱門追蹤股票")
async def get_popular_stocks(
    limit: int = Query(10, ge=1, le=50, description="返回數量"),
    db: Session = Depends(get_db)
):
    from sqlalchemy import func
    
    popular = db.query(
        Watchlist.symbol,
        func.count(Watchlist.user_id).label('count')
    ).group_by(Watchlist.symbol).order_by(func.count(Watchlist.user_id).desc()).limit(limit).all()
    
    result = [{"symbol": row.symbol, "count": row.count} for row in popular]
    
    return {"success": True, "data": result}
```

---

## 8. 常見開發問題

### 8.1 Railway 無法直接執行 SQL

所有資料庫遷移必須透過 `database.py` 的 `run_migrations()` 函數自動執行。

```python
# database.py
def run_migrations():
    """自動執行遷移"""
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE stock_price_cache 
            ADD COLUMN IF NOT EXISTS ma20 NUMERIC(12, 4)
        """))
        conn.commit()
```

### 8.2 LINE Login 多環境部署

需在 LINE Developers Console 添加每個環境的 Callback URL（換行分隔）:
```
https://production.railway.app/auth/line/callback
https://staging.railway.app/auth/line/callback
http://localhost:8000/auth/line/callback
```

### 8.3 瀏覽器快取問題

前端修改後用戶可能看到舊版本:
- 按 `Ctrl + Shift + R` 強制重新整理
- 開啟無痕視窗測試
- 在檔案名加上版本號：`dashboard.html?v=1.0.1`

### 8.4 除錯技巧

```javascript
// 善用 console.log 加上前綴
console.log('📊 [FINAL] _render days=' + days);

// 檢查數據是否正確傳遞
console.log(window.currentChartData);

// 開啟 Debug 模式
window.SELA_DEBUG = true;
```

### 8.5 快速檢查清單

- [ ] `indicator_service` 欄位名是小寫
- [ ] `routers` 讀取欄位名也用小寫
- [ ] API 方法名與 data_sources 一致
- [ ] 前端資料格式與 API 返回一致
- [ ] `showSection` 等函數的 event 參數可選
- [ ] AsyncSession 的操作都有 await
- [ ] 檔案以 UTF-8 without BOM 儲存
