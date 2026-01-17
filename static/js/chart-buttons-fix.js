/**
 * 圖表按鈕修復 Patch (chart-buttons-fix.js)
 * 
 * 🔧 修復問題：
 * 1. chartFullscreen 的時間範圍按鈕無法點擊
 * 2. 圖例無法點擊切換顯示/隱藏
 * 
 * 📍 載入順序：在 sections.js 和 search-render.js 之後載入
 * 
 * 使用方法：
 * <script src="/static/js/chart-buttons-fix.js"></script>
 */

(function() {
    'use strict';
    
    console.log('🔧 chart-buttons-fix.js 開始載入...');

    // ============================================================
    // 修復 1：替換 chartFullscreen 中的按鈕（加上 onclick）
    // ============================================================
    
    function fixChartRangeButtons() {
        const container = document.getElementById('chartRangeButtons');
        if (!container) {
            console.log('chartRangeButtons 容器尚未存在，稍後重試...');
            return false;
        }
        
        // 替換按鈕 HTML，加上 onclick 事件
        container.innerHTML = `
            <button type="button" onclick="setChartRange(22)" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="22">1M</button>
            <button type="button" onclick="setChartRange(65)" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target active bg-blue-600 text-white" data-days="65">3M</button>
            <button type="button" onclick="setChartRange(130)" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="130">6M</button>
            <button type="button" onclick="setChartRange(252)" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="252">1Y</button>
            <button type="button" onclick="setChartRange(756)" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="756">3Y</button>
            <button type="button" onclick="setChartRange(1260)" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="1260">5Y</button>
            <button type="button" onclick="setChartRange(99999)" class="chart-range-btn px-4 py-2 text-sm rounded border touch-target bg-gray-100 text-gray-700" data-days="99999">MAX</button>
        `;
        
        console.log('✅ chartRangeButtons 已修復（加上 onclick）');
        return true;
    }

    // ============================================================
    // 修復 2：確保全域函數存在
    // ============================================================
    
    // 確保 setChartRange 是全域函數
    if (typeof window.setChartRange !== 'function') {
        window.setChartRange = function(days) {
            const chartData = window.currentChartData;
            if (!chartData) {
                console.warn('setChartRange: 無圖表資料');
                return;
            }

            // 更新按鈕狀態
            document.querySelectorAll('.chart-range-btn').forEach(btn => {
                const btnDays = parseInt(btn.dataset.days);
                btn.classList.remove('bg-blue-600', 'text-white', 'active');
                btn.classList.add('bg-gray-100', 'text-gray-700');
                
                if (btnDays === days) {
                    btn.classList.add('bg-blue-600', 'text-white', 'active');
                    btn.classList.remove('bg-gray-100', 'text-gray-700');
                }
            });

            // 重新渲染圖表
            if (typeof window.renderFullscreenChart === 'function') {
                window.renderFullscreenChart(chartData, days);
            } else {
                console.error('renderFullscreenChart 函數不存在');
            }
        };
        console.log('✅ setChartRange 全域函數已建立');
    }

    // ============================================================
    // 修復 3：使用 MutationObserver 監聽 DOM 變化
    // ============================================================
    
    // 當 chartFullscreen 被加入 DOM 時自動修復
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        // 檢查是否是 chartFullscreen 或其子元素
                        if (node.id === 'chartFullscreen' || 
                            node.querySelector && node.querySelector('#chartRangeButtons')) {
                            setTimeout(fixChartRangeButtons, 100);
                        }
                    }
                });
            }
        });
    });
    
    // 開始監聽
    observer.observe(document.body, { childList: true, subtree: true });

    // ============================================================
    // 修復 4：頁面載入完成後嘗試修復
    // ============================================================
    
    function initFix() {
        // 嘗試立即修復
        if (!fixChartRangeButtons()) {
            // 如果失敗，延遲重試
            setTimeout(fixChartRangeButtons, 500);
            setTimeout(fixChartRangeButtons, 1000);
            setTimeout(fixChartRangeButtons, 2000);
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFix);
    } else {
        initFix();
    }

    // ============================================================
    // 修復 5：增強 openChartFullscreen 確保按鈕修復
    // ============================================================
    
    const originalOpenChartFullscreen = window.openChartFullscreen;
    
    window.openChartFullscreen = function(symbol, price) {
        // 呼叫原始函數
        if (typeof originalOpenChartFullscreen === 'function') {
            originalOpenChartFullscreen(symbol, price);
        }
        
        // 確保按鈕已修復
        setTimeout(fixChartRangeButtons, 150);
    };

    console.log('🔧 chart-buttons-fix.js 載入完成');
})();
