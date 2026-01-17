# SELA 更新包 - 券商功能 + Bug 修復

## 📅 更新日期：2026-01-17

---

## 📦 包含內容

### 可直接替換的檔案
```
sela_update/
├── app/
│   ├── models/
│   │   └── broker.py          # 券商模型（新增）
│   └── routers/
│       └── broker.py          # 券商 API（新增）
├── static/
│   └── js/
│       ├── broker.js          # 券商管理前端（新增）
│       ├── transaction.js     # 交易表單（修改）
│       ├── modals.js          # Modal 模板（修改）
│       ├── watchlist.js       # 追蹤清單（修改）
│       └── portfolio.js       # 投資記錄（修改）
├── patch_broker_feature.py    # main.py + dashboard.html 補丁
├── patch_database_broker.py   # database.py 遷移補丁
└── patch_portfolio.py         # portfolio.py 補丁（含最後價格 API）
```

---

## 🚀 部署步驟

### 1. 解壓縮並複製檔案
```bash
# 解壓縮
unzip sela_update.zip

# 複製可直接替換的檔案
cp -r sela_update/app/* app/
cp -r sela_update/static/* static/
```

### 2. 執行補丁腳本（依序執行）
```bash
# 1. main.py + dashboard.html 補丁
python sela_update/patch_broker_feature.py

# 2. database.py 遷移補丁
python sela_update/patch_database_broker.py

# 3. portfolio.py 補丁
python sela_update/patch_portfolio.py
```

### 3. 重新部署
```bash
git add .
git commit -m "新增券商功能 + Bug 修復"
git push
```

---

## ✨ 本次更新內容

### 新功能
- **券商管理**：在投資記錄頁面（美股記錄下方）管理券商
- **交易關聯券商**：新增交易時可選擇券商
- **快速新增券商**：在交易表單中可直接建立新券商
- **自動帶入價格**：輸入股票代碼後自動帶入最後一筆交易價格

### Bug 修復
- ✅ **台股現值計算**：修正 symbol 未加 `.TW` 導致 price_cache 查不到
- ✅ 目標價功能 - 支援「高於/低於」方向
- ✅ 目標價即時更新 - 修復 AppState 快取問題
- ✅ 股票名稱查詢 - 修正 API 路徑
- ✅ 持股載入失敗 - 修正 return_rate undefined 錯誤

### UI 優化
- 移除手續費/交易稅欄位（簡化介面）
- 目標價標記更明顯（綠色高於/紅色低於）
- 券商選擇下拉選單
- 價格自動帶入時欄位閃爍提示

---

## 📝 測試檢查清單

- [ ] 台股現值正確顯示
- [ ] 新增券商
- [ ] 新增交易時選擇券商
- [ ] 新增交易時快速建立券商
- [ ] 輸入股票代碼後自動帶入最後價格
- [ ] 目標價設定（高於/低於）

---

## ⚠️ 注意事項

1. 補丁腳本會自動備份修改的檔案（.bak 結尾）
2. 首次部署會自動建立 brokers 資料表
3. 券商管理區塊會自動插入到投資記錄頁面的美股記錄下方
