# 🔧 Dashboard.html 優化說明

## 優化摘要

| 項目 | 原始 | 優化後 | 變化 |
|------|------|--------|------|
| dashboard.html | 1908 行 | 1419 行 | **-489 行 (-26%)** |
| modals.js (新增) | - | 628 行 | 新增檔案 |

## 變更內容

### 1. 移除的 Modal (約 500 行)
以下 Modal 已從 `dashboard.html` 移至 `static/js/modals.js`：

- `chartFullscreen` - 全螢幕圖表
- `indexChartModal` - 指數圖表 Modal
- `sentimentChartModal` - 情緒圖表 Modal
- `returnsModal` - 年化報酬率 Modal
- `twTransactionModal` - 台股交易 Modal (106 行)
- `usTransactionModal` - 美股交易 Modal (93 行)
- `addWatchlistModal` - 新增追蹤清單 Modal
- `importWatchlistModal` - 匯入追蹤清單 Modal
- `importPortfolioModal` - 匯入持股交易 Modal
- `targetPriceModal` - 目標價設定 Modal
- `toast` - Toast 通知
- `tagEditModal` - 標籤編輯 Modal
- `assignTagModal` - 標籤指派 Modal

### 2. 新增檔案
- `static/js/modals.js` - Modal 動態生成模組

### 3. 修改的部分
在 `dashboard.html` 中：
- 新增 `<div id="modal-container"></div>` 作為 Modal 容器
- 新增 `<script src="/static/js/modals.js"></script>` 引用

## 部署步驟

1. **複製新檔案**
   ```bash
   cp static/js/modals.js 專案目錄/static/js/
   ```

2. **替換 dashboard.html**
   ```bash
   cp dashboard.html 專案目錄/static/dashboard.html
   ```

3. **測試功能**
   - 確認所有 Modal 可以正常開啟和關閉
   - 確認台股/美股交易功能正常
   - 確認標籤功能正常
   - 確認追蹤清單匯入/匯出功能正常

## 技術說明

### modals.js 運作原理

```javascript
// modals.js 在 DOMContentLoaded 時自動初始化
// 將所有 Modal HTML 注入到 #modal-container

window.initAllModals();  // 自動調用
```

### 優點

1. **可維護性提升** - Modal 集中管理，修改一處即可
2. **載入優化** - HTML 初始載入大小減少 26%
3. **關注點分離** - HTML 結構與 Modal 模板分離
4. **按需載入** - 可進一步優化為按需載入 Modal

## 回滾方案

如果需要回滾，只需：
1. 還原原始的 `dashboard.html`
2. 移除 `static/js/modals.js`（不需要刪除，只是不再使用）

---

*優化時間：2026-01-16*
