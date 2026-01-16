/**
 * Chart Fullscreen 修復
 * 修正 openChartFullscreen 和 closeChartFullscreen 函數
 * 確保使用正確的 DOM 元素 ID
 */

(function() {
    'use strict';

    // 覆寫 openChartFullscreen 函數
    window.openChartFullscreen = function(symbol, currentPrice) {
        const chartData = window.currentChartData;
        if (!chartData) {
            if (typeof showToast === 'function') {
                showToast('無圖表資料');
            }
            return;
        }

        // 使用正確的 ID: chartFullscreen (不是 chartFullscreenModal)
        const modal = document.getElementById('chartFullscreen');
        if (!modal) {
            console.error('找不到 chartFullscreen 元素');
            return;
        }

        // 使用正確的 ID: chartFullscreenTitle
        const title = document.getElementById('chartFullscreenTitle');
        if (title) {
            title.textContent = symbol + ' 技術分析';
        }

        // 顯示 modal
        modal.style.display = 'block';
        modal.classList.add('active');

        // 預設顯示 65 天 (3M)
        setTimeout(function() {
            if (typeof renderFullscreenChart === 'function') {
                renderFullscreenChart(chartData, 65);
            }
        }, 100);
    };

    // 覆寫 closeChartFullscreen 函數
    window.closeChartFullscreen = function() {
        const modal = document.getElementById('chartFullscreen');
        if (!modal) return;

        modal.style.display = 'none';
        modal.classList.remove('active');

        // 清理 chart instance
        if (window.fullscreenChartInstance) {
            window.fullscreenChartInstance.destroy();
            window.fullscreenChartInstance = null;
        }
    };

    console.log('✅ chart-fix.js 已載入 - openChartFullscreen/closeChartFullscreen 已修正');
})();
