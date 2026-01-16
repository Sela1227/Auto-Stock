# 🔧 SELA Dashboard 安全優化版

## 優化摘要

| 項目 | 優化前 | 優化後 | 說明 |
|------|--------|--------|------|
| dashboard.html | 1,908 行 | **1,419 行** | -26% |
| Modal 位置 | 內嵌 HTML | modals.js | 動態載入 |

此版本**保留所有功能**，僅將 Modal HTML 移到 JavaScript 動態生成。

---

## 檔案結構

```
static/
├── dashboard.html    # 優化後主頁面 (1,419 行)
└── js/
    └── modals.js     # 新增：Modal 動態生成 (628 行)
```

---

## 部署步驟

### 1. 備份原檔案
```bash
cp static/dashboard.html static/dashboard.html.backup
```

### 2. 複製新檔案
```bash
cp static/dashboard.html 你的專案/static/
cp static/js/modals.js 你的專案/static/js/
```

### 3. 驗證
- 所有 section 功能應正常運作
- 所有 Modal 對話框應正常開啟/關閉

---

## 移出的 Modal (共 13 個)

1. `chartFullscreen` - 全螢幕股票圖表
2. `indexChartModal` - 指數走勢圖
3. `sentimentChartModal` - 情緒指數圖表
4. `returnsModal` - 報酬率詳情
5. `twTransactionModal` - 台股交易表單
6. `usTransactionModal` - 美股交易表單
7. `addWatchlistModal` - 新增追蹤清單
8. `importWatchlistModal` - 匯入追蹤清單
9. `importPortfolioModal` - 匯入持股紀錄
10. `targetPriceModal` - 目標價設定
11. `toast` - Toast 通知
12. `tagEditModal` - 標籤編輯
13. `assignTagModal` - 指派標籤

---

## 回滾方案

```bash
cp static/dashboard.html.backup static/dashboard.html
```

---

*更新日期：2026-01-16*
