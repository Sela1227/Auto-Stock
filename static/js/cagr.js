// ============================================================
// 報酬率比較 (CAGR) - cagr.js
// ============================================================

// 選中的標的
let cagrSelectedSymbols = [];

// 預設組合
const CAGR_PRESETS = {
    'mag7': {
        name: '科技七雄 (MAG7)',
        symbols: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
    },
    'indices': {
        name: '美股三大指數',
        symbols: ['^GSPC', '^DJI', '^IXIC']
    },
    'tw_etf': {
        name: '台股熱門 ETF',
        symbols: ['0050.TW', '0056.TW', '00878.TW', '00919.TW']
    },
    'crypto': {
        name: '加密貨幣',
        symbols: ['BTC-USD', 'ETH-USD', 'SOL-USD']
    }
};

// ==================== 初始化 ====================
function initCagr() {
    cagrLoadPresets();
    cagrLoadSavedComparisons();
}

// ==================== 預設組合 ====================
function cagrLoadPresets() {
    const container = document.getElementById('cagrPresetList');
    if (!container) return;
    
    container.innerHTML = Object.entries(CAGR_PRESETS).map(([id, preset]) => `
        <button onclick="cagrLoadPreset('${id}')" 
            class="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 transition flex justify-between items-center text-sm">
            <span>${preset.name}</span>
            <span class="text-xs text-gray-400">${preset.symbols.length}個</span>
        </button>
    `).join('');
}

function cagrLoadPreset(presetId) {
    const preset = CAGR_PRESETS[presetId];
    if (!preset) {
        showToast('找不到預設組合', 'error');
        return;
    }
    
    // 限制最多 5 個
    cagrSelectedSymbols = preset.symbols.slice(0, 5);
    cagrRenderSelectedSymbols();
    cagrRunComparison();
}

async function cagrQuickCompare(presetId) {
    cagrShowLoading();
    try {
        const benchmark = document.getElementById('cagrBenchmarkSelect').value;
        const sortBy = document.getElementById('cagrSortBySelect').value;
        
        const res = await fetch(`/api/compare/quick/${presetId}?benchmark=${benchmark}&sort_by=${sortBy}`);
        const data = await res.json();
        
        if (data.success) {
            // 更新選中的標的
            if (data.preset && data.preset.symbols) {
                cagrSelectedSymbols = data.preset.symbols;
                cagrRenderSelectedSymbols();
            }
            cagrRenderResult(data);
        } else {
            showToast('比較失敗：' + (data.error || '未知錯誤'), 'error');
        }
    } catch (e) {
        showToast('比較失敗：' + e.message, 'error');
    }
}

// ==================== 標的選擇 ====================
function cagrAddSymbol() {
    const input = document.getElementById('cagrSymbolInput');
    const symbol = input.value.trim().toUpperCase();
    
    if (!symbol) return;
    
    if (cagrSelectedSymbols.length >= 5) {
        showToast('最多只能選擇 5 個標的', 'warning');
        return;
    }
    
    if (cagrSelectedSymbols.includes(symbol)) {
        showToast('已經選擇過此標的', 'warning');
        return;
    }
    
    cagrSelectedSymbols.push(symbol);
    cagrRenderSelectedSymbols();
    input.value = '';
}

function cagrRemoveSymbol(symbol) {
    cagrSelectedSymbols = cagrSelectedSymbols.filter(s => s !== symbol);
    cagrRenderSelectedSymbols();
}

function cagrRenderSelectedSymbols() {
    const container = document.getElementById('cagrSelectedSymbols');
    
    if (cagrSelectedSymbols.length === 0) {
        container.innerHTML = '<span class="text-gray-400 text-sm">尚未選擇</span>';
        return;
    }
    
    container.innerHTML = cagrSelectedSymbols.map(symbol => `
        <span class="inline-flex items-center px-3 py-1 bg-gray-200 rounded-full text-sm m-1">
            ${symbol}
            <button onclick="cagrRemoveSymbol('${symbol}')" class="ml-2 text-gray-400 hover:text-red-500" title="移除">
                <i class="fas fa-times"></i>
            </button>
        </span>
    `).join('');
}

// ==================== 執行比較 ====================
async function cagrRunComparison() {
    if (cagrSelectedSymbols.length === 0) {
        showToast('請至少選擇一個標的', 'warning');
        return;
    }
    
    cagrShowLoading();
    
    // 取得勾選的週期
    const periods = Array.from(document.querySelectorAll('.cagr-period-check:checked'))
        .map(cb => cb.value);
    
    if (periods.length === 0) {
        showToast('請至少選擇一個時間週期', 'warning');
        return;
    }
    
    const benchmark = document.getElementById('cagrBenchmarkSelect').value;
    const sortBy = document.getElementById('cagrSortBySelect').value;
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch('/api/compare/cagr', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { 'Authorization': `Bearer ${token}` } : {})
            },
            body: JSON.stringify({
                symbols: cagrSelectedSymbols,
                periods: periods,
                benchmark: benchmark,
                sort_by: sortBy,
                sort_order: 'desc'
            })
        });
        
        const data = await res.json();
        
        if (data.success) {
            cagrRenderResult(data);
        } else {
            showToast('比較失敗：' + (data.detail || data.error || '未知錯誤'), 'error');
            document.getElementById('cagrComparisonResult').innerHTML = `
                <div class="text-center py-8 text-red-500">
                    <i class="fas fa-exclamation-circle text-4xl mb-2"></i>
                    <p>${data.detail || data.error || '比較失敗'}</p>
                </div>
            `;
        }
    } catch (e) {
        showToast('比較失敗：' + e.message, 'error');
    }
}

function cagrShowLoading() {
    document.getElementById('cagrComparisonResult').innerHTML = `
        <div class="text-center py-12">
            <i class="fas fa-spinner fa-spin text-4xl text-blue-500 mb-4"></i>
            <p class="text-gray-500">正在計算報酬率...</p>
            <p class="text-gray-400 text-sm mt-1">首次查詢可能需要較長時間</p>
        </div>
    `;
}

// ==================== 渲染結果 ====================
function cagrRenderResult(data) {
    const container = document.getElementById('cagrComparisonResult');
    const periods = data.periods || ['1y', '3y', '5y'];
    
    // 更新時間
    if (data.generated_at) {
        const time = new Date(data.generated_at).toLocaleString('zh-TW');
        document.getElementById('cagrResultTime').textContent = `更新：${time}`;
    }
    
    // 建立表格
    let html = `
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead>
                    <tr class="bg-gray-50">
                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">排名</th>
                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">標的</th>
                        <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">現價</th>
                        ${periods.map(p => `
                            <th class="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">${cagrFormatPeriod(p)}</th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
    `;
    
    data.comparison.forEach((item, index) => {
        const rankClass = index === 0 ? 'bg-yellow-100' : index === 1 ? 'bg-gray-100' : index === 2 ? 'bg-orange-100' : '';
        const rankIcon = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}`;
        const typeIcon = item.type === 'crypto' ? '🪙' : item.type === 'index' ? '📈' : '📊';
        
        html += `
            <tr class="hover:bg-gray-50">
                <td class="px-3 py-3">
                    <span class="inline-flex items-center justify-center w-8 h-8 rounded-full ${rankClass} font-bold text-sm">
                        ${rankIcon}
                    </span>
                </td>
                <td class="px-3 py-3">
                    <div class="flex items-center">
                        <span class="mr-2">${typeIcon}</span>
                        <div>
                            <div class="font-medium text-gray-900">${item.symbol}</div>
                            <div class="text-xs text-gray-500">${item.name || ''}</div>
                        </div>
                    </div>
                </td>
                <td class="px-3 py-3 text-right">
                    ${item.current_price ? `$${cagrFormatNumber(item.current_price)}` : '--'}
                </td>
                ${periods.map(p => {
                    const cagr = item.cagr ? item.cagr[p] : null;
                    const vsBench = item.vs_benchmark ? item.vs_benchmark[p] : null;
                    return `
                        <td class="px-3 py-3 text-right">
                            ${cagrFormatCAGR(cagr)}
                            ${vsBench !== null && vsBench !== undefined ? `
                                <div class="text-xs ${vsBench >= 0 ? 'text-green-600' : 'text-red-600'}">
                                    ${vsBench >= 0 ? '+' : ''}${vsBench.toFixed(1)}%
                                </div>
                            ` : ''}
                        </td>
                    `;
                }).join('')}
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    
    // 基準指數資訊
    if (data.benchmark) {
        html += `
            <div class="mt-4 p-3 bg-gray-50 rounded-lg text-sm">
                <span class="text-gray-500">📌 基準指數：</span>
                <span class="font-medium">${data.benchmark.name} (${data.benchmark.symbol})</span>
                <span class="ml-4 text-gray-500">
                    ${periods.map(p => `${cagrFormatPeriod(p)}: ${cagrFormatCAGR(data.benchmark.cagr[p], true)}`).join(' | ')}
                </span>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function cagrFormatPeriod(period) {
    const map = { '1y': '1年', '3y': '3年', '5y': '5年', '10y': '10年', 'custom': '自訂' };
    return map[period] || period;
}

function cagrFormatCAGR(value, simple = false) {
    if (value === null || value === undefined) {
        return '<span class="text-gray-400">--</span>';
    }
    
    const colorClass = value > 0 ? 'text-green-600' : value < 0 ? 'text-red-600' : 'text-gray-600';
    const sign = value > 0 ? '+' : '';
    
    if (simple) {
        return `<span class="${colorClass}">${sign}${value.toFixed(1)}%</span>`;
    }
    
    return `<span class="${colorClass} font-medium">${sign}${value.toFixed(1)}%</span>`;
}

function cagrFormatNumber(num) {
    if (num >= 1000) {
        return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return num.toFixed(2);
}

// ==================== 儲存組合 ====================
async function cagrSaveCurrentComparison() {
    const token = localStorage.getItem('token');
    if (!token) {
        showToast('請先登入', 'warning');
        return;
    }
    
    if (cagrSelectedSymbols.length === 0) {
        showToast('請先選擇標的', 'warning');
        return;
    }
    
    const name = prompt('請輸入組合名稱：');
    if (!name) return;
    
    try {
        const res = await fetch('/api/compare/saved', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                name: name,
                symbols: cagrSelectedSymbols,
                benchmark: document.getElementById('cagrBenchmarkSelect').value
            })
        });
        
        const data = await res.json();
        
        if (data.success) {
            showToast('組合已儲存', 'success');
            cagrLoadSavedComparisons();
        } else {
            showToast('儲存失敗：' + (data.detail || '未知錯誤'), 'error');
        }
    } catch (e) {
        showToast('儲存失敗：' + e.message, 'error');
    }
}

async function cagrLoadSavedComparisons() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const res = await fetch('/api/compare/saved', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        
        if (data.success && data.comparisons && data.comparisons.length > 0) {
            const container = document.getElementById('cagrSavedComparisons');
            container.innerHTML = data.comparisons.map(c => `
                <div class="flex justify-between items-center p-2 rounded hover:bg-gray-50">
                    <button onclick="cagrLoadSavedComparison(${c.id}, ${JSON.stringify(c.symbols).replace(/"/g, '&quot;')})" 
                        class="text-left flex-1">
                        <div class="font-medium text-sm">${c.name}</div>
                        <div class="text-xs text-gray-400">${c.symbols.join(', ')}</div>
                    </button>
                    <button onclick="cagrDeleteSavedComparison(${c.id})" class="text-red-400 hover:text-red-600 ml-2">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('載入儲存組合失敗', e);
    }
}

function cagrLoadSavedComparison(id, symbols) {
    cagrSelectedSymbols = symbols;
    cagrRenderSelectedSymbols();
    cagrRunComparison();
}

async function cagrDeleteSavedComparison(id) {
    if (!confirm('確定要刪除此組合？')) return;
    
    const token = localStorage.getItem('token');
    try {
        const res = await fetch(`/api/compare/saved/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await res.json();
        
        if (data.success) {
            showToast('已刪除', 'success');
            cagrLoadSavedComparisons();
        }
    } catch (e) {
        showToast('刪除失敗', 'error');
    }
}

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延遲初始化，讓其他模組先載入
    setTimeout(initCagr, 100);
});
