# SELA 四大指數快取優化

## 📋 修改目標

| 項目 | 原本 | 修改後 |
|------|------|--------|
| 儀表板載入指數 | DB → 沒有就查 API | **只查 DB** |
| 資料庫無資料 | 自動查 Yahoo API | **回傳 null** |
| 數字變動時機 | 每次載入可能變 | **排程/手動更新才變** |

---

## 🔧 修改步驟

### 方法一：使用腳本（推薦）

```bash
# 1. 上傳 fix_indices_cache_only.py 到專案根目錄
# 2. 執行腳本
python3 fix_indices_cache_only.py

# 3. 部署
git add app/services/market_service.py
git commit -m "四大指數只讀快取"
git push origin main
```

### 方法二：手動修改

**檔案**: `app/services/market_service.py`

**找到** `get_latest_indices` 方法（約第 200-240 行）

**整個方法替換為**:

```python
    def get_latest_indices(self) -> Dict[str, Any]:
        """取得四大指數最新資料（只從資料庫讀取，排程才更新）"""
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
                    # 沒有快取時回傳 None，不查 API
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

## ✅ 驗證

部署後進入儀表板，檢查 Railway log：

```
✅ 應該看到: 📦 指數快取: ^GSPC = 5930.85
❌ 不應看到: 從 API 取得 ^GSPC
```

---

## 📝 注意事項

1. **首次部署**：如果資料庫沒有指數資料，儀表板會顯示「--」
2. **手動更新**：管理員面板點擊「更新指數」可手動觸發
3. **排程更新**：建議設定每日收盤後排程更新（台股 13:35、美股 05:05）
