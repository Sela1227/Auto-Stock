# SELA 更新包 20260114

## 目錄結構

```
├── static/
│   └── dashboard.html      # 追蹤清單排序功能
├── app/
│   └── services/
│       └── cache_helper.py # 查詢結果快取模組（新增）
└── README.md
```

---

## 功能 1: 追蹤清單排序

### 排序選項
- **自訂** - 按加入時間（最新在前）
- **代碼** - 按股票代碼 A-Z
- **漲幅↓** - 漲幅高到低
- **跌幅↓** - 漲幅低到高

### 特點
- ✅ 排序偏好自動儲存到 localStorage
- ✅ 切換排序不重新呼叫 API
- ✅ 手機版滾動友善

---

## 功能 2: 查詢結果快取

需手動在 `app/routers/stock.py` 的 `get_stock_analysis` 函數 return 前加入：

```python
from app.services.cache_helper import cache_stock_price

day_change = calc_change(1)
prev_close = float(df.iloc[-2]['close_raw']) if len(df) > 1 else None
change_amount = current_price - prev_close if prev_close else None

cache_stock_price(
    symbol=symbol,
    name=stock_name,
    price=current_price,
    prev_close=prev_close,
    change=change_amount,
    change_pct=day_change,
    volume=volume_today
)
```

---

## 部署步驟

1. 解壓後直接覆蓋到專案根目錄
2. （可選）手動修改 `stock.py` 啟用查詢快取
3. 重新部署
