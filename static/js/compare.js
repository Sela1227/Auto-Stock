/**
 * 走勢比較模組
 */

(function() {
    'use strict';
    
    let compareChart = null;
    const compareColors = [
        '#3B82F6', // 藍
        '#EF4444', // 紅
        '#10B981', // 綠
        '#F59E0B', // 橙
        '#8B5CF6', // 紫
    ];
    
    /**
     * 新增比較標的
     */
    function addCompareSymbol(symbol) {
        const input = document.getElementById('compareSymbols');
        if (!input) return;
        
        const current = input.value.trim();
        const symbols = current ? current.split(',').map(s => s.trim().toUpperCase()) : [];
        
        if (!symbols.includes(symbol.toUpperCase())) {
            if (symbols.length >= 5) {
                showToast('最多只能比較 5 個標的');
                return;
            }
            symbols.push(symbol.toUpperCase());
            input.value = symbols.join(', ');
            updateSelectedSymbols();
        }
    }
    
    /**
     * 移除比較標的
     */
    function removeCompareSymbol(symbol) {
        const input = document.getElementById('compareSymbols');
        if (!input) return;
        
        const current = input.value.trim();
        const symbols = current ? current.split(',').map(s => s.trim().toUpperCase()) : [];
        const filtered = symbols.filter(s => s !== symbol.toUpperCase());
        input.value = filtered.join(', ');
        updateSelectedSymbols();
    }
    
    /**
     * 更新已選擇的標的顯示
     */
    function updateSelectedSymbols() {
        const input = document.getElementById('compareSymbols');
        const container = document.getElementById('selectedSymbols');
        if (!input || !container) return;
        
        const current = input.value.trim();
        const symbols = current ? current.split(',').map(s => s.trim().toUpperCase()).filter(s => s) : [];
        
        if (symbols.length === 0) {
            container.innerHTML = '';
            return;
        }
        
        container.innerHTML = symbols.map((s, i) => `
            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm" 
                  style="background-color: ${compareColors[i % compareColors.length]}20; 
                         color: ${compareColors[i % compareColors.length]}; 
                         border: 1px solid ${compareColors[i % compareColors.length]}">
                ${s}
                <button onclick="removeCompareSymbol('${s}')" class="ml-2 hover:opacity-70">
                    <i class="fas fa-times text-xs"></i>
                </button>
            </span>
        `).join('');
    }
    
    /**
     * 載入比較圖表
     */
    async function loadCompareChart() {
        const input = document.getElementById('compareSymbols');
        const daysSelect = document.getElementById('compareDays');
        const symbols = input?.value?.trim();
        const days = daysSelect?.value || 90;
        
        if (!symbols) {
            showToast('請輸入至少一個股票代號');
            return;
        }
        
        // 顯示載入中
        const placeholder = document.getElementById('compareChartPlaceholder');
        const container = document.getElementById('compareChartContainer');
        const loading = document.getElementById('compareChartLoading');
        const resultTable = document.getElementById('compareResultTable');
        
        if (placeholder) placeholder.classList.add('hidden');
        if (container) container.classList.add('hidden');
        if (loading) loading.classList.remove('hidden');
        if (resultTable) resultTable.classList.add('hidden');
        
        try {
            const res = await apiRequest(`/api/stock/compare/history?symbols=${encodeURIComponent(symbols)}&days=${days}`);
            const data = await res.json();
            
            if (!data.success) {
                throw new Error(data.detail || '取得資料失敗');
            }
            
            // ✅ 修正：後端返回 data.data 直接是股票字典，不是 data.data.stocks
            const stocks = data.data;
            const symbolList = Object.keys(stocks);
            
            if (symbolList.length === 0) {
                throw new Error('找不到任何有效資料');
            }
            
            // 準備圖表資料
            const datasets = [];
            let tableHtml = '';
            
            symbolList.forEach((sym, idx) => {
                const stock = stocks[sym];
                const color = compareColors[idx % compareColors.length];
                
                // ✅ 修正：後端返回 stock.history，不是 stock.data
                const historyData = stock.history || [];
                
                if (historyData.length === 0) return;
                
                datasets.push({
                    label: `${stock.name} (${sym})`,
                    data: historyData.map(d => ({ x: d.date, y: d.value })),
                    borderColor: color,
                    backgroundColor: color + '20',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    tension: 0.1,
                    fill: false,
                });
                
                // ✅ 修正：從 history 計算起始價、結束價、漲跌幅
                const startValue = historyData[0]?.value || 100;
                const endValue = historyData[historyData.length - 1]?.value || 100;
                const changePct = endValue - startValue; // 因為已經正規化為 100 基準
                
                const changeClass = changePct >= 0 ? 'text-green-600' : 'text-red-600';
                const changeIcon = changePct >= 0 ? '▲' : '▼';
                
                tableHtml += `
                    <tr class="border-b hover:bg-gray-50">
                        <td class="py-2 px-3">
                            <span class="inline-block w-3 h-3 rounded-full mr-2" style="background-color: ${color}"></span>
                            <span class="font-medium">${stock.name}</span>
                            <span class="text-gray-400 text-xs ml-1">${sym}</span>
                        </td>
                        <td class="text-right py-2 px-3">${startValue.toFixed(2)}%</td>
                        <td class="text-right py-2 px-3">${endValue.toFixed(2)}%</td>
                        <td class="text-right py-2 px-3 ${changeClass} font-medium">
                            ${changeIcon} ${Math.abs(changePct).toFixed(2)}%
                        </td>
                    </tr>
                `;
            });
            
            if (datasets.length === 0) {
                throw new Error('無法處理資料');
            }
            
            // 繪製圖表
            const canvas = document.getElementById('compareChart');
            if (!canvas) {
                throw new Error('找不到圖表元素');
            }
            
            const ctx = canvas.getContext('2d');
            
            if (compareChart) {
                compareChart.destroy();
            }
            
            compareChart = new Chart(ctx, {
                type: 'line',
                data: { datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: { usePointStyle: true, boxWidth: 8 }
                        },
                        tooltip: {
                            callbacks: {
                                label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}%`
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: { 
                                unit: 'day', 
                                displayFormats: { day: 'MM/dd' } 
                            },
                            grid: { display: false },
                            ticks: { maxTicksLimit: 8 }
                        },
                        y: {
                            grid: { color: '#F3F4F6' },
                            ticks: { callback: v => v.toFixed(0) + '%' }
                        }
                    }
                }
            });
            
            // 更新 UI
            if (loading) loading.classList.add('hidden');
            if (container) container.classList.remove('hidden');
            
            const tableBody = document.getElementById('compareTableBody');
            if (tableBody) tableBody.innerHTML = tableHtml;
            if (resultTable) resultTable.classList.remove('hidden');
            
        } catch (e) {
            console.error('走勢比較失敗:', e);
            if (loading) loading.classList.add('hidden');
            if (placeholder) placeholder.classList.remove('hidden');
            showToast(e.message || '載入失敗');
        }
    }
    
    /**
     * 清空比較
     */
    function clearCompare() {
        const input = document.getElementById('compareSymbols');
        if (input) input.value = '';
        updateSelectedSymbols();
        
        const placeholder = document.getElementById('compareChartPlaceholder');
        const container = document.getElementById('compareChartContainer');
        const resultTable = document.getElementById('compareResultTable');
        
        if (placeholder) placeholder.classList.remove('hidden');
        if (container) container.classList.add('hidden');
        if (resultTable) resultTable.classList.add('hidden');
        
        if (compareChart) {
            compareChart.destroy();
            compareChart = null;
        }
    }
    
    // 初始化：監聽輸入變化
    document.addEventListener('DOMContentLoaded', () => {
        const input = document.getElementById('compareSymbols');
        if (input) {
            input.addEventListener('input', updateSelectedSymbols);
        }
    });
    
    // 導出到全域
    window.addCompareSymbol = addCompareSymbol;
    window.removeCompareSymbol = removeCompareSymbol;
    window.updateSelectedSymbols = updateSelectedSymbols;
    window.loadCompareChart = loadCompareChart;
    window.clearCompare = clearCompare;
    
    console.log('📈 compare.js 模組已載入');
})();
