# 導航修復 - 報酬率比較與管理後台整合

## 問題
原本「報酬率比較」和「管理後台」是指向外部頁面 (`/static/compare.html`, `/static/admin.html`)，導致 UI 不一致。

## 修復內容

### 1. dashboard.html 修改
- 新增 `section-cagr`（報酬率比較區塊）
- 新增 `section-admin`（管理後台區塊）
- 修正導航連結改為內部 section 切換
- 加入 `cagr.js` 和 `admin.js` 載入
- 加入 Tag Modal（標籤編輯和指派）

### 2. 新增 JS 檔案
- `static/js/cagr.js` - 報酬率比較功能
- `static/js/admin.js` - 管理後台功能

## 部署步驟

```powershell
# 1. 解壓 nav_fix.zip
Expand-Archive nav_fix.zip -DestinationPath nav_fix

# 2. 複製檔案
Copy-Item "nav_fix\static\dashboard.html" "static\dashboard.html" -Force
Copy-Item "nav_fix\static\js\cagr.js" "static\js\cagr.js" -Force
Copy-Item "nav_fix\static\js\admin.js" "static\js\admin.js" -Force

# 3. 提交部署
git add .
git commit -m "fix: 整合報酬率比較和管理後台到 dashboard"
git push
```

## 修改摘要

| 修改項目 | 原本 | 修正後 |
|---------|------|--------|
| 手機版報酬率比較 | `href="/static/compare.html"` | `onclick="mobileNavTo('cagr')"` |
| 電腦版報酬率比較 | `href="/static/compare.html"` | `onclick="showSection('cagr', event)"` |
| 頂部管理後台 | `href="/static/admin.html"` | `onclick="showSection('admin', event)"` |
| 側邊欄管理後台 | `href="/static/admin.html"` | `onclick="showSection('admin', event)"` |

## 新增的 Section

### section-cagr（報酬率比較）
- 快速比較預設組合（科技七雄、三大指數、台股ETF、加密貨幣）
- 自訂標的選擇
- 年化報酬率計算
- 基準指數對比
- 儲存我的組合

### section-admin（管理後台）
- 用戶統計
- 市場資料管理
- 訊號檢查與推播
- 訂閱源管理
- 用戶管理
