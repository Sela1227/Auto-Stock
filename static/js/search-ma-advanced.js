/**
 * MA 進階分析渲染模組
 */
(function() {
    'use strict';

    function renderMAAdvanced(ma) {
        if (!ma) return '';
        let html = '<div class="ma-advanced-container">';
        html += renderCrossSignals(ma);
        html += renderMADistances(ma);
        html += renderAlignment(ma);
        html += renderSupportResistance(ma);
        html += '</div>';
        return html;
    }

    function renderCrossSignals(ma) {
        const signals = [];
        if (ma.golden_cross_20_50) signals.push({ type: 'golden', label: 'MA20↗MA50', days: ma.golden_cross_20_50_days });
        if (ma.death_cross_20_50) signals.push({ type: 'death', label: 'MA20↘MA50', days: ma.death_cross_20_50_days });
        if (ma.golden_cross_50_200) signals.push({ type: 'golden', label: 'MA50↗MA200', days: ma.golden_cross_50_200_days });
        if (ma.death_cross_50_200) signals.push({ type: 'death', label: 'MA50↘MA200', days: ma.death_cross_50_200_days });
        
        if (signals.length === 0) return '';
        
        let html = '<div class="mb-4"><div class="flex items-center mb-2"><i class="fas fa-exchange-alt text-blue-500 mr-2"></i><span class="text-sm font-medium text-gray-700">交叉訊號</span></div><div class="flex flex-wrap gap-2">';
        for (const s of signals) {
            const cls = s.type === 'golden' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';
            const icon = s.type === 'golden' ? '🔺' : '🔻';
            html += `<span class="px-2 py-1 rounded text-xs ${cls}">${icon} ${s.label}`;
            if (s.days) html += ` (${s.days}天前)`;
            html += '</span>';
        }
        html += '</div></div>';
        return html;
    }

    function renderMADistances(ma) {
        const distances = [];
        if (ma.dist_ma20 !== undefined) distances.push({ label: 'MA20', value: ma.dist_ma20 });
        if (ma.dist_ma50 !== undefined) distances.push({ label: 'MA50', value: ma.dist_ma50 });
        if (ma.dist_ma200 !== undefined) distances.push({ label: 'MA200', value: ma.dist_ma200 });
        
        if (distances.length === 0) return '';
        
        let html = '<div class="mb-4"><div class="flex items-center mb-2"><i class="fas fa-ruler-horizontal text-purple-500 mr-2"></i><span class="text-sm font-medium text-gray-700">距離均線</span></div><div class="grid grid-cols-3 gap-2">';
        for (const d of distances) {
            const cls = d.value > 0 ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600';
            const sign = d.value > 0 ? '+' : '';
            html += `<div class="p-2 rounded text-center ${cls}"><div class="text-xs text-gray-500">${d.label}</div><div class="font-bold">${sign}${d.value.toFixed(2)}%</div></div>`;
        }
        html += '</div></div>';
        return html;
    }

    function renderAlignment(ma) {
        if (!ma.alignment_detail) return '';
        const status = ma.alignment_status || 'neutral';
        const cls = status === 'bullish' ? 'bg-green-100 text-green-700' : status === 'bearish' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700';
        const icon = status === 'bullish' ? '📈' : status === 'bearish' ? '📉' : '📊';
        
        let html = '<div class="mb-4"><div class="flex items-center mb-2"><i class="fas fa-layer-group text-orange-500 mr-2"></i><span class="text-sm font-medium text-gray-700">均線排列</span></div>';
        html += `<span class="px-3 py-2 rounded-lg ${cls} inline-flex items-center">${icon} ${ma.alignment_detail}`;
        if (ma.alignment_score !== undefined) html += ` <span class="ml-2 text-xs opacity-75">(${ma.alignment_score}/4)</span>`;
        html += '</span></div>';
        return html;
    }

    function renderSupportResistance(ma) {
        if (!ma.nearest_support && !ma.nearest_resistance) return '';
        
        let html = '<div class="mb-4"><div class="flex items-center mb-2"><i class="fas fa-arrows-alt-v text-cyan-500 mr-2"></i><span class="text-sm font-medium text-gray-700">支撐/壓力</span></div><div class="grid grid-cols-2 gap-2">';
        
        html += '<div class="p-2 rounded bg-green-50 border border-green-200"><div class="text-xs text-green-600 mb-1">📗 支撐</div>';
        if (ma.nearest_support) {
            html += `<div class="font-bold text-green-700">${ma.nearest_support.ma}</div><div class="text-sm text-green-600">${ma.nearest_support.price}</div>`;
        } else {
            html += '<div class="text-gray-400 text-sm">-</div>';
        }
        html += '</div>';
        
        html += '<div class="p-2 rounded bg-red-50 border border-red-200"><div class="text-xs text-red-600 mb-1">📕 壓力</div>';
        if (ma.nearest_resistance) {
            html += `<div class="font-bold text-red-700">${ma.nearest_resistance.ma}</div><div class="text-sm text-red-600">${ma.nearest_resistance.price}</div>`;
        } else {
            html += '<div class="text-gray-400 text-sm">-</div>';
        }
        html += '</div></div></div>';
        
        return html;
    }

    function getMAAdvancedSummary(ma) {
        if (!ma) return '';
        const parts = [];
        if (ma.alignment_detail) parts.push(ma.alignment_detail);
        if (ma.golden_cross_20_50) parts.push(`MA20/50黃金交叉(${ma.golden_cross_20_50_days}天前)`);
        if (ma.death_cross_20_50) parts.push(`MA20/50死亡交叉(${ma.death_cross_20_50_days}天前)`);
        return parts.slice(0, 2).join('，');
    }

    window.renderMAAdvanced = renderMAAdvanced;
    window.getMAAdvancedSummary = getMAAdvancedSummary;
})();
