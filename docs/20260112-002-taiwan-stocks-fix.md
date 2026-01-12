# 🔧 台股名稱編碼修復說明

> 文件編號: 20260112-002  
> 更新日期: 2026-01-12  
> 類型: Bug 修復

---

## 🐛 問題描述

比較頁面的台股名稱顯示亂碼：

| 代碼 | 錯誤顯示 | 正確名稱 |
|------|----------|---------|
| 2330.TW | å°ç©é›» | 台積電 |
| 2317.TW | é´»æµ· | 鴻海 |
| 2454.TW | è¯ç™¼ç§' | 聯發科 |
| 3711.TW | æ—¥æœˆå…‰... | 日月光投控 |
| 2308.TW | å°é"é›» | 台達電 |

**原因：** Yahoo Finance API 返回的台股名稱有 UTF-8 編碼問題

---

## 📁 修復檔案

| 檔案 | 位置 | 說明 |
|------|------|------|
| `taiwan_stocks.py` | `app/data_sources/` | 台股名稱字典（200+ 支股票） |

---

## 🚀 修復步驟

### 1. 複製新模組

```bash
cp app/data_sources/taiwan_stocks.py /你的專案/app/data_sources/
```

### 2. 修改 compare_service.py

#### 在開頭加入導入：

```python
from app.data_sources.taiwan_stocks import (
    TAIWAN_STOCK_NAMES, 
    get_taiwan_stock_name, 
    is_taiwan_stock
)
```

#### 修改 `_fetch_price_data` 方法：

找到返回 `info_dict` 的地方，將：

```python
if info:
    info_dict = {
        "name": info.get("name", symbol),
        ...
    }
```

替換為：

```python
# 優先使用本地台股名稱
name = symbol
if is_taiwan_stock(symbol):
    stock_code = symbol.replace('.TW', '').replace('.TWO', '')
    name = TAIWAN_STOCK_NAMES.get(stock_code, symbol)
elif info:
    name = info.get("name", symbol)

if info:
    info_dict = {
        "name": name,  # 使用修復後的名稱
        ...
    }
```

### 3. 重新部署

---

## ✅ 驗證

1. 開啟比較頁面
2. 選擇「台灣科技股」預設
3. 確認名稱正確顯示：
   - 2330.TW → 台積電
   - 2317.TW → 鴻海
   - 2454.TW → 聯發科

---

## 📝 新增股票

如需新增其他台股，編輯 `taiwan_stocks.py`：

```python
TAIWAN_STOCK_NAMES = {
    # 現有股票...
    "1234": "新股票名稱",
}
```

---

## 🔄 替代方案（前端修復）

如不想改後端，可在 `compare.html` 加入：

```javascript
const TW_STOCK_NAMES = {
    "2330": "台積電",
    "2317": "鴻海",
    // ...
};

function fixStockName(symbol, originalName) {
    if (symbol.endsWith('.TW') || symbol.endsWith('.TWO')) {
        const code = symbol.replace('.TW', '').replace('.TWO', '');
        return TW_STOCK_NAMES[code] || originalName;
    }
    return originalName;
}
```
