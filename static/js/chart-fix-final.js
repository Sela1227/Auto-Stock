/**
 * SELA 圖表終極修復 (chart-fix-final.js)
 * 自動生成於 2026-01-17 11:30:19
 */
(function() {
    'use strict';
    console.log('🔧 [FINAL] chart-fix-final.js 載入中...');

    var _chart = null;
    var _initialized = false;

    function safeSlice(arr, start) {
        if (!arr || !Array.isArray(arr)) return [];
        return arr.slice(start);
    }

    function hasValid(arr) {
        if (!arr || arr.length === 0) return false;
        for (var i = 0; i < arr.length; i++) {
            if (arr[i] !== null && arr[i] !== undefined && !isNaN(arr[i])) return true;
        }
        return false;
    }

    function _render(data, days) {
        console.log('📊 [FINAL] _render days=' + days);
        
        var canvas = document.getElementById('fullscreenChart');
        if (!canvas) { console.error('[FINAL] 找不到 canvas'); return; }

        if (_chart) { try { _chart.destroy(); } catch(e) {} _chart = null; }

        if (!data || !data.dates || data.dates.length === 0) {
            console.error('[FINAL] 無效資料');
            return;
        }

        var ctx = canvas.getContext('2d');
        var len = data.dates.length;
        days = days || 65;
        var actualDays = (days >= 99999 || days > len) ? len : days;
        var start = Math.max(0, len - actualDays);

        var fmt = function(d) {
            if (!d) return '';
            var s = String(d);
            return actualDays <= 130 ? s.slice(5) : s.slice(2, 7).replace('-', '/');
        };

        var labels = safeSlice(data.dates, start).map(fmt);
        var prices = safeSlice(data.prices, start);
        var ma20 = safeSlice(data.ma20, start);
        var ma50 = safeSlice(data.ma50, start);
        var ma200 = safeSlice(data.ma200, start);
        var ma250 = safeSlice(data.ma250, start);

        console.log('📊 [FINAL] MA:', { ma20: hasValid(ma20), ma50: hasValid(ma50), ma200: hasValid(ma200) });

        var datasets = [{
            label: '收盤價', data: prices, borderColor: '#3B82F6',
            backgroundColor: 'rgba(59,130,246,0.1)', borderWidth: 2,
            fill: true, tension: 0.1, pointRadius: 0, order: 5
        }];

        if (hasValid(ma20)) datasets.push({ label: 'MA20', data: ma20, borderColor: '#EF4444', borderWidth: 1.5, fill: false, tension: 0.1, pointRadius: 0, order: 4 });
        if (hasValid(ma50)) datasets.push({ label: 'MA50', data: ma50, borderColor: '#10B981', borderWidth: 1.5, fill: false, tension: 0.1, pointRadius: 0, order: 3 });
        if (hasValid(ma200)) datasets.push({ label: 'MA200', data: ma200, borderColor: '#EAB308', borderWidth: 1.5, fill: false, tension: 0.1, pointRadius: 0, order: 2 });
        if (hasValid(ma250)) datasets.push({ label: 'MA250', data: ma250, borderColor: '#A855F7', borderWidth: 1.5, fill: false, tension: 0.1, pointRadius: 0, order: 1 });

        try {
            _chart = new Chart(ctx, {
                type: 'line',
                data: { labels: labels, datasets: datasets },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    layout: { padding: { right: 30, top: 10, bottom: 10, left: 10 } },
                    plugins: {
                        legend: {
                            display: true, position: 'top',
                            labels: { usePointStyle: true, padding: 15 },
                            onClick: function(e, item, legend) {
                                var meta = legend.chart.getDatasetMeta(item.datasetIndex);
                                meta.hidden = !meta.hidden;
                                legend.chart.update();
                            },
                            onHover: function(e) { e.native.target.style.cursor = 'pointer'; }
                        },
                        tooltip: { enabled: true }
                    },
                    scales: {
                        x: { display: true, grid: { display: false }, ticks: { maxTicksLimit: 10, maxRotation: 0 } },
                        y: { display: true, position: 'right', grid: { color: 'rgba(0,0,0,0.05)' } }
                    }
                }
            });
            console.log('✅ [FINAL] 圖表完成');
        } catch(e) { console.error('[FINAL] Chart error:', e); }
    }

    function _setRange(days) {
        console.log('📊 [FINAL] _setRange days=' + days);
        var data = window.currentChartData;
        if (!data) { console.error('[FINAL] 無 currentChartData'); return; }

        var btns = document.querySelectorAll('.chart-range-btn');
        for (var i = 0; i < btns.length; i++) {
            var btn = btns[i];
            var d = parseInt(btn.getAttribute('data-days')) || 0;
            btn.className = 'chart-range-btn px-4 py-2 text-sm rounded border touch-target ' +
                (d === days ? 'active bg-blue-600 text-white' : 'bg-gray-100 text-gray-700');
        }
        _render(data, days);
    }

    function _open(symbol, price) {
        console.log('📊 [FINAL] _open symbol=' + symbol);
        var data = window.currentChartData;
        if (!data) { alert('無圖表資料'); return; }

        var modal = document.getElementById('chartFullscreen');
        if (!modal) { console.error('[FINAL] 找不到 modal'); return; }

        var title = document.getElementById('chartFullscreenTitle');
        if (title) title.textContent = symbol + ' Technical Analysis';

        modal.style.display = 'block';
        modal.classList.add('active');

        setTimeout(function() { _fixBtns(); _setRange(65); }, 100);
    }

    function _close() {
        var modal = document.getElementById('chartFullscreen');
        if (modal) { modal.style.display = 'none'; modal.classList.remove('active'); }
        if (_chart) { try { _chart.destroy(); } catch(e) {} _chart = null; }
    }

    function _fixBtns() {
        var c = document.getElementById('chartRangeButtons');
        if (!c) return;
        c.innerHTML = '<button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="22">1M</button>' +
            '<button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target active bg-blue-600 text-white" data-days="65">3M</button>' +
            '<button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="130">6M</button>' +
            '<button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="252">1Y</button>' +
            '<button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="756">3Y</button>' +
            '<button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="1260">5Y</button>' +
            '<button type="button" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="99999">MAX</button>';
    }

    function install() {
        if (_initialized) return;
        _initialized = true;
        delete window.setChartRange; delete window.renderFullscreenChart;
        delete window.openChartFullscreen; delete window.closeChartFullscreen;
        try {
            Object.defineProperty(window, 'setChartRange', { value: _setRange, writable: false, configurable: true });
            Object.defineProperty(window, 'renderFullscreenChart', { value: _render, writable: false, configurable: true });
            Object.defineProperty(window, 'openChartFullscreen', { value: _open, writable: false, configurable: true });
            Object.defineProperty(window, 'closeChartFullscreen', { value: _close, writable: false, configurable: true });
        } catch(e) {
            window.setChartRange = _setRange;
            window.renderFullscreenChart = _render;
            window.openChartFullscreen = _open;
            window.closeChartFullscreen = _close;
        }
        _fixBtns();
        console.log('✅ [FINAL] 函數安裝完成');
    }

    document.addEventListener('click', function(e) {
        var t = e.target;
        while (t && t !== document) {
            if (t.classList && t.classList.contains('chart-range-btn')) {
                e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation();
                var days = parseInt(t.getAttribute('data-days')) || 65;
                _setRange(days);
                return false;
            }
            t = t.parentNode;
        }
    }, true);

    function init() {
        install();
        setTimeout(install, 100);
        setTimeout(install, 500);
        setTimeout(install, 1000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else { init(); }

    window.addEventListener('load', function() { setTimeout(install, 100); });

    console.log('✅ [FINAL] chart-fix-final.js 載入完成');
})();
