/**
 * æœå°‹çµæžœæ¸²æŸ“æ¨¡çµ„ (ä¿®å¾©ç‰ˆ 2026-01-17)
 * 
 * ðŸ”§ ä¿®å¾©ï¼š
 * 1. æ™‚é–“ç¯„åœæŒ‰éˆ•ç„¡æ³•é»žæ“Š - ä½¿ç”¨ onclick ç›´æŽ¥ç¶å®š
 * 2. åœ–ä¾‹ç„¡æ³•é»žæ“Šåˆ‡æ› - å•Ÿç”¨ Chart.js legend onClick
 * 3. åœ–è¡¨å³é‚Šç©ºç™½å¤ªå° - å¢žåŠ  layout.padding
 * 4. chartFullscreenModal â†’ chartFullscreen (æ­£ç¢º ID)
 * 5. chartModalTitle â†’ chartFullscreenTitle (æ­£ç¢º ID)
 */

(function() {
    'use strict';

    // ============================================================
    // è¼”åŠ©å‡½æ•¸
    // ============================================================

    function $(id) {
        return document.getElementById(id);
    }

    function setHtml(id, html) {
        const el = $(id);
        if (el) el.innerHTML = html;
    }

    // ============================================================
    // åœ–è¡¨å¯¦ä¾‹
    // ============================================================

    let fullscreenChartInstance = null;
    let volumeChartInstance = null;
    let currentChartData = null;

    // ============================================================
    // æ¸²æŸ“å…¥å£
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
    // è‚¡ç¥¨çµæžœæ¸²æŸ“
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
        const changeIcon = dayChange >= 0 ? 'â–²' : 'â–¼';
        const changeBg = dayChange >= 0 ? 'bg-green-50' : 'bg-red-50';

        // æ ¼å¼åŒ–åƒ¹æ ¼
        const formatPrice = (p) => {
            if (p == null) return '--';
            if (isTaiwan) return p.toLocaleString();
            return p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        };

        // MA ç‹€æ…‹
        const ma = indicators.ma || {};
        const maAlignment = ma.alignment || 'neutral';
        const maAlignmentText = maAlignment === 'bullish' ? 'å¤šé ­æŽ’åˆ—' : maAlignment === 'bearish' ? 'ç©ºé ­æŽ’åˆ—' : 'ä¸­æ€§';
        const maAlignmentClass = maAlignment === 'bullish' ? 'text-green-600' : maAlignment === 'bearish' ? 'text-red-600' : 'text-gray-600';

        // RSI ç‹€æ…‹
        const rsi = indicators.rsi || {};
        const rsiValue = rsi.value || 50;
        const rsiStatus = rsi.status || 'neutral';
        const rsiClass = rsiStatus === 'overbought' ? 'text-red-600' : rsiStatus === 'oversold' ? 'text-green-600' : 'text-gray-600';
        const rsiText = rsiStatus === 'overbought' ? 'è¶…è²·' : rsiStatus === 'oversold' ? 'è¶…è³£' : 'ä¸­æ€§';

        // MACD ç‹€æ…‹
        const macd = indicators.macd || {};
        const macdStatus = macd.status || 'neutral';
        const macdClass = macdStatus === 'bullish' ? 'text-green-600' : 'text-red-600';
        const macdText = macdStatus === 'bullish' ? 'å¤šé ­' : 'ç©ºé ­';

        // è©•åˆ†
        const rating = score.rating || 'neutral';
        const ratingText = rating === 'bullish' ? 'åå¤š' : rating === 'bearish' ? 'åç©º' : 'ä¸­æ€§';
        const ratingClass = rating === 'bullish' ? 'bg-green-100 text-green-800' : rating === 'bearish' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800';

        const html = `
            <div class="bg-white rounded-xl shadow-lg overflow-hidden">
                <!-- æ¨™é¡Œåˆ— -->
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

                <!-- å¿«é€Ÿæ“ä½œ -->
                <div class="p-4 border-b bg-gray-50">
                    <div class="flex flex-wrap gap-2">
                        <button onclick="quickAddToWatchlist('${symbol}', 'stock')" 
                                class="flex-1 min-w-[100px] py-2 px-3 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                            <i class="fas fa-plus mr-1"></i>è¿½è¹¤
                        </button>
                        <button onclick="openChartFullscreen('${symbol}', ${price})"
                                class="flex-1 min-w-[100px] py-2 px-3 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors">
                            <i class="fas fa-chart-line mr-1"></i>åœ–è¡¨
                        </button>
                        <button onclick="loadReturnsModal('${symbol}')"
                                class="flex-1 min-w-[100px] py-2 px-3 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors">
                            <i class="fas fa-percentage mr-1"></i>å ±é…¬çŽ‡
                        </button>
                    </div>
                </div>

                <!-- æŠ€è¡“æŒ‡æ¨™æ‘˜è¦ -->
                <div class="p-4">
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <p class="text-xs text-gray-500 mb-1">MA æŽ’åˆ—</p>
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
                            <p class="text-xs text-gray-500 mb-1">ç¶œåˆè©•åˆ†</p>
                            <span class="px-2 py-1 rounded text-sm font-medium ${ratingClass}">${ratingText}</span>
                        </div>
                    </div>

                    <!-- æ¼²è·Œå¹… -->
                    <div class="border-t pt-4">
                        <p class="text-sm font-medium text-gray-700 mb-2">å€é–“æ¼²è·Œ</p>
                        <div class="flex flex-wrap gap-2 text-xs">
                            ${renderChangeTag('1é€±', change.week)}
                            ${renderChangeTag('1æœˆ', change.month)}
                            ${renderChangeTag('1å­£', change.quarter)}
                            ${renderChangeTag('1å¹´', change.year)}
                        </div>
                    </div>

                    <!-- MA è©³ç´° -->
                    <div class="border-t pt-4 mt-4">
                        <p class="text-sm font-medium text-gray-700 mb-2">å‡ç·šä½ç½®</p>
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
        const posText = position === 'above' ? 'åƒ¹æ ¼åœ¨ä¸Š' : 'åƒ¹æ ¼åœ¨ä¸‹';
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
    // ðŸ”§ ä¿®å¾©ï¼šå…¨èž¢å¹•åœ–è¡¨ï¼ˆä½¿ç”¨æ­£ç¢ºçš„ IDï¼‰
    // ============================================================

    function openChartFullscreen(symbol, currentPrice) {
        const chartData = window.currentChartData;
        if (!chartData) {
            if (typeof showToast === 'function') {
                showToast('ç„¡åœ–è¡¨è³‡æ–™');
            }
            return;
        }

        // ðŸ”§ ä½¿ç”¨æ­£ç¢ºçš„ ID: chartFullscreen
        const modal = $('chartFullscreen');
        if (!modal) {
            console.error('æ‰¾ä¸åˆ° chartFullscreen å…ƒç´ ');
            return;
        }

        // ðŸ”§ ä½¿ç”¨æ­£ç¢ºçš„ ID: chartFullscreenTitle
        const title = $('chartFullscreenTitle');
        if (title) title.textContent = `${symbol} Technical Analysis`;

        // é¡¯ç¤º Modal
        modal.style.display = 'block';
        modal.classList.add('active');

        // ðŸ”§ æ›´æ–°æŒ‰éˆ•ç‹€æ…‹ï¼ˆé è¨­ 3M = 65å¤©ï¼‰
        updateRangeButtonState(65);

        // é è¨­é¡¯ç¤º 65 å¤© (3M)
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

    // ðŸ”§ æ–°å¢žï¼šæ›´æ–°æŒ‰éˆ•ç‹€æ…‹
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

    // ðŸ”§ ä¿®å¾©ï¼šè¨­å®šåœ–è¡¨ç¯„åœï¼ˆå…¨åŸŸå‡½æ•¸ï¼‰
    window.setChartRange = function(days) {
        const chartData = window.currentChartData;
        if (!chartData) return;

        updateRangeButtonState(days);
        renderFullscreenChart(chartData, days);
    };

    // ============================================================
    // ðŸ”§ ä¿®å¾©ï¼šæ¸²æŸ“å…¨èž¢å¹•åœ–è¡¨ï¼ˆå¢žåŠ å³é‚Šç©ºç™½ + åœ–ä¾‹å¯é»žæ“Šï¼‰
    // ============================================================

    function renderFullscreenChart(chartData, days = 65) {
        const canvas = $('fullscreenChart');
        if (!canvas) {
            console.error('æ‰¾ä¸åˆ° fullscreenChart canvas');
            return;
        }

        if (fullscreenChartInstance) {
            fullscreenChartInstance.destroy();
        }

        const ctx = canvas.getContext('2d');
        const dataLength = chartData.dates.length;
        
        // è™•ç† MAX é¸é …
        const actualDays = days === 99999 ? dataLength : days;
        const startIdx = Math.max(0, dataLength - actualDays);

        // æ—¥æœŸæ ¼å¼åŒ–
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
                label: 'æ”¶ç›¤åƒ¹',
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

        // MA20 - ç´…è‰²
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

        // MA50 - ç¶ è‰²
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

        // MA200 - é»ƒè‰²
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

        // MA250 - ç´«è‰²
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
                // ðŸ”§ å¢žåŠ å³é‚Šç©ºç™½
                layout: {
                    padding: {
                        right: 20,  // ðŸ”§ å¢žåŠ å³é‚Š padding
                        top: 10,
                        bottom: 10,
                        left: 10,
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        // ðŸ”§ å•Ÿç”¨åœ–ä¾‹é»žæ“Šåˆ‡æ›é¡¯ç¤º/éš±è—
                        onClick: function(e, legendItem, legend) {
                            const index = legendItem.datasetIndex;
                            const ci = legend.chart;
                            const meta = ci.getDatasetMeta(index);
                            
                            // åˆ‡æ›é¡¯ç¤ºç‹€æ…‹
                            meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;
                            ci.update();
                        },
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 12,
                            },
                            // ðŸ”§ æ·»åŠ æ¸¸æ¨™æ¨£å¼æç¤ºå¯é»žæ“Š
                            generateLabels: function(chart) {
                                const original = Chart.defaults.plugins.legend.labels.generateLabels;
                                const labels = original.call(this, chart);
                                labels.forEach(label => {
                                    label.pointStyle = 'circle';
                                });
                                return labels;
                            }
                        },
                        // ðŸ”§ æ»‘é¼ ç§»ä¸ŠåŽ»é¡¯ç¤ºæ‰‹æŒ‡æ¸¸æ¨™
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
                            // ðŸ”§ å¢žåŠ ä¸€äº›é¡å¤–ç©ºé–“
                            padding: 8,
                        },
                    },
                },
            },
        });
    }

    // ============================================================
    // å°Žå‡º
    // ============================================================

    window.renderSearchResult = renderSearchResult;
    window.openChartFullscreen = openChartFullscreen;
    window.closeChartFullscreen = closeChartFullscreen;
    window.renderFullscreenChart = renderFullscreenChart;

    console.log('ðŸ“Š search-render.js æ¨¡çµ„å·²è¼‰å…¥ (ä¿®å¾©ç‰ˆ 2026-01-17: æŒ‰éˆ•é»žæ“Š + åœ–ä¾‹äº’å‹• + å³é‚Šç©ºç™½)');
})();