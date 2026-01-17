# 📚 SELA 文件包

> 整合日期: 2026-01-17  
> 整合自: 10+ 份分散文件

---

## 📁 文件結構

```
SELA_文件包/
├── SELA_系統規格書.md      # 架構、資料庫、API 設計
├── SELA_開發指南.md        # Bug 修復、前端優化、Router 統一、UI 指南
├── SELA_部署指南.md        # Railway 部署、遷移、運維
├── SELA_待辦追蹤.md        # P1/P2/P3 優先級待辦
├── SELA_更新日誌.md        # 版本變更紀錄 (CHANGELOG)
├── SELA_開發記錄_20260117.md # 最新開發記錄
└── README.md               # 本文件
```

---

## 📖 文件用途

| 文件 | 適合誰看 | 用途 |
|------|---------|------|
| **系統規格書** | 新開發者 | 了解系統架構、資料庫設計、API 端點 |
| **開發指南** | 開發者 | 查詢 Bug 解法、前端優化方案、程式碼範例 |
| **部署指南** | DevOps | Railway 部署、資料庫遷移、排程設定 |
| **待辦追蹤** | 所有人 | 查看待辦事項、確認優先級 |
| **更新日誌** | 所有人 | 追蹤版本變更、功能新增 |
| **開發記錄** | 開發者 | 最近一次開發的詳細記錄 |

---

## 🔄 整合來源

本文件包整合了以下原始文件：

| 原始文件 | 整合至 |
|---------|--------|
| SELA-01-系統規格書.md | SELA_系統規格書.md |
| SELA-02-開發指南.md | SELA_開發指南.md |
| BACKEND_CHANGES.md | SELA_開發指南.md |
| ROUTER_CHANGES.md | SELA_開發指南.md |
| UI_UNIFIED_GUIDE.md | SELA_開發指南.md |
| SELA-03-部署指南.md | SELA_部署指南.md |
| SELA-04-待辦追蹤.md | SELA_待辦追蹤.md |
| CHANGELOG.md | SELA_更新日誌.md |
| 交班_20260115_2330.md | SELA_更新日誌.md + SELA_開發記錄_20260117.md |
| README.md (圖表修復包) | SELA_開發記錄_20260117.md |

---

## 🎯 快速查詢

### 我想了解系統架構
→ 看 **SELA_系統規格書.md**

### 我遇到 Bug / 前端問題
→ 看 **SELA_開發指南.md** 第 1-4 章

### 我要統一 Router 認證
→ 看 **SELA_開發指南.md** 第 5 章

### 我要部署到 Railway
→ 看 **SELA_部署指南.md**

### 我想知道接下來做什麼
→ 看 **SELA_待辦追蹤.md**

### 我想知道最近改了什麼
→ 看 **SELA_更新日誌.md** 或 **SELA_開發記錄_20260117.md**

---

## 📝 重要提醒

### 指標欄位名稱
`indicator_service.py` 產生的欄位都是**小寫**：
- `ma20`, `ma50`, `ma200` (不是 `MA20`)
- `rsi` (不是 `RSI`)
- `macd_dif`, `macd_dea`, `macd_hist`
- `kd_k`, `kd_d`

### Railway 資料庫遷移
Railway 一般用戶無法直接執行 SQL，所有遷移必須透過 `database.py` 的 `run_migrations()` 函數。

### LINE Login 多環境
需在 LINE Developers Console 添加每個環境的 Callback URL。

---

## 🔗 Memory 同步待辦

以下待辦已同步至 Claude Memory：

> SELA 待辦: P1: (1)追蹤清單載入慢診斷 (2)訂閱精選前端Tab (3)追蹤清單匯出匯入 (4)持股交易匯出匯入 (5)stock_info種子表 P2: (6)成交量圖表 (7)MA進階分析 (8)熱門追蹤統計
