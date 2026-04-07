# 📝 SELA 更新日誌

所有重要的變更都會記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
版本號遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

---

## [Unreleased]

### Planned
- Phase 5: 錯誤回報系統
- Phase 6: 會員權限系統

---

## [0.9.0] - 2026-01-17

### Added
- **MA 強化分析功能 (ma_advanced_service.py)**
  - 距離均線百分比 (dist_ma20/50/200/250)
  - 黃金/死亡交叉偵測 (MA20/50、MA50/200、MA20/200)
  - 交叉發生天數 (golden_cross_xx_days)
  - 均線排列分析（多頭/空頭/盤整 + 強度評分）
  - 支撐/壓力位判斷（最近支撐/壓力 + 完整列表）
  - 前端渲染模組 (search-ma-advanced.js)

- **目標價方向功能**
  - 設定目標價時可選擇「高於時提醒」或「低於時提醒」
  - 追蹤清單顯示目標價標記（區分方向）
  - 即時更新（不需刷新頁面）
  - 新增 `target_direction` 欄位到 watchlists 表

- **券商功能（待部署）**
  - 券商資料模型 (broker.py)
  - 券商 API (broker_router.py)
  - 交易紀錄關聯券商帳戶
  - 券商管理前端 (broker.js)
  - 預設券商設定

### Fixed
- 修復 AppState 快取導致目標價設定後不更新的問題
- 修復 numpy 類型無法 JSON 序列化的問題

---

## [0.8.4] - 2026-01-17

### Added
- **追蹤清單匯出匯入**
  - `GET /api/watchlist/export` - 匯出 JSON/CSV
  - `POST /api/watchlist/import` - 匯入 JSON/CSV
  - 前端匯出匯入 UI

- **持股交易匯出匯入**
  - `GET /api/portfolio/export` - 匯出交易紀錄
  - `POST /api/portfolio/import` - 匯入交易紀錄
  - 前端 portfolio-export-import.js

- **stock_info 種子表**
  - 30+ 筆熱門股票預建資料
  - `models/stock_info.py` + `routers/stock_info.py`

- **成交量圖表**
  - 漲跌顏色柱狀圖
  - 20日均量線
  - `renderVolumeChart()` 函數

- **熱門追蹤統計**
  - `GET /api/watchlist/popular`
  - 顯示最多用戶追蹤的股票

- **index_service 模組**
  - `services/index_service.py`
  - 四大指數更新服務

---

## [0.8.3] - 2026-01-17

### Added
- **市場感知快取 (price_cache_service.py)**
  - `get_symbol_market()` - 判斷股票所屬市場
  - `is_market_open_for_symbol()` - 判斷市場是否開盤
  - `get_cached_price_smart()` - 智慧快取判斷
  - 非交易時段效能提升 10-40x

- **圖表功能完整修復 (chart-fix-final.js)**
  - 時間範圍按鈕可正常點擊
  - MA 均線正確顯示
  - 圖例可點擊切換
  - 使用 `Object.defineProperty` 防止函數覆蓋

### Changed
- **API 回傳新增 market_open 欄位**
  - `GET /api/stock/{symbol}` 新增 `market_open`
  - `GET /api/watchlist/with-prices` 新增 `market_status`

### Fixed
- 修復圖表時間範圍按鈕無法點擊問題
- 修復 MA 均線不顯示問題
- 修復圖例無法點擊切換問題
- 修復多個 JS 檔案函數覆蓋問題

---

## [0.8.2] - 2026-01-15

### Added
- **管理員工具區塊**
  - 手動觸發訂閱抓取按鈕
  - 更新價格快取按鈕
  - 更新匯率按鈕

- **追蹤清單 MA20 排序**
  - 新增「MA20距離」排序選項
  - 計算價格與 MA20 的差距百分比

- **快速新增追蹤**
  - `quickAddToWatchlist()` 函數導出全域
  - 從訂閱精選可直接加入追蹤

### Fixed
- **股票詳情技術指標消失**
  - 原因: 快取邏輯錯誤
  - 修正: 永遠從 Yahoo Finance 取得完整資料
  - 檔案: `app/routers/stock.py`

- **訂閱按鈕沒反應**
  - 原因: onclick 未正確綁定
  - 修正: 改用 `window.toggleSubscription`
  - 檔案: `static/js/subscription.js`

- **訂閱精選日期顯示錯誤**
  - 修正: 優先使用 `article_date`
  - 檔案: `static/js/subscription.js`

---

## [0.8.1] - 2026-01-08

### Added
- **訊號偵測引擎 (signal_service.py)**
  - 均線訊號：黃金交叉、死亡交叉、接近突破/跌破
  - RSI 訊號：超買 (>70)、超賣 (<30)
  - MACD 訊號：黃金交叉、死亡交叉
  - KD 訊號：黃金交叉、死亡交叉
  - 布林通道訊號：突破上軌、跌破下軌
  - 成交量訊號：量比暴增 (>2 倍)
  - 市場情緒訊號：極度恐懼 (<20)、極度貪婪 (>80)

- **LINE 推播通知服務 (line_notify_service.py)**
  - LINE Messaging API 整合
  - 單一用戶推播 (push_text_message)
  - 多用戶推播 (multicast_text_message，最多 500 人)
  - Flex Message 支援

- **排程任務整合 (scheduler.py)**
  - 訊號偵測整合到每日更新任務
  - 24 小時內不重複通知同一訊號

- **管理後台訊號功能**
  - POST /api/admin/signal/detect
  - POST /api/admin/signal/notify
  - POST /api/admin/signal/test-push
  - GET /api/admin/signal/status

- **管理後台登入統計**
  - 總登入次數
  - 每個用戶的登入次數

### Changed
- **年化報酬率簡化**
  - Yahoo Finance 歷史價格為除權息調整後價格
  - 只顯示單一「CAGR (年化報酬率)」

---

## [0.8.0] - 2026-01-08

### Added
- **Phase 3: 走勢比較功能**
  - 新增「走勢比較」頁面
  - 支援最多 5 支股票/指數同時比較
  - 價格正規化為起始日 = 100%
  - 時間範圍選擇：1M / 3M / 6M / 1Y
  - API: GET /api/stock/compare/history

- **Phase 4: 年化報酬率計算**
  - 計算 1Y / 3Y / 5Y / 10Y 年化報酬率
  - 顯示配息次數、年均殖利率
  - API: GET /api/stock/{symbol}/returns

- **儀表板新增台股加權指數**
  - 支援 ^TWII 台灣加權股價指數
  - 儀表板指數卡片從 3 個增加到 4 個

### Fixed
- 修復歷史股價使用調整後價格的問題
- 修復指數歷史 API 的 NaN 值 JSON 序列化錯誤
- 修復年化報酬率 yearly_detail 變數未定義錯誤

---

## [0.7.0] - 2026-01-07

### Added
- **Phase 2: 前端顯示功能**
  - 儀表板頂部三大指數卡片（S&P 500、道瓊工業、納斯達克）
  - 點擊指數卡片開啟全螢幕走勢圖
  - 恐懼貪婪指數點擊開啟全螢幕歷史走勢圖
  - **管理後台市場資料管理區塊**

### Changed
- 「情緒指數」更名為「恐懼貪婪指數」
- 圖表改為 Modal 全螢幕顯示

### Fixed
- 修復 get_latest_indices 回傳格式（List → Dict）
- 加強資料庫錯誤處理，自動 fallback 到 Yahoo Finance API

---

## [0.6.1] - 2026-01-07

### Fixed
- **用戶身份驗證強化**
  - 登入時清除所有舊的 localStorage/sessionStorage 資料
  - JWT Token 驗證增加 LINE ID 一致性檢查
  - 所有 API 請求改用統一的 apiRequest 函數
  - **UserResponse schema 加入 is_admin 欄位**

- **追蹤清單安全性**
  - 刪除時增加 user_id 二次驗證
  - 所有操作加入詳細 log 記錄

### Added
- app/logging_config.py: 日誌設定模組

---

## [0.6.0] - 2026-01-07

### Added
- **資料基礎建設 (Phase 1)**
  - 三大指數支援 (S&P 500, 道瓊, 納斯達克)
  - IndexPrice 資料模型
  - 10 年歷史資料支援
  - DividendHistory 資料模型
  - 情緒指數歷史（幣圈 365 天、美股每日累積）
  - 排程任務服務 (scheduler.py)
  - 市場服務 (market_service.py)
  - 市場 API 端點 (/api/market)

### Changed
- stock_service.py 支援 10 年歷史資料
- yahoo_finance.py 新增指數和配息抓取方法
- fear_greed.py 新增歷史資料抓取

---

## [0.5.3] - 2026-01-06

### Fixed
- 可折疊指標區塊在桌面版無法運作
- 追蹤清單缺少即時價格資訊
- 模板選擇無視覺回饋
- 設定頁面顯示 LINE ID（隱私問題）

### Changed
- 追蹤清單卡片增加即時價格和漲跌幅
- 模板按鈕選中狀態樣式
- 設定頁面改顯示會員等級

---

## [0.3.0] - 2026-01-05

### Added
- **用戶系統**
  - LINE Login 整合
  - JWT Token 認證
  - 用戶資料管理

- **追蹤清單功能**
  - 新增/移除追蹤標的
  - 自訂備註
  - 追蹤清單總覽 (含即時價格)

- **個人化設定**
  - 指標顯示設定
  - 通知設定
  - 指標參數調整
  - 預設模板 (極簡/標準/完整/短線)

- **FastAPI Web API**
  - 認證路由 (/auth)
  - 股票查詢 (/api/stock)
  - 加密貨幣查詢 (/api/crypto)
  - 追蹤清單管理 (/api/watchlist)
  - 設定管理 (/api/settings)
  - 市場情緒 (/api/market/sentiment)
  - Swagger 文件 (/docs)

---

## [0.2.0] - 2026-01-05

### Added
- **圖表繪製服務 (chart_service.py)**
  - 價格走勢圖 + 均線 + 布林通道
  - 成交量柱狀圖
  - RSI、MACD、KD 子圖
  - 均線交叉點標記
  - K線圖支援

- **加密貨幣支援**
  - CoinGecko API 整合
  - BTC、ETH 價格追蹤
  - 幣圈技術指標 (MA7/25/99)

- **市場情緒指數**
  - CNN Fear & Greed Index (美股)
  - Alternative.me (加密貨幣)

- **CLI 新增指令**
  - `sentiment` - 查詢市場情緒
  - `chart` - 生成技術分析圖表
  - 支援加密貨幣查詢 (BTC, ETH)

---

## [0.1.0] - 2026-01-05

### Added
- 專案初始化
- Yahoo Finance 股價資料抓取
- SQLite 本地快取機制
- **技術指標計算引擎**
  - 移動平均線 (MA20, MA50, MA200)
  - RSI 相對強弱指標
  - MACD 指數平滑異同移動平均
  - KD 隨機指標
  - 布林通道
  - OBV 能量潮指標
  - 成交量分析
- **訊號偵測系統**
  - 均線黃金交叉/死亡交叉
  - 接近突破/跌破預警
  - RSI 超買超賣
  - MACD/KD 交叉
- 綜合評分系統
- CLI 命令列查詢介面
