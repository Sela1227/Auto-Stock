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
            return cached.data;
        }
        return null;
    }

    function saveToCache(symbol, data) {
        stockCache.set(symbol.toUpperCase(), {
            data: data,
            timestamp: Date.now()
        });
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


            // 設置載入狀態
            if (window.AppState) {
                AppState.setLoading(true);
            }

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);

            const res = await fetch(endpoint, { signal: controller.signal });
            clearTimeout(timeoutId);

            const data = await res.json();

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
        };
    }

    // 全域導出（向後兼容）
    window.searchStock = searchStock;
    window.searchSymbol = searchSymbol;
    window.quickAddToWatchlist = quickAddToWatchlist;

})();
/**
 * 搜尋結果渲染模組 (P2 拆分)
 * 
 * 職責：
 * - 搜尋結果渲染
 * - MA 進階分析
 * - 事件委託處理
 * 
 * 依賴：core.js, search-core.js
 */

(function() {
    'use strict';

    // ============================================================
    // 私有變數
    // ============================================================

    let currentChartData = null;

    // ============================================================
    // 渲染入口
    // ============================================================

    function renderSearchResult(data, symbol) {
        const upperSymbol = symbol.toUpperCase();
        const isCrypto = ['BTC', 'ETH', 'BITCOIN', 'ETHEREUM'].includes(upperSymbol);
        const isTaiwan = /^\d{4,6}$/.test(symbol) || upperSymbol.endsWith('.TW');

        currentChartData = data.chart_data;
        window.currentChartData = currentChartData;

        renderStockResult(data, isCrypto, isTaiwan);
    }

    // ============================================================
    // 股票結果渲染
    // ============================================================

    function renderStockResult(stock, isCrypto, isTaiwan = false) {
        const container = $('searchResult');
        if (!container) return;

        const indicators = stock.indicators || {};
        const ma = indicators.ma || {};
        const rsi = indicators.rsi || {};
        const macd = indicators.macd || {};

        const priceChange = stock.change?.day || 0;
        const priceChangeClass = priceChange >= 0 ? 'text-green-600' : 'text-red-600';
        const priceChangeIcon = priceChange >= 0 ? '<i class="fas fa-arrow-trend-up"></i>' : '<i class="fas fa-arrow-trend-down"></i>';

        const alignmentClass = ma.alignment === 'bullish' ? 'text-green-600' : ma.alignment === 'bearish' ? 'text-red-600' : 'text-gray-600';
        const alignmentText = ma.alignment === 'bullish' ? '多頭 <i class="fas fa-circle text-green-500 text-[8px] align-middle"></i>' : ma.alignment === 'bearish' ? '空頭 <i class="fas fa-circle text-red-500 text-[8px] align-middle"></i>' : '中性';

        const rsiStatus = rsi.status === 'overbought' ? '超買 <i class="fas fa-triangle-exclamation"></i>' : rsi.status === 'oversold' ? '超賣 <i class="fas fa-circle text-green-500 text-[8px] align-middle"></i>' : '中性';
        const macdStatus = macd.status === 'bullish' ? '偏多 <i class="fas fa-circle text-green-500 text-[8px] align-middle"></i>' : '偏空 <i class="fas fa-circle text-red-500 text-[8px] align-middle"></i>';

        let marketLabel, marketClass;
        if (isCrypto) {
            marketLabel = '加密貨幣';
            marketClass = 'bg-purple-100 text-purple-700';
        } else if (isTaiwan) {
            marketLabel = '台股';
            marketClass = 'bg-orange-100 text-orange-700';
        } else {
            marketLabel = '美股';
            marketClass = 'bg-blue-100 text-blue-700';
        }

        const cacheIndicator = stock.from_cache
            ? `<span class="px-2 py-1 rounded text-xs bg-gray-100 text-gray-500" title="資料來自快取">
                   <i class="fas fa-database mr-1"></i>快取
               </span>`
            : '';

        const maAdvanced = renderMAAdvanced(ma, stock.price?.current);

        const html = `
            <div class="bg-white rounded-xl shadow overflow-hidden" id="searchResultCard" data-symbol="${stock.symbol}">
                <!-- 價格區塊 -->
                <div class="p-4 md:p-6 border-b">
                    <div class="flex items-start justify-between mb-2">
                        <div>
                            <h3 class="text-xl md:text-2xl font-bold text-gray-800">${stock.symbol}</h3>
                            <p class="text-gray-500 text-sm">${stock.name || marketLabel}</p>
                        </div>
                        <div class="flex items-center gap-2">
                            ${cacheIndicator}
                            <button data-action="refresh" data-symbol="${stock.symbol}" class="p-2 text-gray-400 hover:text-blue-600 transition" title="重新整理">
                                <i class="fas fa-sync-alt"></i>
                            </button>
                            <span class="px-2 py-1 rounded text-xs ${marketClass}">${marketLabel}</span>
                        </div>
                    </div>
                    <div class="mt-3">
                        <span class="text-3xl md:text-4xl font-bold text-gray-800">$${stock.price?.current?.toLocaleString() || '--'}</span>
                        <span class="ml-2 ${priceChangeClass} text-lg">
                            ${priceChange >= 0 ? '+' : ''}${priceChange?.toFixed(2)}% ${priceChangeIcon}
                        </span>
                    </div>
                </div>

                <!-- 快速總覽 -->
                <div class="p-4 md:p-6 border-b bg-gray-50">
                    <h4 class="font-semibold text-gray-700 mb-3 text-sm"><i class="fas fa-chart-bar mr-2"></i>快速總覽</h4>
                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-500">均線排列</span>
                            <span class="font-medium ${alignmentClass}">${alignmentText}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-500">RSI (${rsi.period || 14})</span>
                            <span class="font-medium">${rsi.value?.toFixed(1) || '--'} ${rsiStatus}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-500">MACD</span>
                            <span class="font-medium">${macdStatus}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-500">評分</span>
                            <span class="font-medium">${stock.score?.rating === 'bullish' ? '偏多' : stock.score?.rating === 'bearish' ? '偏空' : '中性'} (${stock.score?.buy || 0}/${stock.score?.sell || 0})</span>
                        </div>
                    </div>
                </div>

                <!-- MA 進階分析 -->
                ${maAdvanced}

                <!-- 年化報酬率 (CAGR) -->
                ${stock.cagr ? renderCAGRSection(stock.cagr) : ''}

                <!-- 詳細指標 (可摺疊) -->
                <div class="border-b">
                    <button data-action="toggle-collapsible" class="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 touch-target">
                        <span class="font-medium text-gray-700">▼ 展開詳細指標</span>
                        <i class="fas fa-chevron-down text-gray-400 transition-transform"></i>
                    </button>
                    <div class="collapsible-content" style="max-height: 0; overflow: hidden; transition: max-height 0.3s ease;">
                        ${renderDetailedIndicators(ma, rsi, macd)}
                    </div>
                </div>

                <!-- 操作按鈕 -->
                <div class="p-4 pb-28 md:pb-4 space-y-3">
                    ${stock.chart_data ? `
                    <button data-action="open-chart" data-symbol="${stock.symbol}" data-price="${stock.price?.current || 0}"
                        class="w-full py-3 bg-blue-600 text-white rounded-lg font-medium flex items-center justify-center touch-target hover:bg-blue-700">
                        <i class="fas fa-chart-line mr-2"></i>查看完整圖表
                    </button>
                    ` : ''}
                    <button data-action="load-returns" data-symbol="${stock.symbol}"
                        class="w-full py-3 bg-green-600 text-white rounded-lg font-medium flex items-center justify-center touch-target hover:bg-green-700">
                        <i class="fas fa-percentage mr-2"></i>年化報酬率
                    </button>
                    <button data-action="add-watchlist" data-symbol="${stock.symbol}" data-type="${isCrypto ? 'crypto' : 'stock'}"
                        class="w-full py-3 border-2 border-orange-500 text-orange-600 rounded-lg font-medium flex items-center justify-center touch-target hover:bg-orange-50">
                        <i class="fas fa-star mr-2"></i>加入追蹤清單
                    </button>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    // ============================================================
    // MA 進階分析渲染
    // ============================================================

    function renderMAAdvanced(ma, currentPrice) {
        if (!ma || !currentPrice) return '';

        // 交叉訊號
        const crossSignals = [];
        if (ma.golden_cross_20_50) crossSignals.push({ type: 'golden', label: 'MA20↗MA50 黃金交叉', days: ma.golden_cross_20_50_days });
        if (ma.death_cross_20_50) crossSignals.push({ type: 'death', label: 'MA20↘MA50 死亡交叉', days: ma.death_cross_20_50_days });
        if (ma.golden_cross_50_200) crossSignals.push({ type: 'golden', label: 'MA50↗MA200 黃金交叉', days: ma.golden_cross_50_200_days });
        if (ma.death_cross_50_200) crossSignals.push({ type: 'death', label: 'MA50↘MA200 死亡交叉', days: ma.death_cross_50_200_days });

        // 距離均線百分比
        const distances = [];
        if (ma.dist_ma20 !== undefined) distances.push({ label: 'MA20', value: ma.dist_ma20 });
        if (ma.dist_ma50 !== undefined) distances.push({ label: 'MA50', value: ma.dist_ma50 });
        if (ma.dist_ma200 !== undefined) distances.push({ label: 'MA200', value: ma.dist_ma200 });

        if (crossSignals.length === 0 && distances.length === 0) return '';

        let html = `
            <div class="p-4 md:p-6 border-b">
                <h4 class="font-semibold text-gray-700 mb-3 text-sm"><i class="fas fa-magnifying-glass mr-2"></i>均線進階分析</h4>
        `;

        // 交叉訊號
        if (crossSignals.length > 0) {
            html += `<div class="mb-3">`;
            crossSignals.forEach(signal => {
                const bgClass = signal.type === 'golden' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';
                const icon = signal.type === 'golden' ? '<i class="fas fa-caret-up"></i>' : '<i class="fas fa-caret-down"></i>';
                const daysText = signal.days ? `(${signal.days}天前)` : '';
                html += `
                    <span class="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium ${bgClass} mr-2 mb-2">
                        ${icon} ${signal.label} ${daysText}
                    </span>
                `;
            });
            html += `</div>`;
        }

        // 距離均線
        if (distances.length > 0) {
            html += `
                <div class="grid grid-cols-3 gap-2 text-center">
                    ${distances.map(d => {
                        const isAbove = d.value >= 0;
                        const bgClass = isAbove ? 'bg-green-50' : 'bg-red-50';
                        const textClass = isAbove ? 'text-green-600' : 'text-red-600';
                        return `
                            <div class="p-2 rounded-lg ${bgClass}">
                                <p class="text-gray-500 text-xs">距 ${d.label}</p>
                                <p class="font-bold ${textClass}">${d.value >= 0 ? '+' : ''}${d.value.toFixed(1)}%</p>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        html += `</div>`;
        return html;
    }

    // ============================================================
    // CAGR 區塊渲染
    // ============================================================

    function renderCAGRSection(cagr) {
        return `
            <div class="p-4 md:p-6 border-b">
                <h4 class="font-semibold text-gray-700 mb-3 text-sm"><i class="fas fa-chart-line mr-2"></i>年化報酬率 (CAGR)</h4>
                <div class="grid grid-cols-4 gap-2 text-center">
                    ${['1y', '3y', '5y', '10y'].map(period => {
                        const val = cagr[`cagr_${period}`];
                        const bgClass = val > 0 ? 'bg-green-50' : val < 0 ? 'bg-red-50' : 'bg-gray-50';
                        const textClass = val > 0 ? 'text-green-600' : val < 0 ? 'text-red-600' : 'text-gray-600';
                        return `
                            <div class="p-2 rounded-lg ${bgClass}">
                                <p class="text-gray-500 text-xs">${period.replace('y', ' 年')}</p>
                                <p class="font-bold ${textClass}">
                                    ${val !== null ? (val > 0 ? '+' : '') + val + '%' : '--'}
                                </p>
                            </div>
                        `;
                    }).join('')}
                </div>
                <p class="text-xs text-gray-400 mt-2 text-center">年化複合成長率，反映長期投資回報</p>
            </div>
        `;
    }

    // ============================================================
    // 詳細指標渲染
    // ============================================================

    function renderDetailedIndicators(ma, rsi, macd) {
        return `
            <div class="px-4 pb-4 space-y-3">
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    ${['ma20', 'ma50', 'ma200'].map(key => {
                        const val = ma[key];
                        const vsKey = `price_vs_${key}`;
                        const isAbove = ma[vsKey] === 'above';
                        const distKey = `dist_${key}`;
                        const dist = ma[distKey];
                        const distText = dist !== undefined ? `${dist >= 0 ? '+' : ''}${dist.toFixed(1)}%` : '';
                        return `
                            <div class="p-3 rounded-lg ${isAbove ? 'bg-green-50' : 'bg-red-50'}">
                                <p class="text-gray-500 text-xs">${key.toUpperCase()}</p>
                                <p class="font-semibold">${val?.toFixed(2) || '--'}</p>
                                <p class="text-xs ${isAbove ? 'text-green-600' : 'text-red-600'}">
                                    ${isAbove ? '價格在上 ✓' : '價格在下'} ${distText ? `(${distText})` : ''}
                                </p>
                            </div>
                        `;
                    }).join('')}
                </div>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <div class="p-3 bg-gray-50 rounded-lg">
                        <p class="text-gray-500 text-xs">RSI (${rsi.period || 14})</p>
                        <p class="font-semibold">${rsi.value?.toFixed(2) || '--'}</p>
                    </div>
                    <div class="p-3 bg-gray-50 rounded-lg">
                        <p class="text-gray-500 text-xs">MACD DIF</p>
                        <p class="font-semibold">${macd.dif?.toFixed(2) || '--'}</p>
                    </div>
                </div>
            </div>
        `;
    }

    // ============================================================
    // 事件委託 (P2 核心優化)
    // ============================================================

    function initSearchEventDelegation() {
        const container = $('searchResult');
        if (!container) return;

        // 使用事件委託，只綁定一個監聽器
        container.addEventListener('click', handleSearchResultClick);
    }

    function handleSearchResultClick(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        const action = target.dataset.action;
        const symbol = target.dataset.symbol;

        switch (action) {
            case 'refresh':
                e.preventDefault();
                if (typeof searchSymbol === 'function') {
                    searchSymbol(symbol, true);
                }
                break;

            case 'toggle-collapsible':
                e.preventDefault();
                toggleCollapsible(target);
                break;

            case 'open-chart':
                e.preventDefault();
                const price = parseFloat(target.dataset.price) || 0;
                if (typeof openChartFullscreen === 'function') {
                    openChartFullscreen(symbol, price);
                }
                break;

            case 'load-returns':
                e.preventDefault();
                if (typeof loadReturnsModal === 'function') {
                    loadReturnsModal(symbol);
                }
                break;

            case 'add-watchlist':
                e.preventDefault();
                const type = target.dataset.type || 'stock';
                if (typeof quickAddToWatchlist === 'function') {
                    quickAddToWatchlist(symbol, type);
                }
                break;
        }
    }

    // 摺疊面板切換
    function toggleCollapsible(button) {
        const content = button.nextElementSibling;
        const icon = button.querySelector('i');

        if (content.style.maxHeight && content.style.maxHeight !== '0px') {
            content.style.maxHeight = '0px';
            if (icon) icon.style.transform = '';
        } else {
            content.style.maxHeight = content.scrollHeight + 'px';
            if (icon) icon.style.transform = 'rotate(180deg)';
        }
    }

    // ============================================================
    // 初始化
    // ============================================================

    function init() {
        // DOM 載入後初始化事件委託
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initSearchEventDelegation);
        } else {
            initSearchEventDelegation();
        }
    }

    init();

    // ============================================================
    // 導出
    // ============================================================

    // 掛載到 SELA 命名空間
    if (window.SELA && window.SELA.search) {
        Object.assign(window.SELA.search, {
            renderSearchResult,
            renderStockResult
        });
    }

    // 全域導出（向後兼容）
    window.renderSearchResult = renderSearchResult;
    window.renderStockResult = renderStockResult;
    window.toggleCollapsible = toggleCollapsible;

})();
