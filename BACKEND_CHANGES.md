# P2 後端修改說明

## 1. 修改 `app/routers/stock.py` - 增加 chart_data.volumes 和 MA 進階分析

找到 `get_stock_analysis` 函數中的 `chart_data` 部分，修改為：

```python
# 添加圖表數據 (最近 1500 天，支援 5 年範圍)
"chart_data": {
    "dates": [str(d) for d in df['date'].tail(1500).tolist()],
    "prices": [float(p) for p in df['close'].tail(1500).tolist()],
    "volumes": [int(v) if not pd.isna(v) else 0 for v in df['volume'].tail(1500).tolist()] if 'volume' in df.columns else [],  # 🆕 成交量
    "ma20": [float(v) if not pd.isna(v) else None for v in df['ma20'].tail(1500).tolist()] if 'ma20' in df.columns else [],
    "ma50": [float(v) if not pd.isna(v) else None for v in df['ma50'].tail(1500).tolist()] if 'ma50' in df.columns else [],
    "ma200": [float(v) if not pd.isna(v) else None for v in df['ma200'].tail(1500).tolist()] if 'ma200' in df.columns else [],
    "ma250": [float(v) if not pd.isna(v) else None for v in df['ma250'].tail(1500).tolist()] if 'ma250' in df.columns else [],
},
```

## 2. 修改 `app/routers/stock.py` 或 `app/services/indicator_service.py` - 增加 MA 進階分析

在 indicators.ma 部分增加以下欄位：

```python
def analyze_ma_advanced(df, current_price):
    """計算 MA 進階分析"""
    result = {}
    
    # 距離均線百分比
    if 'ma20' in df.columns and not pd.isna(df['ma20'].iloc[-1]):
        ma20 = df['ma20'].iloc[-1]
        result['dist_ma20'] = round((current_price - ma20) / ma20 * 100, 2)
    
    if 'ma50' in df.columns and not pd.isna(df['ma50'].iloc[-1]):
        ma50 = df['ma50'].iloc[-1]
        result['dist_ma50'] = round((current_price - ma50) / ma50 * 100, 2)
    
    if 'ma200' in df.columns and not pd.isna(df['ma200'].iloc[-1]):
        ma200 = df['ma200'].iloc[-1]
        result['dist_ma200'] = round((current_price - ma200) / ma200 * 100, 2)
    
    # 黃金交叉/死亡交叉偵測 (最近 30 天內)
    if 'ma20' in df.columns and 'ma50' in df.columns:
        for i in range(min(30, len(df) - 1), 0, -1):
            idx = -i
            prev_idx = idx - 1
            
            if pd.isna(df['ma20'].iloc[idx]) or pd.isna(df['ma50'].iloc[idx]):
                continue
            if pd.isna(df['ma20'].iloc[prev_idx]) or pd.isna(df['ma50'].iloc[prev_idx]):
                continue
            
            # 黃金交叉: MA20 由下往上穿越 MA50
            if df['ma20'].iloc[prev_idx] < df['ma50'].iloc[prev_idx] and df['ma20'].iloc[idx] >= df['ma50'].iloc[idx]:
                result['golden_cross_20_50'] = True
                result['golden_cross_20_50_days'] = i
                break
            
            # 死亡交叉: MA20 由上往下穿越 MA50
            if df['ma20'].iloc[prev_idx] > df['ma50'].iloc[prev_idx] and df['ma20'].iloc[idx] <= df['ma50'].iloc[idx]:
                result['death_cross_20_50'] = True
                result['death_cross_20_50_days'] = i
                break
    
    # MA50/MA200 交叉偵測
    if 'ma50' in df.columns and 'ma200' in df.columns:
        for i in range(min(30, len(df) - 1), 0, -1):
            idx = -i
            prev_idx = idx - 1
            
            if pd.isna(df['ma50'].iloc[idx]) or pd.isna(df['ma200'].iloc[idx]):
                continue
            if pd.isna(df['ma50'].iloc[prev_idx]) or pd.isna(df['ma200'].iloc[prev_idx]):
                continue
            
            if df['ma50'].iloc[prev_idx] < df['ma200'].iloc[prev_idx] and df['ma50'].iloc[idx] >= df['ma200'].iloc[idx]:
                result['golden_cross_50_200'] = True
                result['golden_cross_50_200_days'] = i
                break
            
            if df['ma50'].iloc[prev_idx] > df['ma200'].iloc[prev_idx] and df['ma50'].iloc[idx] <= df['ma200'].iloc[idx]:
                result['death_cross_50_200'] = True
                result['death_cross_50_200_days'] = i
                break
    
    return result
```

然後在 `get_stock_analysis` 中調用並合併到 `indicators.ma`：

```python
# 在 indicators 建構後
ma_advanced = analyze_ma_advanced(df, current_price)
# 合併到 ma 指標
indicators["ma"].update(ma_advanced)
```

## 3. 新增 `app/routers/watchlist.py` - 熱門追蹤 API

```python
@router.get("/popular", summary="取得熱門追蹤股票")
async def get_popular_stocks(
    limit: int = Query(10, ge=1, le=50, description="返回數量"),
    db: Session = Depends(get_db)
):
    """
    取得最多人追蹤的股票排行
    """
    from sqlalchemy import func
    
    try:
        # 統計每個 symbol 被追蹤的次數
        popular = db.query(
            Watchlist.symbol,
            func.count(Watchlist.user_id).label('count')
        ).group_by(Watchlist.symbol).order_by(func.count(Watchlist.user_id).desc()).limit(limit).all()
        
        result = [{"symbol": row.symbol, "count": row.count} for row in popular]
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"取得熱門追蹤失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## 4. HTML 修改 - dashboard.html

在儀表板頁面增加熱門追蹤區塊：

```html
<!-- 熱門追蹤 -->
<div class="bg-white rounded-xl shadow p-4">
    <div class="flex items-center justify-between mb-3">
        <h3 class="font-semibold text-gray-700">🔥 熱門追蹤</h3>
        <button onclick="loadPopularStocks()" class="text-gray-400 hover:text-blue-600 text-sm">
            <i class="fas fa-sync-alt"></i>
        </button>
    </div>
    <div id="popularStocksContainer">
        <div class="text-center py-4 text-gray-400 text-sm">
            <i class="fas fa-spinner fa-spin"></i> 載入中...
        </div>
    </div>
</div>
```

## 5. HTML 修改 - 全螢幕圖表增加成交量區域

在 `chartFullscreen` modal 中的圖表下方增加：

```html
<!-- 成交量圖表 -->
<div id="volumeChartContainer" class="hidden mt-2" style="height: 100px;">
    <canvas id="volumeChart"></canvas>
</div>
```

---

## 快速整合步驟

1. 複製 `search.js` 到 `static/js/search.js`
2. 複製 `dashboard.js` 到 `static/js/dashboard.js`
3. 修改後端 `app/routers/stock.py` 增加 volumes 和 MA 進階分析
4. 修改後端 `app/routers/watchlist.py` 增加 `/popular` API
5. 修改 `dashboard.html` 增加熱門追蹤區塊和成交量圖表容器
