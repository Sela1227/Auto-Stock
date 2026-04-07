# 📊 SELA MA 強化分析開發記錄

> 日期: 2026-01-17  
> 版本: 1.0  
> 狀態: 待部署

---

## 📋 功能概述

### 新增功能

| 功能 | 說明 | 狀態 |
|------|------|------|
| **距離均線百分比** | dist_ma20/50/200/250 | ✅ 完成 |
| **黃金/死亡交叉偵測** | 支援 MA20/50、MA50/200、MA20/200 | ✅ 完成 |
| **交叉發生天數** | golden_cross_xx_days | ✅ 完成 |
| **均線排列分析** | 多頭/空頭/盤整 + 強度評分 | ✅ 完成 |
| **支撐/壓力位判斷** | 最近支撐/壓力 + 完整列表 | ✅ 完成 |
| **前端渲染模組** | search-ma-advanced.js | ✅ 完成 |

---

## 📦 交付檔案

### 1. 後端服務 (app/services/ma_advanced_service.py)

```
位置: app/services/ma_advanced_service.py
功能: MA 進階分析計算
主函數: analyze_ma_advanced(df, current_price, lookback_days=30)
```

### 2. 前端模組 (static/js/search-ma-advanced.js)

```
位置: static/js/search-ma-advanced.js
功能: MA 進階分析 UI 渲染
主函數: 
  - renderMAAdvanced(ma) - 完整渲染
  - getMAAdvancedSummary(ma) - 摘要文字
```

### 3. 整合補丁說明 (stock_py_integration_patch.py)

```
位置: 參考文件，不需部署
功能: 說明如何整合到 stock.py
```

---

## 🔧 部署步驟

### 步驟 1: 部署後端服務

```bash
# 複製 ma_advanced_service.py 到後端
cp ma_advanced_service.py app/services/ma_advanced_service.py
```

### 步驟 2: 修改 stock.py

在 `app/routers/stock.py` 中：

**A. 新增 import (檔案頂部)**
```python
from app.services.ma_advanced_service import analyze_ma_advanced
```

**B. 修改 get_stock_analysis 函數**

找到 indicators 建構的位置，將：

```python
"indicators": {
    "ma": {
        "ma20": ma20, "ma50": ma50, "ma200": ma200,
        "alignment": alignment,
        ...
    },
```

改為：

```python
# 計算 MA 進階分析
ma_advanced = analyze_ma_advanced(df, current_price)

# 建構基本 MA 指標
ma_indicators = {
    "ma20": ma20, "ma50": ma50, "ma200": ma200,
    "alignment": alignment,
    "price_vs_ma20": "above" if ma20 and current_price > ma20 else "below" if ma20 else None,
    "price_vs_ma50": "above" if ma50 and current_price > ma50 else "below" if ma50 else None,
    "price_vs_ma200": "above" if ma200 and current_price > ma200 else "below" if ma200 else None,
}

# 合併進階分析
ma_indicators.update(ma_advanced)

# 在 return 中使用
"indicators": {
    "ma": ma_indicators,
    ...
},
```

### 步驟 3: 部署前端模組

```bash
# 複製前端模組
cp search-ma-advanced.js static/js/search-ma-advanced.js
```

### 步驟 4: 在 dashboard.html 引入

在 `</body>` 之前加入：

```html
<script src="/static/js/search-ma-advanced.js"></script>
```

### 步驟 5: 整合到搜尋結果顯示

在 `search-render.js` 或相關檔案中，找到顯示技術指標的位置，加入：

```javascript
// 在 MA 指標區塊加入進階分析
if (data.indicators && data.indicators.ma) {
    const maAdvancedHtml = renderMAAdvanced(data.indicators.ma);
    // 插入到適當位置
    document.getElementById('maAdvancedContainer').innerHTML = maAdvancedHtml;
}
```

---

## 📊 API 回傳結構

### indicators.ma 新增欄位

```json
{
  "ma": {
    // 基本欄位（原有）
    "ma20": 150.5,
    "ma50": 148.0,
    "ma200": 140.0,
    "alignment": "多頭排列",
    "price_vs_ma20": "above",
    "price_vs_ma50": "above",
    "price_vs_ma200": "above",
    
    // 🆕 距離百分比
    "dist_ma20": 2.5,
    "dist_ma50": 4.2,
    "dist_ma200": 10.3,
    
    // 🆕 交叉偵測 - MA20/MA50
    "golden_cross_20_50": true,
    "golden_cross_20_50_days": 5,
    "death_cross_20_50": false,
    "death_cross_20_50_days": null,
    
    // 🆕 交叉偵測 - MA50/MA200
    "golden_cross_50_200": false,
    "golden_cross_50_200_days": null,
    "death_cross_50_200": false,
    "death_cross_50_200_days": null,
    
    // 🆕 交叉偵測 - MA20/MA200
    "golden_cross_20_200": false,
    "golden_cross_20_200_days": null,
    "death_cross_20_200": false,
    "death_cross_20_200_days": null,
    
    // 🆕 排列分析
    "alignment_status": "bullish",
    "alignment_detail": "完美多頭排列",
    "alignment_score": 4,
    
    // 🆕 支撐/壓力
    "nearest_support": {
      "ma": "MA20",
      "price": 150.5,
      "distance_pct": -2.3
    },
    "nearest_resistance": null,
    "support_levels": [
      {"ma": "MA20", "price": 150.5, "distance_pct": 2.3},
      {"ma": "MA50", "price": 148.0, "distance_pct": 4.2}
    ],
    "resistance_levels": []
  }
}
```

---

## 🧪 測試驗證

### 1. 後端測試

```python
# 在 Python shell 中測試
from app.services.ma_advanced_service import analyze_ma_advanced
import pandas as pd
import numpy as np

# 建立測試數據
dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
prices = 100 + np.cumsum(np.random.randn(100) * 2)

df = pd.DataFrame({'date': dates, 'close': prices})
df['ma20'] = df['close'].rolling(20).mean()
df['ma50'] = df['close'].rolling(50).mean()
df['ma200'] = df['close'].rolling(100).mean()  # 用 100 代替 200

result = analyze_ma_advanced(df, df['close'].iloc[-1])
print(result)
```

### 2. API 測試

```bash
# 查詢股票，確認回傳包含新欄位
curl -X GET "https://your-domain/api/stock/AAPL" | jq '.indicators.ma'
```

### 3. 前端測試

```javascript
// 在瀏覽器 console 測試
const testMa = {
    dist_ma20: 2.5,
    dist_ma50: 4.2,
    dist_ma200: 10.3,
    golden_cross_20_50: true,
    golden_cross_20_50_days: 5,
    alignment_status: 'bullish',
    alignment_detail: '完美多頭排列',
    alignment_score: 4,
    nearest_support: { ma: 'MA20', price: 150.5, distance_pct: -2.3 },
};

console.log(renderMAAdvanced(testMa));
```

---

## 📝 注意事項

1. **資料依賴**: 需要 df 包含 ma20, ma50, ma200 欄位才能計算
2. **回溯天數**: 預設 30 天，可調整 `lookback_days` 參數
3. **效能**: 分析計算輕量，不會顯著影響回應時間
4. **相容性**: 與現有前端程式碼相容，新欄位為可選

---

## 📋 待辦追蹤更新

完成此功能後，更新 Memory：

> SELA 待辦: P1: ~~(1)MA強化分析~~ ✅ (2)追蹤清單載入效能診斷 P2: (3)訂閱排程驗證 (4)前端效能優化
