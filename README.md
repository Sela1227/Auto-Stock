# P1 低難度功能部署指南

## 功能清單

| 功能 | 說明 |
|------|------|
| 到價提醒變色 | 追蹤清單設定目標價，達標時黃色高亮 |
| 管理員登入自動更新 | 管理員登入後背景自動更新價格/情緒 |

---

## 部署步驟

### 1. 覆蓋後端檔案

```bash
# 複製到專案目錄
cp app/models/watchlist.py /Users/sela/Documents/Python/自動選股系統/app/models/
cp app/routers/watchlist.py /Users/sela/Documents/Python/自動選股系統/app/routers/
cp app/routers/auth.py /Users/sela/Documents/Python/自動選股系統/app/routers/
```

### 2. 添加資料庫遷移

在 `app/database.py` 的 `run_migrations()` 函數中加入：

```python
# 在現有遷移之後加入
# P1: 追蹤清單目標價
try:
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='watchlists' AND column_name='target_price'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE watchlists ADD COLUMN target_price NUMERIC(12, 4) DEFAULT NULL")
        logger.info("✅ 遷移: 追蹤清單 target_price 欄位已添加")
except Exception as e:
    logger.warning(f"遷移 target_price: {e}")
```

### 3. 更新前端

**方法 A: 整合到現有 dashboard.html**

找到 `loadWatchlist` 函數，替換為 `static/js/watchlist-enhanced.js` 中的版本。

同樣替換 `loadWatchlistOverview` 函數。

**方法 B: 引入獨立 JS 檔案**

```html
<!-- 在 dashboard.html 的 </body> 前加入 -->
<script src="/static/js/watchlist-enhanced.js"></script>
```

然後刪除 dashboard.html 中原有的 `loadWatchlist` 和 `loadWatchlistOverview` 函數。

### 4. 部署

```bash
git add .
git commit -m "feat: P1 到價提醒變色 + 管理員自動更新"
git push
```

### 5. 驗證

1. **到價提醒變色**
   - 進入追蹤清單
   - 點擊任一股票的 🎯 圖示
   - 設定目標價
   - 當現價 >= 目標價時，卡片會變黃色

2. **管理員自動更新**
   - 用管理員帳號登入
   - 查看 Railway 日誌，應該看到：
     ```
     🔄 管理員登入，觸發自動更新...
     ✅ 股票價格更新完成
     ✅ 市場情緒更新完成
     🎉 管理員自動更新全部完成
     ```

---

## API 變更

### 新增端點

```
PUT /api/watchlist/{item_id}/target-price
Body: { "target_price": 150.00 }  // 設定目標價
Body: { "target_price": null }     // 清除目標價
```

### 修改端點

```
GET /api/watchlist/with-prices
回應新增欄位:
- target_price: 目標價格
- target_reached: 是否已達標 (boolean)
```

---

## 檔案清單

```
p1-features/
├── app/
│   ├── models/
│   │   └── watchlist.py      # 加入 target_price 欄位
│   └── routers/
│       ├── watchlist.py      # 加入目標價 API
│       └── auth.py           # 加入管理員自動更新
├── migrations/
│   └── add_target_price.sql  # SQL 遷移（參考用）
├── static/js/
│   └── watchlist-enhanced.js # 前端功能
└── README.md                 # 本文件
```
