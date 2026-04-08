/**
 * 搜尋圖表模組 (P2 拆分)
 * 
 * 職責：
 * - 全螢幕圖表
 * - 成交量圖表
 * - 圖表互動
 * 
 * 依賴：core.js, Chart.js
 */

(function() {
    'use strict';

    // ============================================================
    // 私有變數
    // ============================================================

    let fullscreenChartInstance = null;
    let volumeChartInstance = null;

    // ============================================================
    // 全螢幕圖表
    // ============================================================

    function openChartFullscreen(symbol, currentPrice) {
        const chartData = window.currentChartData;
        if (!chartData) {
            showToast('無圖表資料');
            return;
        }

        const modal = $('chartFullscreenModal');
        if (!modal) return;

        // 更新標題
        const title = $('chartModalTitle');
        if (title) title.textContent = `${symbol} 技術分析`;

        const priceEl = $('chartModalPrice');
        if (priceEl) priceEl.textContent = `$${currentPrice?.toLocaleString() || '--'}`;

        modal.classList.remove('hidden');
        modal.classList.add('flex');

        // 預設顯示 60 天
        setTimeout(() => renderFullscreenChart(chartData, 60), 100);
    }

    function closeChartFullscreen() {
        const modal = $('chartFullscreenModal');
        if (!modal) return;

        modal.classList.add('hidden');
        modal.classList.remove('flex');

        if (fullscreenChartInstance) {
            fullscreenChartInstance.destroy();
            fullscreenChartInstance = null;
        }
        if (volumeChartInstance) {
            volumeChartInstance.destroy();
            volumeChartInstance = null;
        }
    }

    function setChartRange(days) {
        const chartData = window.currentChartData;
        if (!chartData) return;

        // 更新按鈕狀態
        document.querySelectorAll('.chart-range-btn').forEach(btn => {
            btn.classList.remove('bg-blue-600', 'text-white');
            btn.classList.add('bg-gray-100', 'text-gray-700');
            if (parseInt(btn.dataset.days) === days) {
                btn.classList.add('bg-blue-600', 'text-white');
                btn.classList.remove('bg-gray-100', 'text-gray-700');
            }
        });

        renderFullscreenChart(chartData, days);
    }

    // ============================================================
    // 渲染全螢幕圖表
    // ============================================================

    function renderFullscreenChart(chartData, days = 60) {
        const canvas = $('fullscreenChart');
        if (!canvas) return;

        if (fullscreenChartInstance) {
            fullscreenChartInstance.destroy();
        }

        const ctx = canvas.getContext('2d');
        const dataLength = chartData.dates.length;
        const startIdx = Math.max(0, dataLength - days);

        // 日期格式化
        const formatDate = (d) => {
            if (days <= 30) return d.slice(5);
            if (days <= 130) return d.slice(5);
            return d.slice(2, 7).replace('-', '/');
        };

        const labels = chartData.dates.slice(startIdx).map(formatDate);

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

        // 渲染成交量圖表
        if (chartData.volumes && chartData.volumes.length > 0) {
            renderVolumeChart(chartData, days, labels);
        }
    }

    // ============================================================
    // 渲染成交量圖表
    // ============================================================

    function renderVolumeChart(chartData, days, labels) {
        const volumeCanvas = $('volumeChart');
        if (!volumeCanvas) return;

        // 顯示成交量容器
        const volumeContainer = $('volumeChartContainer');
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
    // 年化報酬率 Modal
    // ============================================================

    async function loadReturnsModal(symbol) {
        const modal = $('returnsModal');
        const content = $('returnsModalContent');
        if (!modal || !content) return;

        modal.classList.remove('hidden');
        modal.classList.add('flex');

        content.innerHTML = `
            <div class="text-center py-8">
                <i class="fas fa-spinner fa-spin text-2xl text-blue-600"></i>
                <p class="mt-2 text-gray-500">載入中...</p>
            </div>
        `;

        try {
            const res = await apiRequest(`/api/stock/${symbol}/returns`);
            const data = await res.json();

            if (!data.success) {
                content.innerHTML = `<p class="text-center text-red-500">${data.detail || '載入失敗'}</p>`;
                return;
            }

            renderReturnsContent(content, data);

        } catch (e) {
            console.error('Returns error:', e);
            content.innerHTML = `<p class="text-center text-red-500">載入失敗: ${e.message}</p>`;
        }
    }

    function renderReturnsContent(content, data) {
        const returns = data.returns || {};
        const cagr = data.cagr || {};

        const html = `
            <h4 class="font-semibold text-lg mb-4">${data.symbol} 歷史報酬率</h4>
            
            <div class="space-y-4">
                <div>
                    <p class="text-sm text-gray-500 mb-2">累積報酬率</p>
                    <div class="grid grid-cols-4 gap-2 text-center">
                        ${['1m', '3m', '6m', '1y'].map(period => {
                            const val = returns[period];
                            const bgClass = val > 0 ? 'bg-green-50' : val < 0 ? 'bg-red-50' : 'bg-gray-50';
                            const textClass = val > 0 ? 'text-green-600' : val < 0 ? 'text-red-600' : 'text-gray-600';
                            const label = period === '1m' ? '1月' : period === '3m' ? '3月' : period === '6m' ? '6月' : '1年';
                            return `
                                <div class="p-2 rounded ${bgClass}">
                                    <p class="text-xs text-gray-500">${label}</p>
                                    <p class="font-bold ${textClass}">${val !== null && val !== undefined ? (val > 0 ? '+' : '') + val.toFixed(1) + '%' : '--'}</p>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                
                <div>
                    <p class="text-sm text-gray-500 mb-2">年化報酬率 (CAGR)</p>
                    <div class="grid grid-cols-4 gap-2 text-center">
                        ${['1y', '3y', '5y', '10y'].map(period => {
                            const val = cagr[`cagr_${period}`];
                            const bgClass = val > 0 ? 'bg-green-50' : val < 0 ? 'bg-red-50' : 'bg-gray-50';
                            const textClass = val > 0 ? 'text-green-600' : val < 0 ? 'text-red-600' : 'text-gray-600';
                            const label = period.replace('y', '年');
                            return `
                                <div class="p-2 rounded ${bgClass}">
                                    <p class="text-xs text-gray-500">${label}</p>
                                    <p class="font-bold ${textClass}">${val !== null && val !== undefined ? (val > 0 ? '+' : '') + val + '%' : '--'}</p>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                
                <p class="text-xs text-gray-400 text-center">
                    CAGR = 年化複合成長率，已包含配息再投入的複利效果
                </p>
            </div>
        `;

        content.innerHTML = html;
    }

    function closeReturnsModal() {
        const modal = $('returnsModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    // ============================================================
    // 導出
    // ============================================================

    // 掛載到 SELA 命名空間
    if (window.SELA && window.SELA.search) {
        Object.assign(window.SELA.search, {
            openChartFullscreen,
            closeChartFullscreen,
            setChartRange,
            loadReturnsModal,
            closeReturnsModal
        });
    }

    // 全域導出（向後兼容）
    window.openChartFullscreen = openChartFullscreen;
    window.closeChartFullscreen = closeChartFullscreen;
    window.setChartRange = setChartRange;
    window.renderFullscreenChart = renderFullscreenChart;
    window.renderVolumeChart = renderVolumeChart;
    window.loadReturnsModal = loadReturnsModal;
    window.closeReturnsModal = closeReturnsModal;

})();
