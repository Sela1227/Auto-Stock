/**
 * Chart Fullscreen 修復
 * 修正 openChartFullscreen 使用錯誤的 DOM ID
 */
(function() {
    'use strict';

    window.openChartFullscreen = function(symbol, currentPrice) {
        const chartData = window.currentChartData;
        if (!chartData) {
            if (typeof showToast === 'function') {
                showToast('無圖表資料');
            }
            return;
        }
        
        // 正確的 ID: chartFullscreen (不是 chartFullscreenModal)
        const modal = document.getElementById('chartFullscreen');
        if (!modal) return;
        
        // 正確的 ID: chartFullscreenTitle (不是 chartModalTitle)
        const title = document.getElementById('chartFullscreenTitle');
        if (title) title.textContent = symbol + ' 技術分析';
        
        modal.style.display = 'block';
        modal.classList.add('active');
        
        setTimeout(function() {
            if (typeof renderFullscreenChart === 'function') {
                renderFullscreenChart(chartData, 65);
            }
        }, 100);
    };

    window.closeChartFullscreen = function() {
        const modal = document.getElementById('chartFullscreen');
        if (!modal) return;
        
        modal.style.display = 'none';
        modal.classList.remove('active');
        
        if (window.fullscreenChartInstance) {
            window.fullscreenChartInstance.destroy();
            window.fullscreenChartInstance = null;
        }
    };

    console.log('✅ chart-fix.js 已載入');
})();
