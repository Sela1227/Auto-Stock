/**
 * 搜尋核心模組 (P2 拆分)
 * 
 * 職責：
 * - 搜尋邏輯
 * - API 請求
 * - 快取管理
 * 
 * 依賴：core.js, state.js
 * 被依賴：search-render.js
 */

(function() {
    'use strict';

    // ============================================================
    // 快取系統
    // ============================================================
    
    const stockCache = new Map();
    const CACHE_TTL = 5 * 60 * 1000; // 5 分鐘

    function getFromCache(symbol) {
        const cached = stockCache.get(symbol.toUpperCase());
        if (cached && (Date.now() - cached.timestamp < CACHE_TTL)) {
            console.log(`📦 快取命中: ${symbol}`);
            return cached.data;
        }
        return null;
    }

    function saveToCache(symbol, data) {
        stockCache.set(symbol.toUpperCase(), {
            data: data,
            timestamp: Date.now()
        });
        console.log(`💾 已快取: ${symbol}`);
    }

    function clearStockCache() {
        stockCache.clear();
        console.log('🗑️ 股票快取已清除');
        showToast('快取已清除');
    }

    function getStockCacheStats() {
        return {
            count: stockCache.size,
            symbols: Array.from(stockCache.keys())
        };
    }

    // ============================================================
    // 搜尋功能
    // ============================================================

    function searchStock() {
        const input = $('searchSymbol');
        let symbol = input?.value?.trim().toUpperCase();
        if (!symbol) {
            showToast('請輸入股票代號');
            return;
        }
        searchSymbol(symbol);
    }

    async function searchSymbol(symbol, forceRefresh = false) {
        const container = $('searchResult');
        
        if (typeof showSection === 'function') {
            showSection('search');
        }
        
        const input = $('searchSymbol');
        if (input) input.value = symbol;

        // 檢查前端快取
        if (!forceRefresh) {
            const cached = getFromCache(symbol);
            if (cached) {
                container.classList.remove('hidden');
                // 觸發渲染（由 search-render.js 處理）
                renderSearchResult(cached, symbol);
                return;
            }
        }

        // 顯示載入中
        container.classList.remove('hidden');
        setHtml('searchResult', `
            <div class="bg-white rounded-xl shadow p-6 text-center">
                <i class="fas fa-spinner fa-spin text-2xl text-blue-600"></i>
                <p class="mt-2 text-gray-500 text-sm">查詢中...（首次查詢可能需要 10-30 秒）</p>
            </div>
        `);

        try {
            const upperSymbol = symbol.toUpperCase();
            const isCrypto = ['BTC', 'ETH', 'BITCOIN', 'ETHEREUM'].includes(upperSymbol);
            const isTaiwan = /^\d{4,6}$/.test(symbol) || upperSymbol.endsWith('.TW');

            let endpoint;
            let querySymbol = upperSymbol;

            if (isCrypto) {
                endpoint = `/api/crypto/${upperSymbol}`;
            } else if (isTaiwan) {
                querySymbol = upperSymbol.endsWith('.TW') ? upperSymbol : `${symbol}.TW`;
                endpoint = `/api/stock/${querySymbol}`;
            } else {
                endpoint = `/api/stock/${upperSymbol}`;
            }

            if (forceRefresh) {
                endpoint += '?refresh=true';
            }

            console.log(`查詢: ${endpoint}, 類型: ${isCrypto ? '加密貨幣' : isTaiwan ? '台股' : '美股'}`);

            // 設置載入狀態
            if (window.AppState) {
                AppState.setLoading(true);
            }

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);

            const res = await fetch(endpoint, { signal: controller.signal });
            clearTimeout(timeoutId);

            const data = await res.json();
            console.log('API 回應:', data);

            if (window.AppState) {
                AppState.setLoading(false);
            }

            if (!res.ok) {
                setHtml('searchResult', `
                    <div class="bg-white rounded-xl shadow p-6 text-center text-red-500">
                        <p class="font-medium">查詢失敗</p>
                        <p class="text-sm mt-2">${data.detail || 'HTTP ' + res.status}</p>
                        ${isCrypto ? '<p class="text-xs mt-2 text-gray-500">注意：加密貨幣查詢可能因 API 限制暫時無法使用</p>' : ''}
                    </div>
                `);
                return;
            }

            if (!data.success) {
                setHtml('searchResult', `
                    <div class="bg-white rounded-xl shadow p-6 text-center text-red-500">
                        ${data.detail || '查詢失敗'}
                    </div>
                `);
                return;
            }

            // 存入快取
            saveToCache(symbol, data);
            
            // 同步到 AppState
            if (window.AppState) {
                AppState.setCurrentStock({
                    symbol: data.symbol,
                    name: data.name,
                    price: data.price,
                    isCrypto,
                    isTaiwan
                });
            }

            // 渲染結果（由 search-render.js 處理）
            renderSearchResult(data, symbol);

        } catch (e) {
            console.error('Search error:', e);
            
            if (window.AppState) {
                AppState.setLoading(false);
            }

            if (e.name === 'AbortError') {
                setHtml('searchResult', `
                    <div class="bg-white rounded-xl shadow p-6 text-center text-red-500">
                        查詢超時，請稍後再試
                    </div>
                `);
            } else {
                setHtml('searchResult', `
                    <div class="bg-white rounded-xl shadow p-6 text-center text-red-500">
                        查詢失敗: ${e.message}
                    </div>
                `);
            }
        }
    }

    // ============================================================
    // 快速加入追蹤清單
    // ============================================================

    async function quickAddToWatchlist(symbol, type = 'stock') {
        try {
            const res = await apiRequest('/api/watchlist', {
                method: 'POST',
                body: { symbol: symbol.toUpperCase(), type }
            });

            const data = await res.json();

            if (res.ok && data.success) {
                showToast(`已加入追蹤: ${symbol}`);
                
                // 樂觀更新 AppState
                if (window.AppState) {
                    AppState.addToWatchlist({
                        symbol: symbol.toUpperCase(),
                        type,
                        added_at: new Date().toISOString()
                    });
                }
            } else {
                showToast(data.detail || '加入失敗', 'error');
            }
        } catch (e) {
            console.error('Add to watchlist error:', e);
            showToast('加入失敗', 'error');
        }
    }

    // ============================================================
    // 導出
    // ============================================================

    // 掛載到 SELA 命名空間
    if (window.SELA) {
        window.SELA.search = {
            searchStock,
            searchSymbol,
            quickAddToWatchlist,
            clearCache: clearStockCache,
            getCacheStats: getStockCacheStats
        };
    }

    // 全域導出（向後兼容）
    window.searchStock = searchStock;
    window.searchSymbol = searchSymbol;
    window.quickAddToWatchlist = quickAddToWatchlist;
    window.clearStockCache = clearStockCache;
    window.getStockCacheStats = getStockCacheStats;

    console.log('🔍 search-core.js 搜尋核心模組已載入');
})();
