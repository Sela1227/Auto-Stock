# Changelog

所有重要的變更都會記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
版本號遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

## [Unreleased]

### Planned
- Phase 5: 錯誤回報系統
- Phase 6: 會員權限系統

## [0.8.1] - 2025-01-07

### Added
- **Phase 3: 走勢比較功能**
  - 新增「走勢比較」頁面
  - 支援最多 5 支股票/指數同時比較
  - 價格正規化為起始日 = 100%
  - 快速選擇按鈕（四大指數、熱門美股、台股、加密貨幣）
  - 時間範圍選擇：1M / 3M / 6M / 1Y
  - 比較結果表格顯示起始價、最新價、漲跌幅
  - API: GET /api/stock/compare/history

- **Phase 4: 年化報酬率計算**
  - 股票查詢結果新增「年化報酬率」按鈕
  - 計算 1Y / 3Y / 5Y / 10Y 年化報酬率
  - 三種計算方式：
    - 價格報酬：純股價漲跌
    - 含配息：股價 + 配息（不再投入）
    - 配息再投入：配息以除息日股價買入更多股數
  - 顯示配息次數、年均殖利率
  - API: GET /api/stock/{symbol}/returns

- **儀表板新增台股加權指數**
  - 支援 ^TWII 台灣加權股價指數
  - 儀表板指數卡片從 3 個增加到 4 個
  - 走勢比較快速選擇新增台積電、鴻海

- **管理後台登入統計**
  - 統計卡片新增「總登入次數」
  - 用戶列表新增「登入次數」欄位
  - API: /api/admin/stats 新增 total_logins
  - API: /api/admin/users 新增 login_count

### Fixed
- **重要：修復歷史股價使用調整後價格的問題**
  - yfinance 預設回傳 auto_adjust=True（配息調整後價格）
  - 改為 auto_adjust=False 取得原始收盤價
  - 影響：年化報酬率、殖利率計算現在使用正確的歷史價格
- 修復指數歷史 API 的 NaN 值 JSON 序列化錯誤
- IndexPrice model to_dict() 加入 NaN/Infinity 檢查
- market_service save_index_data() 儲存前清理無效數值
- 修復走勢比較圖表需要 chartjs-adapter-date-fns
- 修復年化報酬率 yearly_detail 變數未定義錯誤

## [0.7.0] - 2025-01-07

### Added
- **Phase 2: 前端顯示功能**
  - 儀表板頂部三大指數卡片（S&P 500、道瓊工業、納斯達克）
  - 點擊指數卡片開啟全螢幕走勢圖（Modal 視窗）
  - 指數走勢支援 1M/3M/1Y/5Y 時間範圍切換
  - 恐懼貪婪指數點擊開啟全螢幕歷史走勢圖
  - 情緒走勢支援 1M/3M/6M/1Y 時間範圍切換
  - **管理後台市場資料管理區塊**
    - 初始化歷史資料按鈕
    - 更新三大指數按鈕
    - 更新恐懼貪婪指數按鈕
    - 執行每日更新按鈕

### Changed
- 「情緒指數」更名為「恐懼貪婪指數」
- 圖表改為 Modal 全螢幕顯示，解決卡片內嵌顯示問題
- 圖表邊距增加，改善觸控體驗

### Fixed
- 修復 get_latest_indices 回傳格式（List → Dict）
- 加強資料庫錯誤處理，自動 fallback 到 Yahoo Finance API
- 修復指數/情緒走勢圖無法正常顯示的問題

## [0.6.1] - 2025-01-07

### Fixed
- **用戶身份驗證強化**
  - 登入時清除所有舊的 localStorage/sessionStorage 資料，避免 A 用戶看到 B 用戶資料
  - JWT Token 驗證增加 LINE ID 一致性檢查
  - 前端 checkAuth 增加本地與伺服器用戶 ID 比對
  - 所有 API 請求改用統一的 apiRequest 函數，自動帶入驗證
  - **UserResponse schema 加入 is_admin 欄位**（修復管理員權限消失問題）

- **追蹤清單安全性**
  - 追蹤清單刪除時增加 user_id 二次驗證
  - 所有追蹤清單操作加入詳細 log 記錄
  - 前端操作前檢查 currentUser 是否存在

- **日誌系統強化**
  - 新增 logging_config.py 統一日誌設定
  - 認證服務 (auth_service) 完整登入流程 log
  - 追蹤清單服務 (watchlist_service) 操作 log
  - 日誌檔案按日期分類存放於 logs/ 目錄
  - 分離 auth、watchlist 專用日誌檔

### Changed
- auth_service.py: login_with_line() 加入完整 log 記錄
- auth_service.py: get_user_from_token() 加入 LINE ID 一致性驗證
- watchlist_service.py: 所有操作加入詳細 log
- watchlist.py router: 所有端點加入 log 記錄
- dashboard.html: 新增 apiRequest() 統一 API 請求函數
- dashboard.html: 新增 clearAllUserData() 清除用戶資料函數
- main.py: 使用 logging_config.py 初始化日誌系統
- schemas.py: UserResponse 加入 is_admin 欄位

### Added
- app/logging_config.py: 日誌設定模組

## [0.6.0] - 2025-01-07

### Added
- **資料基礎建設 (Phase 1)**
  - 三大指數支援
    - S&P 500 (^GSPC)
    - 道瓊工業 (^DJI)
    - 納斯達克 (^IXIC)
    - IndexPrice 資料模型
    - 10 年歷史資料支援
  - 配息資料
    - DividendHistory 資料模型
    - yfinance 配息抓取
  - 情緒指數歷史
    - 幣圈情緒 365 天歷史抓取
    - 美股情緒每日累積
  - 排程任務服務 (scheduler.py)
    - 每日自動更新股價
    - 每日更新三大指數
    - 每日更新市場情緒
    - 初始化歷史資料功能
  - 市場服務 (market_service.py)
    - 指數資料存取
    - 情緒資料存取
    - 配息資料存取
  - 市場 API 端點 (/api/market)
    - GET /indices - 取得三大指數
    - GET /indices/{symbol}/history - 指數歷史
    - GET /sentiment - 市場情緒
    - GET /sentiment/{market}/history - 情緒歷史
    - POST /admin/update - 手動觸發更新
    - POST /admin/initialize - 初始化歷史資料
    - POST /admin/update-indices - 更新指數
    - POST /admin/update-sentiment - 更新情緒
    - POST /admin/init-crypto-sentiment - 初始化幣圈情緒

### Changed
- stock_service.py 支援 10 年歷史資料
- yahoo_finance.py 新增指數和配息抓取方法
- fear_greed.py 新增歷史資料抓取

## [0.5.3] - 2025-01-06

### Fixed
- 可折疊指標區塊在桌面版無法運作
- 追蹤清單缺少即時價格資訊
- 模板選擇無視覺回饋
- 設定頁面顯示 LINE ID（隱私問題）

### Changed
- 追蹤清單卡片增加即時價格和漲跌幅
- 模板按鈕選中狀態樣式
- 設定頁面改顯示會員等級

## [0.3.0] - 2025-01-05

### Added
- 用戶系統
  - LINE Login 整合
  - JWT Token 認證
  - 用戶資料管理
- 追蹤清單功能
  - 新增/移除追蹤標的
  - 自訂備註
  - 追蹤清單總覽 (含即時價格)
- 個人化設定
  - 指標顯示設定
  - 通知設定
  - 指標參數調整
  - 預設模板 (極簡/標準/完整/短線)
- FastAPI Web API
  - 認證路由 (/auth)
  - 股票查詢 (/api/stock)
  - 加密貨幣查詢 (/api/crypto)
  - 追蹤清單管理 (/api/watchlist)
  - 設定管理 (/api/settings)
  - 市場情緒 (/api/market/sentiment)
  - Swagger 文件 (/docs)
- 資料模型
  - User (用戶)
  - Watchlist (追蹤清單)
  - UserIndicatorSettings (指標設定)
  - UserAlertSettings (通知設定)
  - UserIndicatorParams (參數設定)
  - Notification (通知記錄)

## [0.2.0] - 2025-01-05

### Added
- 圖表繪製服務 (chart_service.py)
  - 價格走勢圖 + 均線 + 布林通道
  - 成交量柱狀圖
  - RSI、MACD、KD 子圖
  - 均線交叉點標記
  - K線圖支援
- 加密貨幣支援
  - CoinGecko API 整合
  - BTC、ETH 價格追蹤
  - 幣圈技術指標 (MA7/25/99)
- 市場情緒指數
  - CNN Fear & Greed Index (美股)
  - Alternative.me (加密貨幣)
- CLI 新增指令
  - `sentiment` - 查詢市場情緒
  - `chart` - 生成技術分析圖表
  - 支援加密貨幣查詢 (BTC, ETH)

### Changed
- CLI 互動模式提示符改為 `代號>`
- 支援同時查詢股票和加密貨幣

## [0.1.0] - 2025-01-05

### Added
- 專案初始化
- Yahoo Finance 股價資料抓取
- SQLite 本地快取機制
- 技術指標計算引擎
  - 移動平均線 (MA20, MA50, MA200)
  - RSI 相對強弱指標
  - MACD 指數平滑異同移動平均
  - KD 隨機指標
  - 布林通道
  - OBV 能量潮指標
  - 成交量分析
- 訊號偵測系統
  - 均線黃金交叉/死亡交叉
  - 接近突破/跌破預警
  - RSI 超買超賣
  - MACD/KD 交叉
- 綜合評分系統
- CLI 命令列查詢介面
  - 互動模式
  - 單次查詢指令
  - 強制更新選項
