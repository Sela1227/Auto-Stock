# 🔧 台股名稱編碼修復

> 文件編號: 20260112-002  
> 更新日期: 2026-01-12  
> 類型: Bug 修復  
> 優先級: 高

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

**根本原因：** Yahoo Finance API 返回的台股名稱有 UTF-8 編碼問題，而 `compare_service.py` 直接使用了這個有問題的名稱。

**問題代碼位置：** `app/services/compare_service.py` 第 7531 行

```python
info_dict = {
    "name": info.get("name", symbol),  # ⚠️ 這裡直接用 info，會有亂碼
    ...
}
```

---

## 📁 修復檔案

| 檔案 | 位置 | 說明 |
|------|------|------|
| `taiwan_stocks.py` | `app/data_sources/` | 台股名稱字典（200+ 股票）|
| `compare_service_patch.py` | `app/services/` | compare_service.py 修改說明 |

---

## 🚀 修復步驟

### 步驟 1: 新增台股名稱模組

```bash
cp app/data_sources/taiwan_stocks.py /你的專案/app/data_sources/
```

### 步驟 2: 修改 compare_service.py

#### 2.1 在開頭加入導入

找到 `app/services/compare_service.py` 開頭的 import 區塊，加入：

```python
from app.data_sources.taiwan_stocks import TAIWAN_STOCK_NAMES, is_taiwan_stock
```

#### 2.2 修改 _fetch_price_data 方法

找到 `_fetch_price_data` 方法中返回 `info_dict` 的部分（約第 7529-7542 行）：

**原始代碼：**
```python
if info:
    info_dict = {
        "name": info.get("name", symbol),
        "type": asset_type,
        "current_price": current_price or info.get("current_price"),
        "symbol": symbol,
    }
else:
    info_dict = {
        "name": symbol, 
        "type": asset_type, 
        "current_price": current_price,
        "symbol": symbol,
    }
```

**替換為：**
```python
# ========== 修復: 台股優先使用本地名稱字典 ==========
name = symbol
if is_taiwan_stock(symbol):
    stock_code = symbol.replace('.TW', '').replace('.TWO', '')
    name = TAIWAN_STOCK_NAMES.get(stock_code, symbol)
elif info:
    name = info.get("name", symbol)
# ================================================

if info:
    info_dict = {
        "name": name,  # 使用修復後的名稱
        "type": asset_type,
        "current_price": current_price or info.get("current_price"),
        "symbol": symbol,
    }
else:
    info_dict = {
        "name": name,  # 使用修復後的名稱
        "type": asset_type, 
        "current_price": current_price,
        "symbol": symbol,
    }
```

### 步驟 3: 重新部署

```bash
git add .
git commit -m "fix: 修復台股名稱亂碼問題"
git push
```

---

## ✅ 驗證

1. 開啟比較頁面 (`/static/compare.html`)
2. 選擇「台灣科技股」預設組合
3. 確認股票名稱正確顯示：

| 代碼 | 預期名稱 |
|------|---------|
| 2330.TW | 台積電 |
| 2317.TW | 鴻海 |
| 2454.TW | 聯發科 |
| 3711.TW | 日月光投控 |
| 2308.TW | 台達電 |

---

## 📝 新增股票名稱

如需新增其他台股，編輯 `app/data_sources/taiwan_stocks.py`：

```python
TAIWAN_STOCK_NAMES = {
    # 現有股票...
    
    # 新增
    "1234": "新股票名稱",
}
```

---

## ⚠️ 注意事項

1. `taiwan_stocks.py` 必須使用 **UTF-8 編碼** 儲存
2. 確保 import 路徑正確
3. 此修復只影響比較頁面，其他頁面可能需要類似修改
