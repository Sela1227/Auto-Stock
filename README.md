# 🔧 P1 功能修復包

## 問題修復

1. **`/api/tags` 404** - tags_router 沒有註冊到 main.py
2. **stock_info 種子表** - 現在包含在 p1_migrations.py 中
3. **前端標籤功能** - 確保 tags.js 在 watchlist.js 之前載入

## 🚀 快速部署

```powershell
.\p1_fix\deploy.ps1
git add . && git commit -m "fix: P1 tags + stock_info 修復" && git push
```

## 📦 檔案清單

```
p1_fix/
├── app/utils/
│   └── p1_migrations.py    # 完整版（含 33 筆種子資料）
├── static/js/
│   ├── tags.js             # 標籤管理模組
│   └── watchlist.js        # 追蹤清單（含標籤整合）
├── deploy.ps1              # 自動部署腳本
└── README.md
```

## 部署腳本會自動處理

| 項目 | 動作 |
|------|------|
| static/js/tags.js | ✅ 複製 |
| static/js/watchlist.js | ✅ 複製 |
| app/utils/p1_migrations.py | ✅ 複製（含種子資料）|
| app/main.py 加入 tags_router | ✅ 自動 |
| app/main.py 加入 stock_info_router | ✅ 自動 |
| dashboard.html 加入 tags.js | ✅ 自動 |

## ✅ API 端點

部署後可用：

### 🏷️ 標籤 API
- `GET /api/tags` - 用戶標籤列表
- `POST /api/tags` - 建立標籤
- `GET /api/tags/watchlist/{id}` - 取得追蹤項目標籤
- `PUT /api/tags/watchlist/{id}` - 設定追蹤項目標籤

### 📊 股票資訊 API
- `GET /api/stock-info/search?q=台積` - 搜尋
- `GET /api/stock-info/popular` - 熱門 33 筆
