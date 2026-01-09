# 📊 報酬率比較 - 導航連結安裝說明

## 檔案內容

- `static/compare-nav.js` - 自動注入導航連結的 JavaScript 補丁

## 安裝步驟

### 步驟 1：複製檔案

將 `static/compare-nav.js` 複製到你的專案 `static/` 目錄

### 步驟 2：修改 dashboard.html

在 `dashboard.html` 的 `</body>` 標籤前加入以下一行：

```html
    <script src="/static/compare-nav.js"></script>
</body>
</html>
```

### 完成！

重新整理頁面後，你會看到：

1. **側邊欄** - 在「設定」下方新增「報酬率比較」連結
2. **儀表板** - 在頂部顯示快捷入口卡片

## 手動安裝（如果自動注入不生效）

如果 JS 自動注入不生效，你可以手動在 `dashboard.html` 中添加連結：

### 桌面版側邊欄

找到類似這段程式碼：

```html
<a href="#" onclick="showSection('settings', event)" class="nav-link flex items-center px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg">
    <i class="fas fa-cog mr-3"></i>
    <span>設定</span>
</a>
```

在其後面加入：

```html
<a href="/static/compare.html" class="nav-link flex items-center px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg">
    <i class="fas fa-chart-bar mr-3"></i>
    <span>報酬率比較</span>
</a>
```

### 手機版側邊欄

找到手機版的「設定」連結（通常包含 `mobile-nav-link` class），同樣在後面加入：

```html
<a href="/static/compare.html" class="mobile-nav-link flex items-center px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg touch-target">
    <i class="fas fa-chart-bar mr-3 w-6"></i>
    <span>報酬率比較</span>
</a>
```

## 效果預覽

安裝後，側邊欄會顯示：

```
📊 儀表板
🔍 股票查詢
⭐ 追蹤清單
💓 市場情緒
⚙️ 設定
📊 報酬率比較  ← 新增
```

儀表板頂部會顯示一個紫色漸層的快捷入口卡片。
