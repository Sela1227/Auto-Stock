# Dashboard 更新說明

## 變更內容

新增「報酬率比較」導航連結：

1. **手機版側邊欄** - 在「走勢比較」和「設定」之間
2. **電腦版側邊欄** - 在「走勢比較」和「設定」之間

連結指向 `/static/compare.html`（獨立的報酬率比較頁面）

## 使用方式

直接將 `static/dashboard.html` 覆蓋到專案的 `static/` 目錄即可。

## 注意事項

- 確保 `/static/compare.html` 已經部署（來自 `compare_frontend.zip`）
- 確保後端 API 已更新（來自 `cagr_compare_update.zip`）
