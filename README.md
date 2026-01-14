# 📡 SELA 訂閱精選前端更新包

## 📅 版本資訊
- 更新日期：2026-01-14
- 功能：新增「訂閱精選」Tab

---

## 📦 更新內容

### 檔案清單
```
static/
└── dashboard.html    # 完整更新的前端頁面
```

### 新增功能
- ✅ 側邊欄新增「訂閱精選」導航（桌面版 + 手機版）
- ✅ 訂閱精選 Section 頁面
- ✅ 訂閱來源列表（顯示可訂閱的來源）
- ✅ 一鍵訂閱/取消訂閱功能
- ✅ 精選股票列表（含即時價格、漲跌幅）
- ✅ 熱度標籤（🔥熱門 / 📈關注）
- ✅ 剩餘有效天數顯示
- ✅ 點擊股票跳轉查詢

---

## 🚀 部署步驟

### 1. 解壓並覆蓋
將 `static/dashboard.html` 覆蓋到專案的 `static/` 目錄

### 2. 部署後初始化（首次）
```bash
# 初始化訂閱源
POST /api/subscription/admin/init

# 回溯抓取 30 天
POST /api/subscription/admin/fetch?backfill=true
```

---

## 📝 後端 API 需求

確保以下 API 已部署並正常運作：

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/subscription/sources` | 所有訂閱源 |
| GET | `/api/subscription/my` | 用戶已訂閱（需登入）|
| POST | `/api/subscription/subscribe/{id}` | 訂閱（需登入）|
| DELETE | `/api/subscription/unsubscribe/{id}` | 取消訂閱（需登入）|
| GET | `/api/subscription/picks` | 用戶訂閱精選（需登入）|
| GET | `/api/subscription/picks/{slug}` | 特定來源精選（公開）|

---

## ✅ 驗證清單

- [ ] 桌面版側邊欄可看到「訂閱精選」
- [ ] 手機版側邊欄可看到「訂閱精選」
- [ ] 點擊後可切換到訂閱精選頁面
- [ ] 訂閱來源列表正常顯示
- [ ] 精選股票列表正常顯示
- [ ] 訂閱/取消訂閱功能正常
- [ ] 點擊股票可跳轉到查詢頁面
