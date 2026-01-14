# SELA 選股系統 - Bug 修復記錄

> 版本：v0.3.0  
> 更新日期：2026-01-05

---

## 目錄

1. [前端 Bug](#前端-bug)
2. [後端 Bug](#後端-bug)
3. [Async/Await 問題](#asyncawait-問題)
4. [部署注意事項](#部署注意事項)

---

## 前端 Bug

### Bug 1：showSection 函數 event 未定義

**錯誤訊息**：
```
Uncaught TypeError: Cannot read properties of null (reading 'classList')
    at showSection (dashboard.html:277:46)
    at searchSymbol (dashboard.html:411:13)
```

**原因**：
- `showSection` 函數使用了全域 `event` 對象
- 從導航列點擊時有 `event`，但從 `searchSymbol` 等函數調用時沒有

**錯誤代碼**：
```javascript
function showSection(name) {
    // ...
    event.target.closest('.nav-link').classList.add('bg-blue-50');  // ❌ event 未定義
}
```

**修復代碼**：
```javascript
function showSection(name, evt) {
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    const section = document.getElementById(`section-${name}`);
    if (section) {
        section.classList.remove('hidden');
    }
    
    document.querySelectorAll('.nav-link').forEach(l => {
        l.classList.remove('bg-blue-50', 'text-gray-700');
        l.classList.add('text-gray-600');
    });
    
    // ✅ 只有點擊導航時才更新高亮
    if (evt && evt.target) {
        const navLink = evt.target.closest('.nav-link');
        if (navLink) {
            navLink.classList.add('bg-blue-50', 'text-gray-700');
            navLink.classList.remove('text-gray-600');
        }
    }
    // ...
}
```

**HTML 調用也要修改**：
```html
<!-- ❌ 錯誤 -->
<a onclick="showSection('dashboard')">

<!-- ✅ 正確 -->
<a onclick="showSection('dashboard', event)">
```

---

### Bug 2：API 資料格式不符

**錯誤訊息**：
```
TypeError: Cannot read properties of undefined (reading 'stock')
    at loadSentiment (dashboard.html:299:60)
```

**原因**：
- 前端期望 `data.data.stock` 格式
- 後端 API 實際返回 `data.stock` 格式

**錯誤代碼**：
```javascript
// ❌ 前端期望
updateSentimentCard('stock', data.data.stock);
updateSentimentCard('crypto', data.data.crypto);
```

**修復代碼**：
```javascript
// ✅ 符合 API 實際返回格式
updateSentimentCard('stock', data.stock);
updateSentimentCard('crypto', data.crypto);
```

**API 實際返回格式**：
```json
{
  "success": true,
  "stock": { "value": 45, "classification": "neutral" },
  "crypto": { "value": 32, "classification": "fear" }
}
```

---

### Bug 3：搜尋結果資料格式

**原因**：
- 前端期望 `data.data` 包含股票資料
- 後端直接返回資料在頂層

**錯誤代碼**：
```javascript
// ❌ 錯誤
renderStockResult(data.data, isCrypto);
```

**修復代碼**：
```javascript
// ✅ 正確 - 資料直接在頂層
renderStockResult(data, isCrypto);
```

---

## 後端 Bug

### Bug 4：技術指標欄位名大小寫不一致

**原因**：
- `indicator_service.py` 產生小寫欄位名：`ma20`, `rsi`, `macd_dif`
- `stock.py` / `crypto.py` 讀取大寫欄位名：`MA20`, `RSI`, `MACD_DIF`

**錯誤代碼**：
```python
# ❌ routers/stock.py 使用大寫
ma20 = float(latest.get('MA20', 0)) if 'MA20' in latest else None
rsi_value = float(latest.get('RSI', 50)) if 'RSI' in latest else 50
macd_dif = float(latest.get('MACD_DIF', 0)) if 'MACD_DIF' in latest else 0
```

**修復代碼**：
```python
# ✅ 使用小寫，符合 indicator_service 產生的欄位名
ma20 = float(latest.get('ma20', 0)) if 'ma20' in latest else None
ma50 = float(latest.get('ma50', 0)) if 'ma50' in latest else None
ma200 = float(latest.get('ma200', 0)) if 'ma200' in latest else None
rsi_value = float(latest.get('rsi', 50)) if 'rsi' in latest else 50
macd_dif = float(latest.get('macd_dif', 0)) if 'macd_dif' in latest else 0
macd_dea = float(latest.get('macd_dea', 0)) if 'macd_dea' in latest else 0
macd_hist = float(latest.get('macd_hist', 0)) if 'macd_hist' in latest else 0
```

**indicator_service.py 產生的欄位名參考**：
```python
df[f"ma{self.ma_short}"]  # ma20
df[f"ma{self.ma_mid}"]    # ma50
df[f"ma{self.ma_long}"]   # ma200
df["rsi"]                  # rsi
df["macd_dif"]            # macd_dif
df["macd_dea"]            # macd_dea
df["macd_hist"]           # macd_hist
df["kd_k"]                # kd_k
df["kd_d"]                # kd_d
```

---

### Bug 5：方法名稱錯誤

**原因**：調用不存在的方法名

**錯誤代碼**：
```python
# ❌ routers/stock.py
df = yahoo_finance.get_stock_data(symbol, period="1y")  # 方法不存在

# ❌ routers/crypto.py
df = coingecko.get_historical_data(symbol, days=365)  # 方法不存在
```

**修復代碼**：
```python
# ✅ routers/stock.py - 使用正確的方法名
df = yahoo_finance.get_stock_history(symbol, period="1y")

# ✅ routers/crypto.py - 使用正確的方法名
df = coingecko.get_ohlc(symbol, days=365)
```

**data_sources 可用方法參考**：

| 檔案 | 可用方法 |
|------|----------|
| yahoo_finance.py | `get_stock_info()`, `get_stock_history()`, `get_current_price()` |
| coingecko.py | `get_coin_info()`, `get_market_chart()`, `get_ohlc()`, `get_current_price()`, `validate_symbol()` |

---

## Async/Await 問題

### Bug 6：Settings API 缺少 await

**錯誤訊息**：
```
'coroutine' object has no attribute 'scalar_one_or_none'
```

**原因**：
- 使用 `AsyncSession` 但沒有 `await` 資料庫操作

**錯誤代碼**：
```python
# ❌ 缺少 await
settings = db.execute(stmt).scalar_one_or_none()
db.commit()
db.refresh(settings)
```

**修復代碼**：
```python
# ✅ 加上 await
result = await db.execute(stmt)
settings = result.scalar_one_or_none()
await db.commit()
await db.refresh(settings)
```

---

## 部署注意事項

### 1. 瀏覽器快取問題

修改前端檔案後，用戶可能看到舊版本。

**解決方法**：
- 按 `Ctrl + Shift + R` 強制重新整理
- 開啟無痕視窗測試
- 在檔案名加上版本號：`dashboard.html?v=1.0.1`

### 2. Railway 部署檢查

部署後檢查 log 確認：
- 容器啟動成功
- API 端點返回 200 OK
- 沒有 500 錯誤

### 3. API 測試方法

直接在瀏覽器測試 API：
```
https://your-domain.railway.app/api/stock/AAPL
https://your-domain.railway.app/api/crypto/BTC
https://your-domain.railway.app/api/market/sentiment
```

### 4. 前端 Console 調試

按 `F12` 開啟開發者工具，查看：
- Console 錯誤訊息
- Network 請求狀態
- API 回應內容

---

## 修復檔案清單

| 檔案 | 修復內容 |
|------|----------|
| `static/dashboard.html` | showSection 參數、API 資料格式 |
| `app/routers/stock.py` | 方法名、欄位名大小寫 |
| `app/routers/crypto.py` | 方法名、欄位名大小寫 |
| `app/routers/settings.py` | async/await 完整版 |

---

## 快速檢查清單

- [ ] `indicator_service` 欄位名是小寫
- [ ] `routers` 讀取欄位名也用小寫
- [ ] API 方法名與 data_sources 一致
- [ ] 前端資料格式與 API 返回一致
- [ ] `showSection` 等函數的 event 參數可選
- [ ] AsyncSession 的操作都有 await

---

> 文件維護：每次修復 bug 後更新此文件
