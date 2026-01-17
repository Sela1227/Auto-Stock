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
└── patch_broker_feature.py    # 一鍵補丁腳本
```

### 一鍵補丁會修改
- `app/main.py` - 加入 broker router
- `app/database.py` - 加入資料庫遷移
- `app/routers/portfolio.py` - 加入 broker_id 支援
- `templates/dashboard.html` - 加入 broker.js 引用
- 交易模型 - 加入 broker_id 欄位

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

### 2. 執行補丁腳本
```bash
# 複製補丁到根目錄
cp sela_update/patch_broker_feature.py ./

# 執行補丁
python patch_broker_feature.py
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
- **券商管理**：可建立、編輯、刪除券商
- **交易關聯券商**：新增交易時可選擇券商
- **快速新增券商**：在交易表單中可直接建立新券商

### Bug 修復
- ✅ 目標價功能 - 支援「高於/低於」方向
- ✅ 目標價即時更新 - 修復 AppState 快取問題
- ✅ 股票名稱查詢 - 修正 API 路徑
- ✅ 持股載入失敗 - 修正 return_rate undefined 錯誤
- ✅ numpy 類型序列化 - 修正 MA 進階分析

### UI 優化
- 移除手續費/交易稅欄位（簡化介面）
- 目標價標記更明顯（綠色高於/紅色低於）
- 券商選擇下拉選單

---

## 📝 測試檢查清單

- [ ] 新增券商
- [ ] 新增交易時選擇券商
- [ ] 新增交易時快速建立券商
- [ ] 目標價設定（高於/低於）
- [ ] 目標價即時更新
- [ ] 股票名稱自動帶入
- [ ] 持股記錄正常載入

---

## ⚠️ 注意事項

1. 補丁腳本會自動備份修改的檔案（.bak 結尾）
2. 首次部署會自動建立 brokers 資料表
3. 如果補丁執行失敗，請參考 `SELA_券商功能部署指南.md` 手動修改
