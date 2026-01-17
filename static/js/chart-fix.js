/**
 * Chart Fullscreen Fix
 * Fixes openChartFullscreen using wrong DOM IDs
 */
(function() {
    'use strict';

    window.openChartFullscreen = function(symbol, currentPrice) {
        const chartData = window.currentChartData;
        if (!chartData) {
            if (typeof showToast === 'function') {
                showToast('No chart data');
            }
            return;
        }
        
        // Correct ID: chartFullscreen (not chartFullscreenModal)
        const modal = document.getElementById('chartFullscreen');
        if (!modal) return;
        
        // Correct ID: chartFullscreenTitle (not chartModalTitle)
        const title = document.getElementById('chartFullscreenTitle');
        if (title) title.textContent = symbol + ' Technical Analysis';
        
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

    console.log('chart-fix.js loaded');
})();
