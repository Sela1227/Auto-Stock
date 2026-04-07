/**
 * 搜尋核心模組 (P2 拆分 + 效能優化版)
 * 
 * 職責：
 * - 搜尋邏輯
 * - API 請求
 * - 快取管理
 * 
 * ⭐ 效能優化：
 * - 快取時間延長到 30 分鐘
 * - 使用 sessionStorage 持久化（頁面刷新後保留）
 * - 當日有效期判斷
 * 
 * 依賴：core.js, state.js
 * 被依賴：search-render.js
 */

(function() {
    'use strict';

    // ============================================================
    // 快取系統（優化版）
    // ============================================================
    
    const stockCache = new Map();
    const CACHE_TTL = 30 * 60 * 1000; // ⭐ 延長到 30 分鐘
    const STORAGE_KEY = 'sela_stock_cache';

    /**
     * 取得今日日期字串 (用於判斷快取是否當日有效)
     */
    function getTodayStr() {
        return new Date().toISOString().split('T')[0];
    }

    /**
     * 啟動時從 sessionStorage 恢復快取
     */
    function restoreCacheFromStorage() {
        try {
            const stored = sessionStorage.getItem(STORAGE_KEY);
            if (!stored) return;

            const parsed = JSON.parse(stored);
            const today = getTodayStr();

            // 只恢復當日的快取
            if (parsed.date !== today) {
                sessionStorage.removeItem(STORAGE_KEY);
                console.log('📦 快取已過期（非當日），已清除');
                return;
            }

            // 恢復快取
            let restored = 0;
            for (const [symbol, entry] of Object.entries(parsed.data)) {
                // 檢查 TTL 是否過期
                if (Date.now() - entry.timestamp < CACHE_TTL) {
                    stockCache.set(symbol, entry);
                    restored++;
                }
            }

            if (restored > 0) {
                console.log(`📦 已從 sessionStorage 恢復 ${restored} 筆快取`);
            }
        } catch (e) {
            console.warn('恢復快取失敗:', e);
            sessionStorage.removeItem(STORAGE_KEY);
        }
    }

    /**
     * 將快取同步到 sessionStorage
     */
    function syncCacheToStorage() {
        try {
            const data = {};
            stockCache.forEach((value, key) => {
                data[key] = value;
            });

            sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
                date: getTodayStr(),
                data: data
            }));
        } catch (e) {
            // sessionStorage 可能已滿，忽略錯誤
            console.warn('同步快取到 storage 失敗:', e);
        }
    }

    // 啟動時恢復快取
    restoreCacheFromStorage();

    function getFromCache(symbol) {
        const cached = stockCache.get(symbol.toUpperCase());
        if (cached && (Date.now() - cached.timestamp < CACHE_TTL)) {
            console.log(`📦 快取命中: ${symbol} (剩餘 ${Math.round((CACHE_TTL - (Date.now() - cached.timestamp)) / 1000)}秒)`);
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
        
        // 同步到 sessionStorage
        syncCacheToStorage();
    }

    function clearStockCache() {
        stockCache.clear();
        sessionStorage.removeItem(STORAGE_KEY);
        console.log('🗑️ 股票快取已清除');
        showToast('快取已清除');
    }

    function getStockCacheStats() {
        const now = Date.now();
        const validCount = Array.from(stockCache.values())
            .filter(c => now - c.timestamp < CACHE_TTL).length;
        
        return {
            count: stockCache.size,
            validCount: validCount,
            symbols: Array.from(stockCache.keys()),
            ttlMinutes: CACHE_TTL / 60000
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

    console.log('🔍 search-core.js 搜尋核心模組已載入 (優化版: 30分鐘快取 + sessionStorage 持久化)');
})();
