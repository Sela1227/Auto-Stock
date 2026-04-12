# AutoStock

**SELA 多用戶自動選股分析系統**  
FastAPI + Vanilla JS + PostgreSQL，部署於 Railway

---

## 版本歷程

### V1.05（2026-04-07）⚡ 效能大優化
- 🆕 **股票詳情快取**：減少 Yahoo API 調用 50%
- 🆕 **技術指標預計算**：排程預先計算追蹤清單股票
- 🆕 **圖表快取**：1 小時內相同請求直接返回，減少 CPU 80%
- 🆕 **新增 3 個快取表**：stock_detail_cache, indicator_cache, chart_cache

### V1.04（2026-04-07）
- 情緒指數優先載入

### V1.03（2026-04-07）
- 程式碼精簡

### V1.02（2026-04-07）
- 極簡排程

---

## 快取機制

| 快取類型 | 有效期（交易時段）| 有效期（非交易時段）|
|----------|-------------------|---------------------|
| 股票詳情 | 5 分鐘 | 1 小時 |
| 技術指標 | 10 分鐘 | 24 小時 |
| 圖表 | 1 小時 | 1 小時 |
| 情緒指數 | 60 秒 | 60 秒 |

---

## 排程任務

| 時間 | 任務 |
|------|------|
| 21:00 | 每日預載 + 指標預計算 |
| 09:00 | 情緒補充 |
| 09:30 | 匯率補充 |
| 03:00 | 清除過期快取 |
| 08:00, 18:00 | 訂閱源 |

---

## 新增資料表

```sql
-- 股票詳情快取
CREATE TABLE stock_detail_cache (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    price NUMERIC(12,4),
    ...
    updated_at TIMESTAMP
);

-- 技術指標快取
CREATE TABLE indicator_cache (
    symbol VARCHAR(20) PRIMARY KEY,
    ma5, ma10, ma20, ma60, ma120, ma240,
    rsi, macd_dif, k_value, d_value,
    score INTEGER,
    signals JSON,
    updated_at TIMESTAMP
);

-- 圖表快取
CREATE TABLE chart_cache (
    cache_key VARCHAR(50) PRIMARY KEY,
    symbol VARCHAR(20),
    days INTEGER,
    chart_data BYTEA,
    updated_at TIMESTAMP
);
```
