# SELA 管理員登入更新優化 - 修改指南

## 📋 修改目標

| 項目 | 原本行為 | 修改後 |
|------|---------|--------|
| 管理員登入觸發更新 | 無論何時都更新股票價格 | 只在股市開盤時間更新 |
| 加密貨幣價格更新 | 視為 24/7 開盤，頻繁更新 | 改為 3 小時更新一次 |

---

## 🔧 修改 1：管理員登入只在開盤時更新

### 📁 檔案：`app/routers/auth.py`

### 找到 `trigger_admin_updates` 函數（約第 5881 行），替換為：

```python
async def trigger_admin_updates():
    """
    管理員登入觸發的背景更新
    - 🆕 只在股市開盤時間更新股票價格
    - 更新市場情緒指數（不受時間限制）
    """
    from app.database import SessionLocal
    from app.services.price_cache_service import is_tw_market_open, is_us_market_open
    
    tw_open = is_tw_market_open()
    us_open = is_us_market_open()
    
    logger.info(f"🔄 管理員登入，檢查是否需要更新...")
    logger.info(f"   台股: {'開盤' if tw_open else '收盤'}, 美股: {'開盤' if us_open else '收盤'}")
    
    try:
        db = SessionLocal()
        
        # 1. 更新股票價格快取（只在開盤時）
        if tw_open or us_open:
            try:
                from app.services.price_cache_service import PriceCacheService
                cache_service = PriceCacheService(db)
                result = cache_service.update_all_prices()
                logger.info(f"✅ 股票價格更新完成: {result}")
            except Exception as e:
                logger.error(f"❌ 股票價格更新失敗: {e}")
        else:
            logger.info("💤 台股美股皆收盤，跳過股票價格更新")
        
        # 2. 更新市場情緒（總是更新）
        try:
            from app.services.market_service import market_service
            market_service.update_fear_greed()
            logger.info("✅ 市場情緒更新完成")
        except Exception as e:
            logger.error(f"❌ 市場情緒更新失敗: {e}")
        
        # 3. 抓取訂閱精選（如果有）
        try:
            from app.services.subscription_service import SubscriptionService
            sub_service = SubscriptionService(db)
            sub_result = sub_service.fetch_all_sources(backfill=False)
            logger.info(f"✅ 訂閱精選更新完成: {sub_result}")
        except Exception as e:
            logger.warning(f"⚠️ 訂閱精選更新跳過: {e}")
        
        db.close()
        logger.info("🎉 管理員自動更新完成")
        
    except Exception as e:
        logger.error(f"❌ 管理員自動更新失敗: {e}")
```

---

## 🔧 修改 2：加密貨幣改為 3 小時更新

### 📁 檔案：`app/services/price_cache_service.py`

### 2.1 修改 `is_market_open_for_symbol` 函數

找到（約第 18011 行）：
```python
def is_market_open_for_symbol(symbol: str) -> bool:
    """判斷該 symbol 的市場是否開盤"""
    market = get_symbol_market(symbol)
    
    if market == "crypto":
        return True  # 24/7
```

改為：
```python
def is_market_open_for_symbol(symbol: str) -> bool:
    """判斷該 symbol 的市場是否開盤"""
    market = get_symbol_market(symbol)
    
    if market == "crypto":
        return False  # 🆕 加密貨幣改為定時更新（3小時），不需要即時查詢
```

### 2.2 修改 `batch_update_crypto_prices` 方法

找到（約第 18147 行）：
```python
def batch_update_crypto_prices(self, symbols: List[str]) -> Dict[str, Any]:
    """批次更新加密貨幣價格"""
    if not symbols:
        return {"updated": 0, "failed": []}
```

改為：
```python
def batch_update_crypto_prices(self, symbols: List[str], force: bool = False) -> Dict[str, Any]:
    """批次更新加密貨幣價格（3小時快取）"""
    if not symbols:
        return {"updated": 0, "failed": [], "skipped": 0}
    
    # 🆕 檢查快取時間（3小時 = 180分鐘）
    CRYPTO_CACHE_MINUTES = 180
    
    if not force:
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(minutes=CRYPTO_CACHE_MINUTES)
        
        # 檢查是否有任何加密貨幣需要更新
        needs_update = []
        for symbol in symbols:
            cache = self.db.query(StockPriceCache).filter(
                StockPriceCache.symbol == symbol.upper()
            ).first()
            
            if not cache or cache.updated_at < cutoff:
                needs_update.append(symbol)
        
        if not needs_update:
            logger.info(f"💤 加密貨幣快取未過期（{CRYPTO_CACHE_MINUTES}分鐘內），跳過更新")
            return {"updated": 0, "failed": [], "skipped": len(symbols)}
        
        symbols = needs_update
        logger.info(f"🔄 {len(symbols)} 個加密貨幣需要更新")
```

---

## 🔧 修改 3：排程任務優化（可選）

### 📁 檔案：`app/tasks/price_cache_task.py`

在 `run_update` 方法中，確保加密貨幣不會每 30 分鐘都更新：

找到類似這段邏輯：
```python
# 如果所有股市都收盤，只更新加密貨幣
if not tw_open and not us_open:
    logger.info("台股美股皆收盤，只更新加密貨幣")
```

改為：
```python
# 如果所有股市都收盤，跳過更新（加密貨幣由專用排程處理）
if not tw_open and not us_open:
    logger.info("台股美股皆收盤，跳過本次更新")
    return {"skipped": True, "reason": "markets_closed"}
```

---

## 📊 修改後的行為

### 管理員登入時：

| 時間 | 台股 | 美股 | 更新行為 |
|-----|------|------|---------|
| 週一~五 09:00-13:30 | ✅ 開盤 | ❌ 收盤 | 更新台股價格 |
| 週二~六 21:30-04:00 | ❌ 收盤 | ✅ 開盤 | 更新美股價格 |
| 其他時間 | ❌ 收盤 | ❌ 收盤 | **不更新股票價格** |

### 加密貨幣更新：

| 項目 | 值 |
|-----|-----|
| 快取有效期 | 3 小時（180 分鐘） |
| 更新條件 | 快取過期或強制更新 |
| 查詢時行為 | 使用快取，不即時查詢 API |

---

## ✅ 驗證方式

1. **管理員登入測試**（非開盤時間）：
   - 登入後檢查 log
   - 應該看到：`💤 台股美股皆收盤，跳過股票價格更新`

2. **加密貨幣快取測試**：
   - 查詢 BTC 價格
   - 3 小時內再次查詢，應使用快取
   - log 應顯示：`💤 加密貨幣快取未過期`

---

## 📦 部署步驟

```bash
# 1. 修改檔案
# 2. 提交 Git
git add .
git commit -m "優化：管理員登入只在開盤時更新、加密貨幣3小時快取"

# 3. 推送到 Railway
git push origin main
```
