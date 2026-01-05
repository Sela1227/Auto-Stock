# Changelog

所有重要的變更都會記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
版本號遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

## [Unreleased]

### Planned
- LINE Messaging 推播通知
- Web 前端介面

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
