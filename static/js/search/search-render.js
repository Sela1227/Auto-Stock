/**
 * 搜尋結果渲染模組 (修復版 2026-01-17)
 * 
 * 🔧 修復：
 * 1. 時間範圍按鈕無法點擊 - 使用 onclick 直接綁定
 * 2. 圖例無法點擊切換 - 啟用 Chart.js legend onClick
 * 3. 圖表右邊空白太小 - 增加 layout.padding
 * 4. chartFullscreenModal → chartFullscreen (正確 ID)
 * 5. chartModalTitle → chartFullscreenTitle (正確 ID)
 */

(function() {
    'use strict';

    // ============================================================
    // 輔助函數
    // ============================================================

    function $(id) {
        return document.getElementById(id);
    }

    function setHtml(id, html) {
        const el = $(id);
        if (el) el.innerHTML = html;
    }

    // ============================================================
    // 圖表實例
    // ============================================================

    let fullscreenChartInstance = null;
    let volumeChartInstance = null;
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

    function renderStockResult(data, isCrypto, isTaiwan) {
        const symbol = data.symbol;
        const name = data.name || symbol;
        const price = data.price?.current || 0;
        const change = data.change || {};
        const indicators = data.indicators || {};
        const score = data.score || {};

        const dayChange = change.day;
        const changeClass = dayChange >= 0 ? 'text-green-600' : 'text-red-600';
        const changeIcon = dayChange >= 0 ? '▲' : '▼';
        const changeBg = dayChange >= 0 ? 'bg-green-50' : 'bg-red-50';

        // 格式化價格
        const formatPrice = (p) => {
            if (p == null) return '--';
            if (isTaiwan) return p.toLocaleString();
            return p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        };

        // MA 狀態
        const ma = indicators.ma || {};
        const maAlignment = ma.alignment || 'neutral';
        const maAlignmentText = maAlignment === 'bullish' ? '多頭排列' : maAlignment === 'bearish' ? '空頭排列' : '中性';
        const maAlignmentClass = maAlignment === 'bullish' ? 'text-green-600' : maAlignment === 'bearish' ? 'text-red-600' : 'text-gray-600';

        // RSI 狀態
        const rsi = indicators.rsi || {};
        const rsiValue = rsi.value || 50;
        const rsiStatus = rsi.status || 'neutral';
        const rsiClass = rsiStatus === 'overbought' ? 'text-red-600' : rsiStatus === 'oversold' ? 'text-green-600' : 'text-gray-600';
        const rsiText = rsiStatus === 'overbought' ? '超買' : rsiStatus === 'oversold' ? '超賣' : '中性';

        // MACD 狀態
        const macd = indicators.macd || {};
        const macdStatus = macd.status || 'neutral';
        const macdClass = macdStatus === 'bullish' ? 'text-green-600' : 'text-red-600';
        const macdText = macdStatus === 'bullish' ? '多頭' : '空頭';

        // 評分
        const rating = score.rating || 'neutral';
        const ratingText = rating === 'bullish' ? '偏多' : rating === 'bearish' ? '偏空' : '中性';
        const ratingClass = rating === 'bullish' ? 'bg-green-100 text-green-800' : rating === 'bearish' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800';

        const html = `
            <div class="bg-white rounded-xl shadow-lg overflow-hidden">
                <!-- 標題列 -->
                <div class="p-4 ${changeBg} border-b">
                    <div class="flex items-center justify-between">
                        <div>
                            <h2 class="text-xl font-bold text-gray-800">${symbol}</h2>
                            <p class="text-sm text-gray-600">${name}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-2xl font-bold text-gray-800">${isTaiwan ? '' : '$'}${formatPrice(price)}</p>
                            <p class="${changeClass} text-sm font-medium">
                                ${changeIcon} ${dayChange != null ? Math.abs(dayChange).toFixed(2) + '%' : '--'}
                            </p>
                        </div>
                    </div>
                </div>

                <!-- 快速操作 -->
                <div class="p-4 border-b bg-gray-50">
                    <div class="flex flex-wrap gap-2">
                        <button onclick="quickAddToWatchlist('${symbol}', 'stock')" 
                                class="flex-1 min-w-[100px] py-2 px-3 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                            <i class="fas fa-plus mr-1"></i>追蹤
                        </button>
                        <button onclick="openChartFullscreen('${symbol}', ${price})"
                                class="flex-1 min-w-[100px] py-2 px-3 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors">
                            <i class="fas fa-chart-line mr-1"></i>圖表
                        </button>
                        <button onclick="loadReturnsModal('${symbol}')"
                                class="flex-1 min-w-[100px] py-2 px-3 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors">
                            <i class="fas fa-percentage mr-1"></i>報酬率
                        </button>
                    </div>
                </div>

                <!-- 技術指標摘要 -->
                <div class="p-4">
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <p class="text-xs text-gray-500 mb-1">MA 排列</p>
                            <p class="font-bold ${maAlignmentClass}">${maAlignmentText}</p>
                        </div>
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <p class="text-xs text-gray-500 mb-1">RSI(14)</p>
                            <p class="font-bold ${rsiClass}">${rsiValue.toFixed(1)} ${rsiText}</p>
                        </div>
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <p class="text-xs text-gray-500 mb-1">MACD</p>
                            <p class="font-bold ${macdClass}">${macdText}</p>
                        </div>
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <p class="text-xs text-gray-500 mb-1">綜合評分</p>
                            <span class="px-2 py-1 rounded text-sm font-medium ${ratingClass}">${ratingText}</span>
                        </div>
                    </div>

                    <!-- 漲跌幅 -->
                    <div class="border-t pt-4">
                        <p class="text-sm font-medium text-gray-700 mb-2">區間漲跌</p>
                        <div class="flex flex-wrap gap-2 text-xs">
                            ${renderChangeTag('1週', change.week)}
                            ${renderChangeTag('1月', change.month)}
                            ${renderChangeTag('1季', change.quarter)}
                            ${renderChangeTag('1年', change.year)}
                        </div>
                    </div>

                    <!-- MA 詳細 -->
                    <div class="border-t pt-4 mt-4">
                        <p class="text-sm font-medium text-gray-700 mb-2">均線位置</p>
                        <div class="space-y-1 text-xs">
                            ${renderMARow('MA20', ma.ma20, ma.price_vs_ma20, price)}
                            ${renderMARow('MA50', ma.ma50, ma.price_vs_ma50, price)}
                            ${renderMARow('MA200', ma.ma200, ma.price_vs_ma200, price)}
                        </div>
                    </div>
                </div>
            </div>
        `;

        setHtml('searchResult', html);
    }

    function renderChangeTag(label, value) {
        if (value == null) return `<span class="px-2 py-1 bg-gray-100 text-gray-500 rounded">${label}: --</span>`;
        const cls = value >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';
        const sign = value >= 0 ? '+' : '';
        return `<span class="px-2 py-1 ${cls} rounded">${label}: ${sign}${value.toFixed(2)}%</span>`;
    }

    function renderMARow(label, maValue, position, currentPrice) {
        if (maValue == null) return '';
        const posClass = position === 'above' ? 'text-green-600' : 'text-red-600';
        const posText = position === 'above' ? '價格在上' : '價格在下';
        const diff = currentPrice && maValue ? ((currentPrice - maValue) / maValue * 100).toFixed(2) : '--';
        return `
            <div class="flex justify-between items-center py-1">
                <span class="text-gray-600">${label}</span>
                <span class="text-gray-800">${maValue.toFixed(2)}</span>
                <span class="${posClass}">${posText} (${diff}%)</span>
            </div>
        `;
    }

    // ============================================================
    // 🔧 修復：全螢幕圖表（使用正確的 ID）
    // ============================================================

    function openChartFullscreen(symbol, currentPrice) {
        const chartData = window.currentChartData;
        if (!chartData) {
            if (typeof showToast === 'function') {
                showToast('無圖表資料');
            }
            return;
        }

        // 🔧 使用正確的 ID: chartFullscreen
        const modal = $('chartFullscreen');
        if (!modal) {
            console.error('找不到 chartFullscreen 元素');
            return;
        }

        // 🔧 使用正確的 ID: chartFullscreenTitle
        const title = $('chartFullscreenTitle');
        if (title) title.textContent = `${symbol} Technical Analysis`;

        // 顯示 Modal
        modal.style.display = 'block';
        modal.classList.add('active');

        // 🔧 更新按鈕狀態（預設 3M = 65天）
        updateRangeButtonState(65);

        // 預設顯示 65 天 (3M)
        setTimeout(() => renderFullscreenChart(chartData, 65), 100);
    }

    function closeChartFullscreen() {
        const modal = $('chartFullscreen');
        if (!modal) return;

        modal.style.display = 'none';
        modal.classList.remove('active');

        if (fullscreenChartInstance) {
            fullscreenChartInstance.destroy();
            fullscreenChartInstance = null;
        }
    }

    // 🔧 新增：更新按鈕狀態
    function updateRangeButtonState(days) {
        document.querySelectorAll('.chart-range-btn').forEach(btn => {
            const btnDays = parseInt(btn.dataset.days);
            btn.classList.remove('bg-blue-600', 'text-white', 'active');
            btn.classList.add('bg-gray-100', 'text-gray-700');
            
            if (btnDays === days) {
                btn.classList.add('bg-blue-600', 'text-white', 'active');
                btn.classList.remove('bg-gray-100', 'text-gray-700');
            }
        });
    }

    // 🔧 修復：設定圖表範圍（全域函數）
    window.setChartRange = function(days) {
        const chartData = window.currentChartData;
        if (!chartData) return;

        updateRangeButtonState(days);
        renderFullscreenChart(chartData, days);
    };

    // ============================================================
    // 🔧 修復：渲染全螢幕圖表（增加右邊空白 + 圖例可點擊）
    // ============================================================

    function renderFullscreenChart(chartData, days = 65) {
        const canvas = $('fullscreenChart');
        if (!canvas) {
            console.error('找不到 fullscreenChart canvas');
            return;
        }

        if (fullscreenChartInstance) {
            fullscreenChartInstance.destroy();
        }

        const ctx = canvas.getContext('2d');
        const dataLength = chartData.dates.length;
        
        // 處理 MAX 選項
        const actualDays = days === 99999 ? dataLength : days;
        const startIdx = Math.max(0, dataLength - actualDays);

        // 日期格式化
        const formatDate = (d) => {
            if (!d) return '';
            if (actualDays <= 30) return d.slice(5);      // MM-DD
            if (actualDays <= 130) return d.slice(5);     // MM-DD
            return d.slice(2, 7).replace('-', '/');       // YY/MM
        };

        const labels = chartData.dates.slice(startIdx).map(formatDate);
        const prices = chartData.prices.slice(startIdx);
        const ma20 = chartData.ma20?.slice(startIdx) || [];
        const ma50 = chartData.ma50?.slice(startIdx) || [];
        const ma200 = chartData.ma200?.slice(startIdx) || [];
        const ma250 = chartData.ma250?.slice(startIdx) || [];

        const datasets = [
            {
                label: '收盤價',
                data: prices,
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1,
                pointRadius: 0,
                pointHoverRadius: 4,
            }
        ];

        // MA20 - 紅色
        if (ma20.length > 0 && ma20.some(v => v != null)) {
            datasets.push({
                label: 'MA20',
                data: ma20,
                borderColor: '#EF4444',
                borderWidth: 1.5,
                fill: false,
                tension: 0.1,
                pointRadius: 0,
            });
        }

        // MA50 - 綠色
        if (ma50.length > 0 && ma50.some(v => v != null)) {
            datasets.push({
                label: 'MA50',
                data: ma50,
                borderColor: '#10B981',
                borderWidth: 1.5,
                fill: false,
                tension: 0.1,
                pointRadius: 0,
            });
        }

        // MA200 - 黃色
        if (ma200.length > 0 && ma200.some(v => v != null)) {
            datasets.push({
                label: 'MA200',
                data: ma200,
                borderColor: '#EAB308',
                borderWidth: 1.5,
                fill: false,
                tension: 0.1,
                pointRadius: 0,
            });
        }

        // MA250 - 紫色
        if (ma250.length > 0 && ma250.some(v => v != null)) {
            datasets.push({
                label: 'MA250',
                data: ma250,
                borderColor: '#A855F7',
                borderWidth: 1.5,
                fill: false,
                tension: 0.1,
                pointRadius: 0,
            });
        }

        fullscreenChartInstance = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                // 🔧 增加右邊空白
                layout: {
                    padding: {
                        right: 20,  // 🔧 增加右邊 padding
                        top: 10,
                        bottom: 10,
                        left: 10,
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        // 🔧 啟用圖例點擊切換顯示/隱藏
                        onClick: function(e, legendItem, legend) {
                            const index = legendItem.datasetIndex;
                            const ci = legend.chart;
                            const meta = ci.getDatasetMeta(index);
                            
                            // 切換顯示狀態
                            meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;
                            ci.update();
                        },
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 12,
                            },
                            // 🔧 添加游標樣式提示可點擊
                            generateLabels: function(chart) {
                                const original = Chart.defaults.plugins.legend.labels.generateLabels;
                                const labels = original.call(this, chart);
                                labels.forEach(label => {
                                    label.pointStyle = 'circle';
                                });
                                return labels;
                            }
                        },
                        // 🔧 滑鼠移上去顯示手指游標
                        onHover: function(e) {
                            e.native.target.style.cursor = 'pointer';
                        },
                        onLeave: function(e) {
                            e.native.target.style.cursor = 'default';
                        },
                    },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: function(context) {
                                if (context.raw === null || context.raw === undefined) return null;
                                return `${context.dataset.label}: $${context.raw.toFixed(2)}`;
                            }
                        }
                    },
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false,
                        },
                        ticks: {
                            maxTicksLimit: actualDays <= 60 ? 8 : 10,
                            maxRotation: 0,
                            font: { size: 10 },
                        },
                    },
                    y: {
                        display: true,
                        position: 'right',
                        grid: {
                            color: 'rgba(0,0,0,0.05)',
                        },
                        ticks: {
                            font: { size: 10 },
                            // 🔧 增加一些額外空間
                            padding: 8,
                        },
                    },
                },
            },
        });
    }

    // ============================================================
    // 導出
    // ============================================================

    window.renderSearchResult = renderSearchResult;
    window.openChartFullscreen = openChartFullscreen;
    window.closeChartFullscreen = closeChartFullscreen;
    window.renderFullscreenChart = renderFullscreenChart;

    console.log('📊 search-render.js 模組已載入 (修復版 2026-01-17: 按鈕點擊 + 圖例互動 + 右邊空白)');
})();
