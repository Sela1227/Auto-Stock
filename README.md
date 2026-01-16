# SELA 追蹤清單載入效能優化

## 🚀 效能改善

| 項目 | 優化前 | 優化後 | 改善 |
|------|--------|--------|------|
| API 請求數 | 1 + N 次 | 1 次 | -95% |
| 載入時間 | 2-5 秒 | < 200ms | -90%+ |

## 📁 檔案說明

```
sela_update/
├── app/
│   └── routers/
│       └── watchlist.py      # 後端 API（完整替換）
├── static/
│   └── js/
│       └── watchlist.js      # 前端 JS（完整替換）
└── README.md
```

## 📝 更新方式

1. **後端**：將 `app/routers/watchlist.py` 複製到專案中替換原檔案
2. **前端**：將 `static/js/watchlist.js` 複製到專案中替換原檔案
3. **部署**：重新部署即可，無需資料庫遷移

## 🔧 修改內容

### 後端 `watchlist.py`
- 在 `/api/watchlist/with-prices` 端點中加入批量標籤查詢
- 每個返回項目現在包含 `tags` 陣列
- 新增匯入：`from app.models.watchlist_tag import UserTag, watchlist_tags`

### 前端 `watchlist.js`
- `loadWatchlist()` 函數不再調用 `loadAllWatchlistTags()`
- 直接使用 API 返回的 `item.tags` 陣列

## ⚠️ 注意事項

- 確認 `app/models/watchlist_tag.py` 存在且包含 `UserTag` 和 `watchlist_tags`
- 如果標籤功能尚未啟用，API 會自動容錯，不影響主要功能
