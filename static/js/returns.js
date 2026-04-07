/**
 * 年化報酬率模組
 */

(function() {
    'use strict';
    
    /**
     * 載入年化報酬率 Modal
     */
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
    
    /**
     * 渲染報酬率內容
     */
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
    
    /**
     * 關閉 Modal
     */
    function closeReturnsModal() {
        const modal = document.getElementById('returnsModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }
    
    // 導出到全域
    window.loadReturnsModal = loadReturnsModal;
    window.renderReturnsModal = renderReturnsModal;
    window.closeReturnsModal = closeReturnsModal;
    
    console.log('📊 returns.js 模組已載入');
})();
