# SELA 快取優化（四大指數 + 恐懼貪婪指數）

## 📋 修改目標

| 項目 | 原本 | 修改後 |
|------|------|--------|
| 四大指數載入 | DB → 沒有就查 Yahoo API | **只查 DB** |
| 恐懼貪婪載入 | DB → 過期就查外部 API | **只查 DB** |
| 數字變動時機 | 每次載入可能變 | **排程/手動更新才變** |

---

## 🔧 修改步驟

### 方法一：使用腳本（推薦）

```bash
# 1. 上傳 fix_cache_optimization.py 到專案根目錄
# 2. 執行腳本
python3 fix_cache_optimization.py

# 3. 部署
git add app/services/market_service.py
git commit -m "快取優化：指數和情緒只讀DB"
git push origin main
```

### 方法二：手動修改

**檔案**: `app/services/market_service.py`

---

### 修改 1：四大指數 `get_latest_indices`

**找到** `get_latest_indices` 方法，**整個方法替換為**:

```python
    def get_latest_indices(self) -> Dict[str, Any]:
        """取得四大指數最新資料（🆕 只從資料庫讀取，排程才更新）"""
        result = {}
        
        for symbol, info in INDEX_SYMBOLS.items():
            try:
                stmt = (
                    select(IndexPrice)
                    .where(IndexPrice.symbol == symbol)
                    .order_by(desc(IndexPrice.date))
                    .limit(1)
                )
                latest = self.db.execute(stmt).scalar_one_or_none()
                
                if latest:
                    result[symbol] = latest.to_dict()
                    logger.debug(f"📦 指數快取: {symbol} = {latest.close}")
                else:
                    # 🆕 沒有快取時回傳 None，不查 API
                    logger.warning(f"⚠️ 指數 {symbol} 無快取資料，請執行更新")
                    result[symbol] = {
                        "symbol": symbol,
                        "name": info["name"],
                        "name_zh": info["name_zh"],
                        "date": None,
                        "close": None,
                        "change": None,
                        "change_pct": None,
                    }
            except Exception as e:
                logger.error(f"讀取指數 {symbol} 失敗: {e}")
                result[symbol] = {
                    "symbol": symbol,
                    "name": info["name"],
                    "name_zh": info["name_zh"],
                    "date": None,
                    "close": None,
                    "change": None,
                    "change_pct": None,
                }
        
        return result
```

---

### 修改 2：恐懼貪婪指數 `get_latest_sentiment`

**找到** `get_latest_sentiment` 方法，**整個方法替換為**:

```python
    def get_latest_sentiment(self) -> Dict[str, Any]:
        """
        取得最新的市場情緒（🆕 只從資料庫讀取，排程才更新）
        
        - 只從資料庫讀取，不主動查外部 API
        - 資料庫沒有或過期時回傳 None
        - 排程或手動更新時才會查 API
        """
        result = {}
        
        for market in ["stock", "crypto"]:
            try:
                stmt = (
                    select(MarketSentiment)
                    .where(MarketSentiment.market == market)
                    .order_by(desc(MarketSentiment.date))
                    .limit(1)
                )
                latest = self.db.execute(stmt).scalar_one_or_none()
                
                if latest:
                    result[market] = latest.to_dict()
                    logger.debug(f"📦 情緒快取: {market} = {latest.value}")
                else:
                    # 🆕 沒有快取時回傳 None，不查 API
                    logger.warning(f"⚠️ 情緒 {market} 無快取資料，請執行更新")
                    result[market] = {
                        "market": market,
                        "value": None,
                        "label": "無資料",
                        "date": None,
                    }
            except Exception as e:
                logger.error(f"讀取情緒 {market} 失敗: {e}")
                result[market] = {
                    "market": market,
                    "value": None,
                    "label": "錯誤",
                    "date": None,
                }
        
        return result
```

---

## ✅ 驗證

部署後進入儀表板，檢查 Railway log：

```
✅ 應該看到: 📦 指數快取: ^GSPC = 5930.85
✅ 應該看到: 📦 情緒快取: stock = 45
❌ 不應看到: 從 API 取得 / 從 API 更新成功
```

---

## 📝 注意事項

1. **首次部署**：如果資料庫沒有資料，儀表板會顯示「--」或「無資料」
2. **手動更新**：管理員面板可手動觸發更新
3. **排程更新**：系統已設定每日多次情緒更新排程（早/午/晚）
