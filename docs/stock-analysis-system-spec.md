# 📈 多用戶選股分析系統 - 開發規格書

> 版本：1.0  
> 最後更新：2025-01

---

## 目錄

1. [專案概述](#1-專案概述)
2. [系統架構](#2-系統架構)
3. [資料來源](#3-資料來源)
4. [資料庫設計](#4-資料庫設計)
5. [功能模組](#5-功能模組)
6. [技術指標](#6-技術指標)
7. [用戶系統](#7-用戶系統)
8. [通知系統](#8-通知系統)
9. [圖表系統](#9-圖表系統)
10. [API 設計](#10-api-設計)
11. [技術選型](#11-技術選型)
12. [開發階段](#12-開發階段)

---

## 1. 專案概述

### 1.1 專案目標

建立一個支援多用戶的股票與加密貨幣技術分析平台，提供：

- 美股即時報價與技術指標分析
- 比特幣、以太幣價格追蹤
- 個人化追蹤清單
- 自訂技術指標與通知
- LINE 推播警報

### 1.2 核心特色

| 特色 | 說明 |
|------|------|
| 多用戶支援 | LINE 登入，每人獨立追蹤清單 |
| 共享資料庫 | 股價資料共用，減少 API 呼叫 |
| 彈性指標 | 用戶可自選要顯示/通知的指標 |
| 智能預警 | 突破、交叉、極端值自動推播 |
| 雙市場 | 同時支援美股與加密貨幣 |

### 1.3 支援資產

| 類型 | 標的 |
|------|------|
| 美股 | 所有 Yahoo Finance 支援的股票代號 |
| 加密貨幣 | BTC（比特幣）、ETH（以太幣） |

---

## 2. 系統架構

### 2.1 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                        前端介面                              │
│              (Web 應用程式 / LINE Bot)                       │
├─────────────────────────────────────────────────────────────┤
│                        API 層                                │
│    ├─ 用戶驗證 (LINE Login)                                  │
│    ├─ 追蹤清單管理                                           │
│    ├─ 股票/幣圈查詢                                          │
│    └─ 設定管理                                               │
├─────────────────────────────────────────────────────────────┤
│                      商業邏輯層                               │
│    ├─ 技術指標計算引擎                                        │
│    ├─ 訊號偵測引擎                                           │
│    ├─ 綜合評分系統                                           │
│    └─ 通知排程服務                                           │
├─────────────────────────────────────────────────────────────┤
│                       快取層                                  │
│    └─ 判斷讀取本地資料庫 或 抓取外部 API                       │
├─────────────────────────────────────────────────────────────┤
│                      資料庫層                                 │
│    ├─ 共享資料 (股價、幣價、情緒指數)                          │
│    └─ 私有資料 (用戶、追蹤清單、設定)                          │
├─────────────────────────────────────────────────────────────┤
│                    外部資料來源                               │
│    ├─ Yahoo Finance (美股)                                   │
│    ├─ CoinGecko (加密貨幣)                                   │
│    ├─ CNN Fear & Greed (美股情緒)                            │
│    ├─ Alternative.me (幣圈情緒)                              │
│    └─ LINE Login API (用戶驗證)                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 資料流程

```
用戶查詢 AAPL
      │
      ▼
  檢查本地資料庫
      │
      ├─ 有資料 且 今日已更新 → 直接使用
      │
      └─ 無資料 或 過期 → 抓 Yahoo Finance
                              │
                              ▼
                         寫入資料庫
                              │
                              ▼
                         計算技術指標
                              │
                              ▼
                      根據用戶設定過濾
                              │
                              ▼
                         回傳結果
```

---

## 3. 資料來源

### 3.1 美股資料

| 來源 | 用途 | 取得方式 |
|------|------|----------|
| Yahoo Finance | 股價、成交量、歷史資料 | yfinance Python 套件 |
| CNN Fear & Greed | 美股市場情緒指數 | 網頁爬蟲 或 第三方 API |

**yfinance 可取得欄位：**
- Open, High, Low, Close, Volume
- 歷史資料（可取多年）
- 延遲約 15-20 分鐘

### 3.2 加密貨幣資料

| 來源 | 用途 | 取得方式 |
|------|------|----------|
| CoinGecko | BTC/ETH 價格、市值、成交量 | 免費公開 API |
| Alternative.me | 幣圈 Fear & Greed 指數 | 免費公開 API |

**CoinGecko API 端點：**
```
GET https://api.coingecko.com/api/v3/simple/price
    ?ids=bitcoin,ethereum
    &vs_currencies=usd
    &include_24hr_change=true
    &include_market_cap=true
    &include_24hr_vol=true
```

**Alternative.me API 端點：**
```
GET https://api.alternative.me/fng/
```

### 3.3 資料更新策略

| 資料類型 | 更新頻率 | 觸發方式 |
|----------|----------|----------|
| 美股股價 | 每日一次 | 美股收盤後 (約 UTC+8 05:00) |
| 加密貨幣 | 每小時 或 查詢時 | 排程 / 用戶查詢觸發 |
| 情緒指數 | 每日一次 | 排程任務 |

---

## 4. 資料庫設計

### 4.1 共享資料表

#### stock_prices（美股價格歷史）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵，自動遞增 |
| symbol | VARCHAR(10) | 股票代號 |
| date | DATE | 交易日期 |
| open | DECIMAL(12,4) | 開盤價 |
| high | DECIMAL(12,4) | 最高價 |
| low | DECIMAL(12,4) | 最低價 |
| close | DECIMAL(12,4) | 收盤價 |
| volume | BIGINT | 成交量 |
| updated_at | TIMESTAMP | 資料更新時間 |

**索引：**
- `idx_stock_symbol_date` ON (symbol, date)

---

#### crypto_prices（加密貨幣價格歷史）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵，自動遞增 |
| symbol | VARCHAR(10) | 幣種代號 (BTC/ETH) |
| date | DATE | 日期 |
| price | DECIMAL(18,8) | 價格 (USD) |
| volume_24h | DECIMAL(18,2) | 24 小時成交量 |
| market_cap | DECIMAL(18,2) | 市值 |
| updated_at | TIMESTAMP | 資料更新時間 |

**索引：**
- `idx_crypto_symbol_date` ON (symbol, date)

---

#### market_sentiment（市場情緒指數）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵，自動遞增 |
| date | DATE | 日期 |
| market | VARCHAR(10) | stock / crypto |
| value | INTEGER | 指數值 (0-100) |
| classification | VARCHAR(20) | 文字分類 |
| updated_at | TIMESTAMP | 資料更新時間 |

---

### 4.2 私有資料表

#### users（用戶資料）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵，自動遞增 |
| line_user_id | VARCHAR(50) | LINE 唯一識別碼 |
| display_name | VARCHAR(100) | LINE 顯示名稱 |
| picture_url | VARCHAR(500) | LINE 頭像網址 |
| created_at | TIMESTAMP | 註冊時間 |
| last_login | TIMESTAMP | 最後登入時間 |

**索引：**
- `idx_users_line_id` UNIQUE ON (line_user_id)

---

#### watchlists（追蹤清單）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵，自動遞增 |
| user_id | INTEGER | 用戶 ID (FK → users.id) |
| symbol | VARCHAR(10) | 股票/幣種代號 |
| asset_type | VARCHAR(10) | stock / crypto |
| note | VARCHAR(200) | 自訂備註（選填） |
| added_at | TIMESTAMP | 加入時間 |

**索引：**
- `idx_watchlist_user` ON (user_id)
- `idx_watchlist_unique` UNIQUE ON (user_id, symbol, asset_type)

---

#### user_indicator_settings（指標顯示設定）

| 欄位 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| user_id | INTEGER | - | 用戶 ID (PK, FK) |
| show_ma | BOOLEAN | true | 顯示均線 |
| show_rsi | BOOLEAN | true | 顯示 RSI |
| show_macd | BOOLEAN | true | 顯示 MACD |
| show_kd | BOOLEAN | false | 顯示 KD |
| show_bollinger | BOOLEAN | true | 顯示布林通道 |
| show_obv | BOOLEAN | false | 顯示 OBV |
| show_volume | BOOLEAN | true | 顯示成交量 |

---

#### user_alert_settings（通知設定）

| 欄位 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| user_id | INTEGER | - | 用戶 ID (PK, FK) |
| alert_ma_cross | BOOLEAN | true | 均線交叉通知 |
| alert_ma_breakout | BOOLEAN | true | 均線突破通知 |
| alert_rsi | BOOLEAN | true | RSI 超買超賣通知 |
| alert_macd | BOOLEAN | true | MACD 交叉通知 |
| alert_kd | BOOLEAN | false | KD 交叉通知 |
| alert_bollinger | BOOLEAN | false | 布林突破通知 |
| alert_volume | BOOLEAN | false | 量能異常通知 |
| alert_sentiment | BOOLEAN | true | 情緒極端通知 |

---

#### user_indicator_params（指標參數設定）

| 欄位 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| user_id | INTEGER | - | 用戶 ID (PK, FK) |
| ma_short | INTEGER | 20 | 短均線週期 |
| ma_mid | INTEGER | 50 | 中均線週期 |
| ma_long | INTEGER | 200 | 長均線週期 |
| rsi_period | INTEGER | 14 | RSI 週期 |
| rsi_overbought | INTEGER | 70 | RSI 超買門檻 |
| rsi_oversold | INTEGER | 30 | RSI 超賣門檻 |
| macd_fast | INTEGER | 12 | MACD 快線週期 |
| macd_slow | INTEGER | 26 | MACD 慢線週期 |
| macd_signal | INTEGER | 9 | MACD 訊號線週期 |
| kd_period | INTEGER | 9 | KD 週期 |
| bollinger_period | INTEGER | 20 | 布林通道週期 |
| bollinger_std | DECIMAL(3,1) | 2.0 | 布林標準差倍數 |
| breakout_threshold | DECIMAL(4,2) | 2.00 | 突破預警門檻 (%) |
| volume_alert_ratio | DECIMAL(3,1) | 2.0 | 量比警戒倍數 |

---

#### notifications（通知記錄）

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵，自動遞增 |
| user_id | INTEGER | 用戶 ID (FK) |
| symbol | VARCHAR(10) | 股票/幣種代號 |
| asset_type | VARCHAR(10) | stock / crypto |
| alert_type | VARCHAR(30) | 通知類型（見下表） |
| indicator | VARCHAR(20) | 相關指標 |
| message | TEXT | 通知內容 |
| price_at_trigger | DECIMAL(18,8) | 觸發時價格 |
| triggered_at | TIMESTAMP | 觸發時間 |
| sent | BOOLEAN | 是否已發送 |

**alert_type 類型：**
- `ma_golden_cross` - 均線黃金交叉
- `ma_death_cross` - 均線死亡交叉
- `approaching_breakout` - 接近向上突破
- `approaching_breakdown` - 接近向下跌破
- `breakout` - 已突破
- `breakdown` - 已跌破
- `rsi_overbought` - RSI 超買
- `rsi_oversold` - RSI 超賣
- `macd_golden_cross` - MACD 黃金交叉
- `macd_death_cross` - MACD 死亡交叉
- `kd_golden_cross` - KD 黃金交叉
- `kd_death_cross` - KD 死亡交叉
- `bollinger_breakout` - 布林上軌突破
- `bollinger_breakdown` - 布林下軌跌破
- `volume_surge` - 成交量暴增
- `sentiment_extreme_fear` - 極度恐懼
- `sentiment_extreme_greed` - 極度貪婪

---

## 5. 功能模組

### 5.1 股票/加密貨幣查詢

#### 輸入
- 股票代號 (如 AAPL、TSLA) 或幣種 (BTC、ETH)

#### 輸出資料

**價格資訊：**
| 項目 | 說明 |
|------|------|
| 現價 | 最新收盤價/即時價 |
| 52 週最高 | 過去一年最高價（美股）|
| 52 週最低 | 過去一年最低價（美股）|
| ATH | 歷史最高價（加密貨幣）|
| 離高點 % | 現價距離高點跌幅 |
| 離低點 % | 現價距離低點漲幅 |
| 市值 | Market Cap |

**漲跌幅：**
| 項目 | 計算方式 |
|------|----------|
| 日漲跌 | 今日 vs 昨日 |
| 週漲跌 | 今日 vs 5 交易日前 |
| 月漲跌 | 今日 vs 20 交易日前 |
| 季漲跌 | 今日 vs 60 交易日前 |
| 年漲跌 | 今日 vs 250 交易日前 |
| YTD | 今年以來 |

**成交量：**
| 項目 | 說明 |
|------|------|
| 今日成交量 | 當日成交量 |
| 20 日均量 | 近 20 日平均成交量 |
| 量比 | 今日量 / 均量 |

---

### 5.2 追蹤清單管理

| 操作 | 說明 |
|------|------|
| 新增 | 加入股票/加密貨幣到個人清單 |
| 刪除 | 從清單移除 |
| 列表 | 顯示所有追蹤的標的 |
| 總覽 | 一次顯示所有追蹤標的的即時狀態 |
| 備註 | 為標的加入自訂備註 |

---

### 5.3 市場情緒總覽

| 市場 | 來源 | 數值範圍 |
|------|------|----------|
| 美股 | CNN Fear & Greed Index | 0-100 |
| 幣圈 | Alternative.me | 0-100 |

**情緒分級：**
| 數值 | 分類 | 意義 |
|------|------|------|
| 0-25 | 極度恐懼 | 可能買點 |
| 26-45 | 恐懼 | 偏謹慎 |
| 46-55 | 中性 | 觀望 |
| 56-75 | 貪婪 | 偏樂觀 |
| 76-100 | 極度貪婪 | 可能賣點 |

---

### 5.4 設定管理

**指標顯示設定：**
- 勾選要在報告中顯示的指標
- 預設模板：極簡 / 標準 / 完整 / 短線 / 自訂

**通知設定：**
- 勾選要接收推播的訊號類型
- 設定預警門檻（如接近均線 2%）

**參數調整：**
- 自訂均線週期、RSI 週期等參數

---

## 6. 技術指標

### 6.1 移動平均線 (MA)

**定義：** 過去 N 日收盤價的簡單平均

**常用週期：**
| 市場 | 短期 | 中期 | 長期 |
|------|------|------|------|
| 美股 | MA20 | MA50 | MA200 |
| 幣圈 | MA7 | MA25 | MA99 |

**計算公式：**
```
MA(N) = (P1 + P2 + ... + PN) / N
其中 P 為收盤價
```

**訊號：**
| 訊號 | 條件 | 意義 |
|------|------|------|
| 黃金交叉 | 短均線由下往上穿越長均線 | 偏多 |
| 死亡交叉 | 短均線由上往下穿越長均線 | 偏空 |
| 多頭排列 | 價 > 短均 > 中均 > 長均 | 強勢 |
| 空頭排列 | 價 < 短均 < 中均 < 長均 | 弱勢 |

**交叉判斷邏輯：**
```python
# 黃金交叉
yesterday: MA_short < MA_long
today: MA_short > MA_long

# 死亡交叉
yesterday: MA_short > MA_long
today: MA_short < MA_long
```

---

### 6.2 RSI（相對強弱指標）

**定義：** 衡量價格漲跌力道的比例

**預設週期：** 14 日

**計算公式：**
```
RS = 平均漲幅 / 平均跌幅
RSI = 100 - (100 / (1 + RS))
```

**訊號：**
| 數值 | 狀態 | 意義 |
|------|------|------|
| > 70 | 超買 | 可能回檔 |
| < 30 | 超賣 | 可能反彈 |
| 50 | 中性 | 多空平衡 |

**進階訊號：**
- RSI 背離：價格創新高但 RSI 未創新高 → 弱勢警告

---

### 6.3 MACD（指數平滑異同移動平均）

**定義：** 短期與長期 EMA 的差距及其變化

**預設參數：** (12, 26, 9)

**組成：**
| 線條 | 計算 |
|------|------|
| DIF | EMA(12) - EMA(26) |
| MACD (DEA) | DIF 的 EMA(9) |
| 柱狀體 | DIF - MACD |

**訊號：**
| 訊號 | 條件 | 強度 |
|------|------|------|
| 黃金交叉 + 零軸上方 | DIF 上穿 MACD，且 > 0 | 強勢買點 |
| 黃金交叉 + 零軸下方 | DIF 上穿 MACD，但 < 0 | 弱勢反彈 |
| 死亡交叉 + 零軸上方 | DIF 下穿 MACD，但 > 0 | 回檔修正 |
| 死亡交叉 + 零軸下方 | DIF 下穿 MACD，且 < 0 | 強勢賣點 |

---

### 6.4 KD（隨機指標）

**定義：** 衡量收盤價在一段時間內的相對位置

**預設參數：** (9, 3, 3)

**計算公式：**
```
RSV = (今日收盤 - 9日最低) / (9日最高 - 9日最低) × 100
K = 2/3 × 昨日K + 1/3 × RSV
D = 2/3 × 昨日D + 1/3 × K
```

**訊號：**
| 訊號 | 條件 | 意義 |
|------|------|------|
| K > 80 | 超買區 | 留意回檔 |
| K < 20 | 超賣區 | 留意反彈 |
| K 上穿 D | 黃金交叉 | 買進訊號 |
| K 下穿 D | 死亡交叉 | 賣出訊號 |
| 低檔鈍化 | K 持續 < 20 | 極弱勢，勿接刀 |

---

### 6.5 布林通道 (Bollinger Bands)

**定義：** 以移動平均為中心，上下加減標準差形成通道

**預設參數：** 週期 20，標準差 2 倍

**計算公式：**
```
中軌 = MA(20)
上軌 = MA(20) + 2 × 標準差
下軌 = MA(20) - 2 × 標準差
帶寬 = (上軌 - 下軌) / 中軌
```

**訊號：**
| 訊號 | 條件 | 意義 |
|------|------|------|
| 觸及上軌 | 價格 ≥ 上軌 | 短線強勢，可能回檔 |
| 觸及下軌 | 價格 ≤ 下軌 | 短線弱勢，可能反彈 |
| 通道收窄 | 帶寬創新低 | 盤整，即將變盤 |
| 通道擴張 | 帶寬放大 | 趨勢進行中 |

---

### 6.6 OBV（能量潮指標）

**定義：** 累積成交量，判斷資金流向

**計算邏輯：**
```python
if 今日收盤 > 昨日收盤:
    OBV = 昨日OBV + 今日成交量
elif 今日收盤 < 昨日收盤:
    OBV = 昨日OBV - 今日成交量
else:
    OBV = 昨日OBV
```

**訊號：**
| 訊號 | 條件 | 意義 |
|------|------|------|
| OBV 上升 | OBV 持續創新高 | 資金流入 |
| OBV 下降 | OBV 持續破底 | 資金流出 |
| 背離 | 價漲但 OBV 不漲 | 漲勢可能衰竭 |

---

### 6.7 成交量分析

**指標：**
| 指標 | 計算 | 意義 |
|------|------|------|
| 今日量 | 當日成交量 | - |
| 20 日均量 | 近 20 日平均 | 基準量 |
| 量比 | 今日量 / 均量 | 相對強度 |

**訊號：**
| 量比 | 狀態 | 意義 |
|------|------|------|
| > 2.0 | 爆量 | 關注後續方向 |
| 1.0 - 2.0 | 正常偏多 | 量價配合 |
| 0.5 - 1.0 | 縮量 | 觀望氣氛 |
| < 0.5 | 極度縮量 | 冷門或盤整 |

---

### 6.8 綜合評分系統

根據多指標共振給予評分：

**買進訊號評分：**
| 條件 | 加分 |
|------|------|
| 多頭排列 | +1 |
| RSI 超賣回升 | +1 |
| MACD 黃金交叉 | +1 |
| KD 黃金交叉 | +1 |
| 布林下軌支撐 | +1 |
| 量能放大 | +1 |
| OBV 上升 | +1 |

**賣出訊號評分：**
| 條件 | 加分 |
|------|------|
| 空頭排列 | +1 |
| RSI 超買下彎 | +1 |
| MACD 死亡交叉 | +1 |
| KD 死亡交叉 | +1 |
| 跌破布林中軌 | +1 |
| 量價背離 | +1 |
| OBV 下降 | +1 |

**評分等級：**
| 分數 | 等級 | 建議 |
|------|------|------|
| 5-7 | ⭐⭐⭐⭐⭐ | 強烈訊號 |
| 3-4 | ⭐⭐⭐⭐ | 中等訊號 |
| 1-2 | ⭐⭐ | 弱訊號 |
| 0 | - | 無明顯訊號 |

---

## 7. 用戶系統

### 7.1 LINE Login 流程

```
┌──────────────────────────────────────────────────────────┐
│                    LINE Login 流程                        │
└──────────────────────────────────────────────────────────┘

用戶點擊「LINE 登入」
          │
          ▼
    跳轉至 LINE 授權頁面
    https://access.line.me/oauth2/v2.1/authorize
          │
          ▼
     用戶同意授權
          │
          ▼
    LINE 回傳 authorization code
          │
          ▼
    後端用 code 換取 access_token
    POST https://api.line.me/oauth2/v2.1/token
          │
          ▼
    用 access_token 取得用戶資料
    GET https://api.line.me/v2/profile
          │
          ├─ line_user_id
          ├─ displayName
          └─ pictureUrl
          │
          ▼
    ┌─ 新用戶 → 建立帳號，初始化預設設定
    │
    └─ 舊用戶 → 更新 last_login
          │
          ▼
    發送 JWT Token 給前端
          │
          ▼
      登入完成 ✅
```

### 7.2 LINE Login 所需設定

1. 建立 LINE Login Channel（LINE Developers Console）
2. 設定 Callback URL
3. 取得 Channel ID 和 Channel Secret

### 7.3 JWT Token 設計

**Payload：**
```json
{
  "user_id": 123,
  "line_user_id": "Uxxxxxxxxxxxx",
  "display_name": "用戶名稱",
  "exp": 1234567890
}
```

**Token 有效期：** 7 天

---

## 8. 通知系統

### 8.1 通知類型

#### 均線相關

| 類型 | 條件 | 訊息範例 |
|------|------|----------|
| 接近突破 | 價格在均線下方，差距 < 門檻 | "AAPL 接近突破 MA50 ⬆️" |
| 接近跌破 | 價格在均線上方，差距 < 門檻 | "AAPL 接近跌破 MA20 ⬇️" |
| 已突破 | 價格由下往上穿越均線 | "AAPL 已突破 MA50 ✅" |
| 已跌破 | 價格由上往下穿越均線 | "AAPL 已跌破 MA20 ❌" |
| 黃金交叉 | 短均線上穿長均線 | "AAPL MA20 黃金交叉 MA50 🟢" |
| 死亡交叉 | 短均線下穿長均線 | "AAPL MA20 死亡交叉 MA50 🔴" |

#### 其他指標

| 類型 | 條件 | 訊息範例 |
|------|------|----------|
| RSI 超買 | RSI > 超買門檻 | "NVDA RSI 達 75，進入超買區 ⚠️" |
| RSI 超賣 | RSI < 超賣門檻 | "TSLA RSI 跌至 25，進入超賣區 🟢" |
| MACD 黃金交叉 | DIF 上穿 MACD | "MSFT MACD 黃金交叉 🟢" |
| MACD 死亡交叉 | DIF 下穿 MACD | "GOOGL MACD 死亡交叉 🔴" |
| 量能異常 | 量比 > 門檻 | "AMD 成交量暴增 (量比 2.5) 📊" |
| 情緒極端 | 指數 < 20 或 > 80 | "幣圈極度恐懼 (18)，留意機會 😱" |

### 8.2 通知流程

```
排程任務觸發（每日收盤後）
          │
          ▼
    載入所有需檢查的標的
    （所有用戶追蹤清單的聯集）
          │
          ▼
    更新價格資料
          │
          ▼
    計算技術指標
          │
          ▼
    ┌─────────────────────────┐
    │  遍歷每個用戶           │
    │    │                   │
    │    ▼                   │
    │  遍歷用戶的追蹤清單     │
    │    │                   │
    │    ▼                   │
    │  根據用戶的通知設定     │
    │  檢查是否觸發條件       │
    │    │                   │
    │    ▼                   │
    │  ┌─ 未觸發 → 略過      │
    │  │                     │
    │  └─ 觸發 → 檢查是否    │
    │            已通知過    │
    │              │         │
    │    ┌─ 是 → 略過       │
    │    │                   │
    │    └─ 否 → 加入通知    │
    │             佇列       │
    └─────────────────────────┘
          │
          ▼
    批次發送 LINE 推播
          │
          ▼
    更新通知記錄
```

### 8.3 避免重複通知

**規則：**
1. 同一訊號 24 小時內不重複發送
2. 價格穿越後（突破/跌破），清除「接近」的通知記錄
3. 合併通知：多檔同時觸發時，合併為一則訊息

### 8.4 LINE 推播

**使用 LINE Messaging API：**
```
POST https://api.line.me/v2/bot/message/push
```

**所需設定：**
1. 建立 Messaging API Channel
2. 取得 Channel Access Token

---

## 9. 圖表系統

### 9.1 圖表類型

| 圖表 | 用途 |
|------|------|
| 價格走勢圖 | 顯示收盤價折線 + 均線 |
| K 線圖 | 顯示 OHLC + 均線 |
| 成交量圖 | 柱狀圖顯示每日成交量 |
| 指標子圖 | RSI、MACD、KD 等獨立顯示 |
| 情緒走勢圖 | Fear & Greed 歷史走勢 |

### 9.2 圖表元素

**主圖（價格）：**
- 收盤價折線 或 K 線
- MA20（藍色）
- MA50（橙色）
- MA200（紅色）
- 布林通道（淺灰色區域）
- 交叉點標記（圓點）

**副圖（指標）：**
- 成交量柱狀圖
- RSI 折線 + 超買超賣線
- MACD 柱狀圖 + DIF/MACD 線
- KD 線

### 9.3 使用者可自訂項目

```
┌─────────────────────────────────┐
│        圖表顯示設定              │
├─────────────────────────────────┤
│  時間範圍: [1M] [3M] [6M] [1Y]  │
│                                 │
│  主圖:                          │
│    ☑ 收盤價                     │
│    ☐ K 線                       │
│    ☑ MA20 / MA50 / MA200        │
│    ☑ 布林通道                   │
│    ☑ 標記交叉點                 │
│                                 │
│  副圖:                          │
│    ☑ 成交量                     │
│    ☐ RSI                        │
│    ☐ MACD                       │
│    ☐ KD                         │
└─────────────────────────────────┘
```

### 9.4 技術實作

**推薦套件：** matplotlib + mplfinance

**輸出格式：** PNG 圖片

---

## 10. API 設計

### 10.1 API 端點總覽

#### 認證

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/auth/line` | 導向 LINE 登入 |
| GET | `/auth/line/callback` | LINE 登入回調 |
| POST | `/auth/logout` | 登出 |

#### 股票/加密貨幣

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/stock/{symbol}` | 查詢單一股票 |
| GET | `/api/crypto/{symbol}` | 查詢單一加密貨幣 |
| GET | `/api/market/sentiment` | 取得市場情緒 |
| GET | `/api/stock/{symbol}/chart` | 取得股票圖表 |
| GET | `/api/crypto/{symbol}/chart` | 取得加密貨幣圖表 |

#### 追蹤清單

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/watchlist` | 取得追蹤清單 |
| POST | `/api/watchlist` | 新增追蹤標的 |
| DELETE | `/api/watchlist/{id}` | 刪除追蹤標的 |
| GET | `/api/watchlist/overview` | 追蹤清單總覽 |

#### 設定

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/settings/indicators` | 取得指標設定 |
| PUT | `/api/settings/indicators` | 更新指標設定 |
| GET | `/api/settings/alerts` | 取得通知設定 |
| PUT | `/api/settings/alerts` | 更新通知設定 |
| GET | `/api/settings/params` | 取得參數設定 |
| PUT | `/api/settings/params` | 更新參數設定 |
| POST | `/api/settings/template` | 套用預設模板 |

---

### 10.2 API 回應格式

#### 成功回應

```json
{
  "success": true,
  "data": { ... }
}
```

#### 錯誤回應

```json
{
  "success": false,
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "找不到此股票代號"
  }
}
```

---

### 10.3 主要 API 詳細規格

#### GET /api/stock/{symbol}

**回應：**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "asset_type": "stock",
    "price": {
      "current": 195.50,
      "high_52w": 199.62,
      "low_52w": 164.08,
      "from_high_pct": -2.07,
      "from_low_pct": 19.15
    },
    "change": {
      "day": 1.25,
      "week": 3.42,
      "month": 8.15,
      "quarter": 12.30,
      "year": 48.25,
      "ytd": 5.60
    },
    "volume": {
      "today": 52300000,
      "avg_20d": 48500000,
      "ratio": 1.08
    },
    "indicators": {
      "ma": {
        "ma20": 192.30,
        "ma50": 188.75,
        "ma200": 178.20,
        "alignment": "bullish",
        "price_vs_ma20": "above",
        "price_vs_ma50": "above",
        "price_vs_ma200": "above"
      },
      "rsi": {
        "value": 62.5,
        "status": "neutral"
      },
      "macd": {
        "dif": 2.35,
        "macd": 1.98,
        "histogram": 0.37,
        "status": "bullish"
      },
      "kd": {
        "k": 68.5,
        "d": 62.3,
        "status": "neutral_high"
      },
      "bollinger": {
        "upper": 198.50,
        "middle": 192.30,
        "lower": 186.10,
        "position": "upper_half"
      },
      "obv": {
        "trend": "rising"
      }
    },
    "signals": {
      "recent": [
        {
          "date": "2025-01-10",
          "type": "ma_golden_cross",
          "description": "MA20 黃金交叉 MA50"
        }
      ]
    },
    "score": {
      "buy": 4,
      "sell": 0,
      "rating": "bullish"
    },
    "updated_at": "2025-01-15T05:30:00Z"
  }
}
```

#### GET /api/watchlist/overview

**回應：**
```json
{
  "success": true,
  "data": {
    "stocks": [
      {
        "symbol": "AAPL",
        "price": 195.50,
        "change_day": 1.25,
        "ma_alignment": "bullish",
        "score": 4
      }
    ],
    "crypto": [
      {
        "symbol": "BTC",
        "price": 67850,
        "change_24h": 2.35,
        "ma_alignment": "bullish",
        "score": 3
      }
    ],
    "sentiment": {
      "stock": {
        "value": 45,
        "classification": "neutral"
      },
      "crypto": {
        "value": 32,
        "classification": "fear"
      }
    }
  }
}
```

---

## 11. 技術選型

### 11.1 後端

| 項目 | 選擇 | 理由 |
|------|------|------|
| 語言 | Python 3.10+ | 豐富的金融分析套件 |
| 框架 | FastAPI | 現代、高效能、自動 API 文件 |
| 資料庫 | PostgreSQL | 穩定、支援多用戶併發 |
| ORM | SQLAlchemy | 成熟穩定 |
| 任務排程 | APScheduler 或 Celery | 定時更新資料 |
| 快取 | Redis（選配） | 加速頻繁查詢 |

### 11.2 資料處理

| 項目 | 套件 |
|------|------|
| 股價抓取 | yfinance |
| 數據處理 | pandas, numpy |
| 技術指標 | ta-lib 或 pandas-ta |
| 圖表繪製 | matplotlib, mplfinance |

### 11.3 外部服務

| 項目 | 服務 |
|------|------|
| 用戶驗證 | LINE Login API |
| 推播通知 | LINE Messaging API |
| 股價資料 | Yahoo Finance |
| 幣價資料 | CoinGecko API |
| 情緒指數 | CNN, Alternative.me |

### 11.4 部署

| 項目 | 建議選項 |
|------|----------|
| 主機 | Render / Railway / DigitalOcean / AWS |
| 資料庫 | Supabase / Railway PostgreSQL / AWS RDS |
| 排程 | 主機內建 或 外部 Cron 服務 |

### 11.5 前端（選配）

| 方案 | 說明 |
|------|------|
| 純 LINE Bot | 最輕量，用指令互動 |
| Web 應用 | React / Vue + REST API |
| 混合 | Web 為主，LINE Bot 推播 |

---

## 12. 開發階段

### 階段一：核心基礎

**目標：** 單機可運行的股票分析工具

**功能：**
- [ ] 股票資料抓取（yfinance）
- [ ] 本地 SQLite 快取
- [ ] 基本技術指標（MA20/50/200）
- [ ] 命令列查詢介面

**產出：** 可用 CLI 查詢股票資訊

---

### 階段二：完整指標

**目標：** 完整的技術分析功能

**功能：**
- [ ] RSI 計算與判讀
- [ ] MACD 計算與判讀
- [ ] KD 計算與判讀
- [ ] 布林通道
- [ ] OBV
- [ ] 成交量分析
- [ ] 綜合評分系統
- [ ] 圖表繪製

**產出：** 完整技術分析報告與圖表

---

### 階段三：加密貨幣

**目標：** 整合幣圈資料

**功能：**
- [ ] CoinGecko API 整合
- [ ] BTC/ETH 價格追蹤
- [ ] 幣圈技術指標
- [ ] 市場情緒指數（雙市場）

**產出：** 股票 + 加密貨幣統一分析

---

### 階段四：用戶系統

**目標：** 多用戶支援

**功能：**
- [ ] 資料庫遷移至 PostgreSQL
- [ ] LINE Login 整合
- [ ] 用戶資料表建立
- [ ] 追蹤清單功能
- [ ] JWT 驗證

**產出：** 可登入、有個人追蹤清單

---

### 階段五：個人化設定

**目標：** 用戶自訂體驗

**功能：**
- [ ] 指標顯示設定
- [ ] 通知設定
- [ ] 參數調整
- [ ] 預設模板

**產出：** 完整的設定系統

---

### 階段六：通知系統

**目標：** 自動推播警報

**功能：**
- [ ] LINE Messaging API 整合
- [ ] 排程任務建立
- [ ] 訊號偵測引擎
- [ ] 通知記錄與防重複

**產出：** 自動推播技術訊號

---

### 階段七：Web 介面（選配）

**目標：** 提供網頁操作介面

**功能：**
- [ ] 前端框架建立
- [ ] 登入頁面
- [ ] 儀表板頁面
- [ ] 設定頁面
- [ ] 互動式圖表

**產出：** 完整 Web 應用

---

### 階段八：優化與上線

**目標：** 正式環境部署

**功能：**
- [ ] 效能優化
- [ ] 錯誤處理完善
- [ ] 日誌系統
- [ ] 監控與告警
- [ ] 正式環境部署

**產出：** 穩定運行的生產系統

---

## 附錄

### A. 環境變數

```bash
# 資料庫
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# LINE Login
LINE_LOGIN_CHANNEL_ID=your_channel_id
LINE_LOGIN_CHANNEL_SECRET=your_channel_secret
LINE_LOGIN_CALLBACK_URL=https://your-domain.com/auth/line/callback

# LINE Messaging
LINE_MESSAGING_CHANNEL_ACCESS_TOKEN=your_access_token

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_EXPIRE_DAYS=7

# 應用程式
APP_ENV=development
APP_DEBUG=true
```

### B. 專案目錄結構

```
stock-analysis/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 設定檔
│   ├── database.py          # 資料庫連線
│   │
│   ├── models/              # 資料模型
│   │   ├── user.py
│   │   ├── watchlist.py
│   │   ├── stock_price.py
│   │   ├── crypto_price.py
│   │   ├── sentiment.py
│   │   ├── notification.py
│   │   └── settings.py
│   │
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py
│   │   ├── stock.py
│   │   ├── crypto.py
│   │   └── settings.py
│   │
│   ├── routers/             # API 路由
│   │   ├── auth.py
│   │   ├── stock.py
│   │   ├── crypto.py
│   │   ├── watchlist.py
│   │   └── settings.py
│   │
│   ├── services/            # 商業邏輯
│   │   ├── stock_service.py
│   │   ├── crypto_service.py
│   │   ├── indicator_service.py
│   │   ├── chart_service.py
│   │   ├── notification_service.py
│   │   └── line_service.py
│   │
│   ├── data_sources/        # 外部資料來源
│   │   ├── yahoo_finance.py
│   │   ├── coingecko.py
│   │   ├── cnn_fear_greed.py
│   │   └── alternative_me.py
│   │
│   └── tasks/               # 排程任務
│       ├── update_prices.py
│       ├── update_sentiment.py
│       └── check_alerts.py
│
├── tests/                   # 測試
├── migrations/              # 資料庫遷移
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### C. 參考資源

- [yfinance 文件](https://github.com/ranaroussi/yfinance)
- [CoinGecko API 文件](https://www.coingecko.com/en/api/documentation)
- [LINE Login 文件](https://developers.line.biz/en/docs/line-login/)
- [LINE Messaging API 文件](https://developers.line.biz/en/docs/messaging-api/)
- [FastAPI 文件](https://fastapi.tiangolo.com/)
- [pandas-ta 技術指標](https://github.com/twopirllc/pandas-ta)

---

> 本文件為開發規格書，實際開發時可依需求調整細節。
