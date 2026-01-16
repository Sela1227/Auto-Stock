/**
 * 股票查詢模組
 * 包含：搜尋、結果顯示、全螢幕圖表、成交量圖表、MA進階分析
 */

(function() {
    'use strict';
    
    // ============================================================
    // 私有變數
    // ============================================================
    
    let currentChartData = null;
    let fullscreenChartInstance = null;
    let volumeChartInstance = null;  // 🆕 成交量圖表實例
    
    // 前端快取（5分鐘有效）
    const stockCache = new Map();
    const CACHE_TTL = 5 * 60 * 1000; // 5 分鐘
    
    /**
     * 從快取取得資料
     */
    function getFromCache(symbol) {
        const cached = stockCache.get(symbol.toUpperCase());
        if (cached && (Date.now() - cached.timestamp < CACHE_TTL)) {
            console.log(`📦 快取命中: ${symbol}`);
            return cached.data;
        }
        return null;
    }
    
    /**
     * 存入快取
     */
    function saveToCache(symbol, data) {
        stockCache.set(symbol.toUpperCase(), {
            data: data,
            timestamp: Date.now()
        });
        console.log(`💾 已快取: ${symbol}`);
    }
    
    // ============================================================
    // 搜尋功能
    // ============================================================
    
    function searchStock() {
        let symbol = document.getElementById('searchSymbol').value.trim().toUpperCase();
        if (!symbol) {
            showToast('請輸入股票代號');
            return;
        }
        searchSymbol(symbol);
    }

    async function searchSymbol(symbol, forceRefresh = false) {
        const container = document.getElementById('searchResult');
        
        if (typeof showSection === 'function') {
            showSection('search');
        }
        document.getElementById('searchSymbol').value = symbol;
        
        // 檢查前端快取（除非強制刷新）
        if (!forceRefresh) {
            const cached = getFromCache(symbol);
            if (cached) {
                container.classList.remove('hidden');
                renderSearchResult(cached, symbol);
                return;
            }
        }
        
        // 顯示載入中
        container.classList.remove('hidden');
        container.innerHTML = `
            <div class="bg-white rounded-xl shadow p-6 text-center">
                <i class="fas fa-spinner fa-spin text-2xl text-blue-600"></i>
                <p class="mt-2 text-gray-500 text-sm">查詢中...（首次查詢可能需要 10-30 秒）</p>
            </div>
        `;

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
            
            console.log(`查詢: ${endpoint}, 類型: ${isCrypto ? '加密貨幣' : isTaiwan ? '台股' : '美股'}, 強制刷新: ${forceRefresh}`);
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);
            
            const res = await fetch(endpoint, { signal: controller.signal });
            clearTimeout(timeoutId);
            
            const data = await res.json();
            console.log('API 回應:', data);
            
            if (data.from_cache) {
                console.log(`📦 後端快取命中: ${symbol} (快取時間: ${data.cache_time})`);
            }
            
            if (!res.ok) {
                container.innerHTML = `
                    <div class="bg-white rounded-xl shadow p-6 text-center text-red-500">
                        <p class="font-medium">查詢失敗</p>
                        <p class="text-sm mt-2">${data.detail || 'HTTP ' + res.status}</p>
                        ${isCrypto ? '<p class="text-xs mt-2 text-gray-500">注意：加密貨幣查詢可能因 API 限制暫時無法使用</p>' : ''}
                    </div>
                `;
                return;
            }
            
            if (!data.success) {
                container.innerHTML = `<div class="bg-white rounded-xl shadow p-6 text-center text-red-500">${data.detail || '查詢失敗'}</div>`;
                return;
            }

            saveToCache(symbol, data);
            renderSearchResult(data, symbol);
            
        } catch (e) {
            console.error('Search error:', e);
            if (e.name === 'AbortError') {
                container.innerHTML = '<div class="bg-white rounded-xl shadow p-6 text-center text-red-500">查詢超時，請稍後再試</div>';
            } else {
                container.innerHTML = `<div class="bg-white rounded-xl shadow p-6 text-center text-red-500">查詢失敗: ${e.message}</div>`;
            }
        }
    }

    // ============================================================
    // 結果渲染
    // ============================================================
    
    function renderSearchResult(data, symbol) {
        const upperSymbol = symbol.toUpperCase();
        const isCrypto = ['BTC', 'ETH', 'BITCOIN', 'ETHEREUM'].includes(upperSymbol);
        const isTaiwan = /^\d{4,6}$/.test(symbol) || upperSymbol.endsWith('.TW');
        
        currentChartData = data.chart_data;
        window.currentChartData = currentChartData;
        
        renderStockResult(data, isCrypto, isTaiwan);
    }

    function renderStockResult(stock, isCrypto, isTaiwan = false) {
        const container = document.getElementById('searchResult');
        const indicators = stock.indicators || {};
        const ma = indicators.ma || {};
        const rsi = indicators.rsi || {};
        const macd = indicators.macd || {};
        
        const priceChange = stock.change?.day || 0;
        const priceChangeClass = priceChange >= 0 ? 'text-green-600' : 'text-red-600';
        const priceChangeIcon = priceChange >= 0 ? '📈' : '📉';
        
        const alignmentClass = ma.alignment === 'bullish' ? 'text-green-600' : ma.alignment === 'bearish' ? 'text-red-600' : 'text-gray-600';
        const alignmentText = ma.alignment === 'bullish' ? '多頭 🟢' : ma.alignment === 'bearish' ? '空頭 🔴' : '中性';
        
        const rsiStatus = rsi.status === 'overbought' ? '超買 ⚠️' : rsi.status === 'oversold' ? '超賣 🟢' : '中性';
        const macdStatus = macd.status === 'bullish' ? '偏多 🟢' : '偏空 🔴';
        
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
            ? `<span class="px-2 py-1 rounded text-xs bg-gray-100 text-gray-500" title="資料來自快取，點擊刷新按鈕取得最新">
                   <i class="fas fa-database mr-1"></i>快取
               </span>` 
            : '';
        
        // 🆕 MA 進階分析
        const maAdvanced = renderMAAdvanced(ma, stock.price?.current);
        
        const html = `
            <div class="bg-white rounded-xl shadow overflow-hidden">
                <!-- 價格區塊 -->
                <div class="p-4 md:p-6 border-b">
                    <div class="flex items-start justify-between mb-2">
                        <div>
                            <h3 class="text-xl md:text-2xl font-bold text-gray-800">${stock.symbol}</h3>
                            <p class="text-gray-500 text-sm">${stock.name || marketLabel}</p>
                        </div>
                        <div class="flex items-center gap-2">
                            ${cacheIndicator}
                            <button onclick="searchSymbol('${stock.symbol}', true)" class="p-2 text-gray-400 hover:text-blue-600 transition" title="重新整理">
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
                    <h4 class="font-semibold text-gray-700 mb-3 text-sm">📊 快速總覽</h4>
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
                
                <!-- 🆕 MA 進階分析 -->
                ${maAdvanced}
                
                <!-- 年化報酬率 (CAGR) -->
                ${stock.cagr ? `
                <div class="p-4 md:p-6 border-b">
                    <h4 class="font-semibold text-gray-700 mb-3 text-sm">📈 年化報酬率 (CAGR)</h4>
                    <div class="grid grid-cols-4 gap-2 text-center">
                        ${['1y', '3y', '5y', '10y'].map(period => {
                            const val = stock.cagr[`cagr_${period}`];
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
                ` : ''}
                
                <!-- 詳細指標 (可摺疊) -->
                <div class="border-b">
                    <button onclick="toggleCollapsible(this)" class="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 touch-target">
                        <span class="font-medium text-gray-700">▼ 展開詳細指標</span>
                        <i class="fas fa-chevron-down text-gray-400 transition-transform"></i>
                    </button>
                    <div class="collapsible-content">
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
                    </div>
                </div>
                
                <!-- 操作按鈕 -->
                <div class="p-4 pb-28 md:pb-4 space-y-3">
                    ${stock.chart_data ? `
                    <button onclick="openChartFullscreen('${stock.symbol}', ${stock.price?.current || 0})" 
                        class="w-full py-3 bg-blue-600 text-white rounded-lg font-medium flex items-center justify-center touch-target hover:bg-blue-700">
                        <i class="fas fa-chart-line mr-2"></i>查看完整圖表
                    </button>
                    ` : ''}
                    <button onclick="loadReturnsModal('${stock.symbol}')" 
                        class="w-full py-3 bg-green-600 text-white rounded-lg font-medium flex items-center justify-center touch-target hover:bg-green-700">
                        <i class="fas fa-percentage mr-2"></i>年化報酬率
                    </button>
                    <button onclick="quickAddToWatchlist('${stock.symbol}', '${isCrypto ? 'crypto' : 'stock'}')" 
                        class="w-full py-3 border-2 border-orange-500 text-orange-600 rounded-lg font-medium flex items-center justify-center touch-target hover:bg-orange-50">
                        <i class="fas fa-star mr-2"></i>加入追蹤清單
                    </button>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    /**
     * 🆕 渲染 MA 進階分析區塊
     */
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
        
        // 如果沒有任何資料，返回空
        if (crossSignals.length === 0 && distances.length === 0) return '';
        
        let html = `
            <div class="p-4 md:p-6 border-b">
                <h4 class="font-semibold text-gray-700 mb-3 text-sm">📐 均線進階分析</h4>
        `;
        
        // 交叉訊號
        if (crossSignals.length > 0) {
            html += `<div class="mb-3">`;
            crossSignals.forEach(signal => {
                const bgClass = signal.type === 'golden' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';
                const icon = signal.type === 'golden' ? '🔺' : '🔻';
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
                        const isPositive = d.value >= 0;
                        const bgClass = isPositive ? 'bg-green-50' : 'bg-red-50';
                        const textClass = isPositive ? 'text-green-600' : 'text-red-600';
                        const arrow = isPositive ? '↑' : '↓';
                        return `
                            <div class="p-2 rounded-lg ${bgClass}">
                                <p class="text-gray-500 text-xs">距 ${d.label}</p>
                                <p class="font-bold ${textClass}">
                                    ${arrow} ${Math.abs(d.value).toFixed(1)}%
                                </p>
                            </div>
                        `;
                    }).join('')}
                </div>
                <p class="text-xs text-gray-400 mt-2 text-center">正值表示價格高於均線，負值表示低於均線</p>
            `;
        }
        
        html += `</div>`;
        return html;
    }
    
    function toggleCollapsible(btn) {
        const content = btn.nextElementSibling;
        const icon = btn.querySelector('i');
        content.classList.toggle('open');
        icon.style.transform = content.classList.contains('open') ? 'rotate(180deg)' : '';
        btn.querySelector('span').textContent = content.classList.contains('open') ? '▲ 收合詳細指標' : '▼ 展開詳細指標';
    }

    // ============================================================
    // 全螢幕圖表
    // ============================================================

    function openChartFullscreen(symbol, price) {
        const chartData = currentChartData || window.currentChartData;
        if (!chartData) {
            showToast('沒有圖表資料');
            return;
        }
        
        document.getElementById('chartFullscreenTitle').textContent = `${symbol}  $${price.toLocaleString()}`;
        document.getElementById('chartFullscreen').classList.add('open');
        document.body.style.overflow = 'hidden';
        
        setTimeout(() => {
            renderFullscreenChart(chartData, 65);
        }, 100);
    }
    
    function closeChartFullscreen() {
        document.getElementById('chartFullscreen').classList.remove('open');
        document.body.style.overflow = '';
        
        if (fullscreenChartInstance) {
            fullscreenChartInstance.destroy();
            fullscreenChartInstance = null;
        }
        if (volumeChartInstance) {
            volumeChartInstance.destroy();
            volumeChartInstance = null;
        }
    }
    
    function setChartRange(days, btn) {
        document.querySelectorAll('.chart-range-btn').forEach(b => {
            b.classList.remove('bg-blue-50', 'border-blue-500', 'text-blue-600', 'active');
            b.classList.add('border-gray-300');
        });
        if (btn) {
            btn.classList.remove('border-gray-300');
            btn.classList.add('bg-blue-50', 'border-blue-500', 'text-blue-600', 'active');
        }
        
        const chartData = currentChartData || window.currentChartData;
        if (chartData && chartData.dates && chartData.dates.length > 0) {
            renderFullscreenChart(chartData, days);
        }
    }
    
    function renderFullscreenChart(chartData, days) {
        const canvas = document.getElementById('fullscreenChart');
        if (!canvas) return;
        
        if (fullscreenChartInstance) {
            fullscreenChartInstance.destroy();
        }
        if (volumeChartInstance) {
            volumeChartInstance.destroy();
            volumeChartInstance = null;
        }
        
        const ctx = canvas.getContext('2d');
        const dataLength = chartData.dates.length;
        const startIdx = Math.max(0, dataLength - days);
        
        const formatDate = (d) => {
            if (days <= 130) {
                return d.slice(5);
            } else {
                return d.slice(2, 7).replace('-', '/');
            }
        };
        
        const labels = chartData.dates.slice(startIdx).map(d => formatDate(d));
        
        fullscreenChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '收盤價',
                        data: chartData.prices.slice(startIdx),
                        borderColor: '#3B82F6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0,
                    },
                    {
                        label: 'MA20',
                        data: chartData.ma20.slice(startIdx),
                        borderColor: '#EF4444',
                        borderWidth: 1.5,
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0,
                    },
                    {
                        label: 'MA50',
                        data: chartData.ma50.slice(startIdx),
                        borderColor: '#10B981',
                        borderWidth: 1.5,
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0,
                    },
                    {
                        label: 'MA200',
                        data: chartData.ma200.slice(startIdx),
                        borderColor: '#EAB308',
                        borderWidth: 1.5,
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0,
                    },
                    {
                        label: 'MA250',
                        data: chartData.ma250 ? chartData.ma250.slice(startIdx) : [],
                        borderColor: '#A855F7',
                        borderWidth: 1.5,
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0,
                    },
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { usePointStyle: true, padding: 10 }
                    },
                    tooltip: {
                        callbacks: {
                            label: ctx => ctx.raw === null ? null : `${ctx.dataset.label}: $${ctx.raw.toFixed(2)}`
                        }
                    }
                },
                scales: {
                    x: { 
                        grid: { display: false },
                        ticks: { maxTicksLimit: days <= 60 ? 8 : 10, maxRotation: 0 }
                    },
                    y: { grid: { color: 'rgba(0,0,0,0.05)' } }
                }
            }
        });
        
        // 🆕 渲染成交量圖表
        if (chartData.volumes && chartData.volumes.length > 0) {
            renderVolumeChart(chartData, days, labels);
        }
    }
    
    /**
     * 🆕 渲染成交量圖表
     */
    function renderVolumeChart(chartData, days, labels) {
        const volumeCanvas = document.getElementById('volumeChart');
        if (!volumeCanvas) return;
        
        // 顯示成交量容器
        const volumeContainer = document.getElementById('volumeChartContainer');
        if (volumeContainer) {
            volumeContainer.classList.remove('hidden');
        }
        
        if (volumeChartInstance) {
            volumeChartInstance.destroy();
        }
        
        const ctx = volumeCanvas.getContext('2d');
        const dataLength = chartData.dates.length;
        const startIdx = Math.max(0, dataLength - days);
        
        const volumes = chartData.volumes.slice(startIdx);
        const prices = chartData.prices.slice(startIdx);
        
        // 計算每根柱子的顏色（漲綠跌紅）
        const barColors = prices.map((price, i) => {
            if (i === 0) return 'rgba(156, 163, 175, 0.6)';
            return price >= prices[i - 1] ? 'rgba(34, 197, 94, 0.6)' : 'rgba(239, 68, 68, 0.6)';
        });
        
        // 計算 20 日均量
        const avgVolumes = [];
        for (let i = 0; i < volumes.length; i++) {
            if (i < 19) {
                avgVolumes.push(null);
            } else {
                const sum = volumes.slice(i - 19, i + 1).reduce((a, b) => a + b, 0);
                avgVolumes.push(sum / 20);
            }
        }
        
        volumeChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '成交量',
                        data: volumes,
                        backgroundColor: barColors,
                        borderWidth: 0,
                        barPercentage: 0.8,
                    },
                    {
                        label: '20日均量',
                        data: avgVolumes,
                        type: 'line',
                        borderColor: '#F59E0B',
                        borderWidth: 1.5,
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { usePointStyle: true, padding: 10, boxWidth: 8 }
                    },
                    tooltip: {
                        callbacks: {
                            label: ctx => {
                                if (ctx.raw === null) return null;
                                const val = ctx.raw;
                                if (val >= 1e9) return `${ctx.dataset.label}: ${(val / 1e9).toFixed(2)}B`;
                                if (val >= 1e6) return `${ctx.dataset.label}: ${(val / 1e6).toFixed(2)}M`;
                                if (val >= 1e3) return `${ctx.dataset.label}: ${(val / 1e3).toFixed(2)}K`;
                                return `${ctx.dataset.label}: ${val.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: { 
                        grid: { display: false },
                        ticks: { display: false }
                    },
                    y: { 
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        ticks: {
                            callback: function(value) {
                                if (value >= 1e9) return (value / 1e9).toFixed(1) + 'B';
                                if (value >= 1e6) return (value / 1e6).toFixed(1) + 'M';
                                if (value >= 1e3) return (value / 1e3).toFixed(1) + 'K';
                                return value;
                            }
                        }
                    }
                }
            }
        });
    }

    // ============================================================
    // 快速加入追蹤清單
    // ============================================================

    async function quickAddToWatchlist(symbol, assetType) {
        try {
            const res = await apiRequest('/api/watchlist', {
                method: 'POST',
                body: { symbol, asset_type: assetType }
            });
            
            const data = await res.json();
            
            if (data.success) {
                showToast('已加入追蹤清單');
            } else {
                showToast(data.detail || '新增失敗');
            }
        } catch (e) {
            console.error('新增追蹤失敗:', e);
            showToast('新增失敗');
        }
    }

    // ============================================================
    // 事件監聽
    // ============================================================

    function initChartRangeButtons() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.chart-range-btn');
            if (btn && btn.dataset.days) {
                e.preventDefault();
                e.stopPropagation();
                const days = parseInt(btn.dataset.days, 10);
                setChartRange(days, btn);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', initChartRangeButtons);
    
    window.addEventListener('orientationchange', () => {
        setTimeout(initChartRangeButtons, 100);
    });

    // ============================================================
    // 年化報酬率 Modal
    // ============================================================

    async function loadReturnsModal(symbol) {
        const modal = document.getElementById('returnsModal');
        const content = document.getElementById('returnsModalContent');
        const title = document.getElementById('returnsModalTitle');
        
        if (!modal || !content) return;
        
        if (title) title.textContent = `${symbol} 年化報酬率`;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        content.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-spinner fa-spin text-2xl text-green-600"></i>
                <p class="mt-2 text-gray-500">計算中...（含配息再投入）</p>
            </div>
        `;
        
        try {
            const res = await apiRequest(`/api/stock/${symbol}/returns`);
            const data = await res.json();
            
            if (!data.success) {
                throw new Error(data.detail || '計算失敗');
            }
            
            renderReturnsModal(data.data);
            
        } catch (e) {
            console.error('載入年化報酬率失敗:', e);
            content.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    <i class="fas fa-exclamation-circle text-3xl mb-2"></i>
                    <p>${e.message || '載入失敗'}</p>
                </div>
            `;
        }
    }
    
    function renderReturnsModal(data) {
        const content = document.getElementById('returnsModalContent');
        if (!content) return;
        
        const periods = ['1Y', '3Y', '5Y', '10Y'];
        
        let html = `
            <div class="mb-4 p-3 bg-gray-50 rounded-lg">
                <p class="text-gray-600 text-sm">${data.name}</p>
                <p class="text-2xl font-bold text-gray-800">$${data.current_price.toLocaleString()}</p>
                <p class="text-xs text-gray-400">${data.current_date}</p>
            </div>
            <div class="space-y-3">
        `;
        
        for (const period of periods) {
            const ret = data.returns[period];
            
            if (!ret) {
                html += `
                    <div class="p-3 bg-gray-100 rounded-lg opacity-50">
                        <div class="flex justify-between items-center">
                            <span class="font-medium text-gray-600">${period}</span>
                            <span class="text-gray-400 text-sm">資料不足</span>
                        </div>
                    </div>
                `;
                continue;
            }
            
            const cagr = ret.cagr;
            const cagrClass = cagr >= 0 ? 'text-green-600' : 'text-red-600';
            const cagrIcon = cagr >= 0 ? '▲' : '▼';
            const cagrBg = cagr >= 0 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200';
            
            html += `
                <div class="p-4 bg-white border rounded-lg shadow-sm">
                    <div class="flex justify-between items-center mb-3">
                        <span class="font-bold text-lg text-gray-800">${period}</span>
                        <span class="text-xs text-gray-400">${ret.start_date} ~ 今</span>
                    </div>
                    <div class="p-4 ${cagrBg} rounded-lg border text-center mb-3">
                        <p class="text-xs text-gray-500 mb-1">年化報酬率 (CAGR)</p>
                        <p class="text-3xl font-bold ${cagrClass}">${cagrIcon} ${cagr !== null ? Math.abs(cagr).toFixed(2) + '%' : '--'}</p>
                    </div>
                    <div class="flex justify-between text-xs text-gray-500 border-t pt-2">
                        <span>起始價: $${ret.start_price.toLocaleString()}</span>
                        <span>配息 ${ret.dividend_count} 次</span>
                        <span>總配息: $${ret.total_dividends.toFixed(2)}</span>
                    </div>
                </div>
            `;
        }
        
        html += `
            </div>
            <div class="mt-4 p-3 bg-blue-50 rounded-lg">
                <p class="text-xs text-blue-600">
                    <i class="fas fa-info-circle mr-1"></i>
                    CAGR 基於 Yahoo Finance 除權息調整後價格計算，<br>
                    已包含配息再投入的複利效果
                </p>
            </div>
        `;
        
        content.innerHTML = html;
    }
    
    function closeReturnsModal() {
        const modal = document.getElementById('returnsModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    // ============================================================
    // 快取管理
    // ============================================================
    
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
    // 導出到全域
    // ============================================================
    
    window.searchStock = searchStock;
    window.searchSymbol = searchSymbol;
    window.renderStockResult = renderStockResult;
    window.toggleCollapsible = toggleCollapsible;
    window.openChartFullscreen = openChartFullscreen;
    window.closeChartFullscreen = closeChartFullscreen;
    window.setChartRange = setChartRange;
    window.renderFullscreenChart = renderFullscreenChart;
    window.renderVolumeChart = renderVolumeChart;
    window.quickAddToWatchlist = quickAddToWatchlist;
    window.loadReturnsModal = loadReturnsModal;
    window.closeReturnsModal = closeReturnsModal;
    window.clearStockCache = clearStockCache;
    window.getStockCacheStats = getStockCacheStats;
    
    console.log('🔍 search.js 模組已載入 (P2 含成交量圖表+MA進階分析)');
})();
