# 🚀 SELA Dashboard 模組化重構指南

## 優化摘要

| 指標 | 優化前 | 優化後 | 改善幅度 |
|------|--------|--------|----------|
| dashboard.html | 1,908 行 | 102 行 | **-95%** |
| 單檔維護 | ❌ 困難 | ✅ 模組化 | - |
| 按需載入 | ❌ 全部載入 | ✅ 支援 | - |

---

## 檔案結構

```
static/
├── dashboard.html          # 主框架 (102 行)
├── css/
│   └── dashboard.css       # 樣式 (保持不變)
└── js/
    ├── utils.js            # 工具函數 (保持不變)
    ├── core.js             # 核心邏輯 (保持不變)
    ├── layout.js           # 🆕 導航元件 (157 行)
    ├── sections.js         # 🆕 頁面內容 (295 行)
    ├── modals.js           # 🆕 彈窗元件 (628 行)
    ├── dashboard.js        # 儀表板邏輯 (保持不變)
    └── ...其他 JS
```

---

## 部署步驟

### 步驟 1：備份原檔案
```bash
cp static/dashboard.html static/dashboard.html.backup
```

### 步驟 2：複製新檔案
```bash
# 複製主框架
cp static/dashboard.html 你的專案/static/

# 複製新 JS 模組
cp static/js/layout.js 你的專案/static/js/
cp static/js/sections.js 你的專案/static/js/
cp static/js/modals.js 你的專案/static/js/
```

### 步驟 3：驗證載入順序
確認 `dashboard.html` 中 JS 載入順序：
```html
<script src="/static/js/utils.js"></script>
<script src="/static/js/core.js"></script>
<script src="/static/js/layout.js"></script>      <!-- 新增 -->
<script src="/static/js/sections.js"></script>    <!-- 新增 -->
<script src="/static/js/modals.js"></script>      <!-- 新增 -->
<script src="/static/js/dashboard.js"></script>
<!-- ...其他 JS -->
```

---

## 模組說明

### layout.js (157 行)
負責動態生成導航元件：
- 手機版側邊選單 (`#mobileSidebar`)
- 電腦版側邊欄 (`#desktopSidebar`)  
- 底部導航列 (`#mobileBottomNav`)

**優點**：導航項目集中配置，新增/修改只需改一處

### sections.js (295 行)
負責按需載入頁面內容：
- dashboard, search, watchlist, sentiment
- compare, portfolio, subscription
- settings, cagr, admin

**運作原理**：攔截 `showSection()` 函數，在切換頁面時才載入對應 HTML

### modals.js (628 行)
負責管理所有彈窗：
- 全螢幕圖表、指數圖表、情緒圖表
- 台股/美股交易 Modal
- 追蹤清單/持股匯入匯出 Modal
- 標籤管理 Modal、Toast 通知

**運作原理**：頁面載入時注入到 `#modal-container`

---

## 回滾方案

如果出現問題，可快速回滾：
```bash
cp static/dashboard.html.backup static/dashboard.html
```

---

## 後續優化建議

| 優先級 | 項目 | 說明 |
|--------|------|------|
| P1 | search.js 拆分 | 888 行 → 模組化 |
| P1 | indicator_service.py | 830 行 → 獨立指標類別 |
| P2 | ES6 模組化 | import/export |
| P2 | 打包工具 | Webpack/Vite |

---

*更新日期：2026-01-16*
