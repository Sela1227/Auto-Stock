/**
 * 追蹤清單功能模組（含到價提醒）
 * 
 * 使用方式：
 * 1. 在 dashboard.html 的 <script> 區塊中加入這些函數
 * 2. 或作為獨立 JS 檔案引入
 */

// ============================================================
// 追蹤清單（含價格和到價提醒）
// ============================================================

async function loadWatchlist() {
    const container = document.getElementById('watchlistContent');

    try {
        // 使用 with-prices API 取得含價格的追蹤清單
        const res = await fetch(`${API_BASE}/api/watchlist/with-prices`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (!data.success || !data.data || data.data.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12">
                    <i class="fas fa-star text-gray-300 text-4xl mb-3"></i>
                    <p class="text-gray-500 mb-4">尚無追蹤的股票</p>
                    <button onclick="showAddWatchlistModal()" class="px-6 py-2 bg-blue-600 text-white rounded-lg">
                        <i class="fas fa-plus mr-2"></i>新增追蹤
                    </button>
                </div>
            `;
            return;
        }

        let html = '<div class="space-y-3">';

        for (const item of data.data) {
            const typeClass = item.asset_type === 'crypto' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700';
            const typeText = item.asset_type === 'crypto' ? '幣' : '股';

            // 價格變動顏色
            const changeClass = item.change_pct >= 0 ? 'text-green-600' : 'text-red-600';
            const changeIcon = item.change_pct >= 0 ? '▲' : '▼';

            // 🆕 到價提醒變色
            const targetReached = item.target_reached;
            const cardBorderClass = targetReached ? 'border-2 border-yellow-400 bg-yellow-50' : 'bg-white';
            const targetBadge = targetReached ? '<span class="ml-2 px-2 py-0.5 bg-yellow-400 text-yellow-900 text-xs rounded-full animate-pulse">🎯 達標!</span>' : '';

            html += `
                <div class="stock-card ${cardBorderClass} rounded-xl shadow-sm p-4">
                    <div class="flex items-start justify-between mb-2">
                        <div class="flex items-center flex-wrap">
                            <span class="font-bold text-lg text-gray-800">${item.symbol}</span>
                            <span class="ml-2 px-2 py-0.5 rounded text-xs ${typeClass}">${typeText}</span>
                            ${targetBadge}
                        </div>
                        <div class="flex items-center space-x-1">
                            <button onclick="showTargetPriceModal(${item.id}, '${item.symbol}', ${item.target_price || 'null'})" 
                                class="p-2 text-gray-400 hover:text-yellow-500 touch-target" title="設定目標價">
                                <i class="fas fa-crosshairs"></i>
                            </button>
                            <button onclick="removeFromWatchlist(${item.id})" 
                                class="p-2 text-gray-400 hover:text-red-500 touch-target" title="移除">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    
                    ${item.name ? `<p class="text-gray-500 text-sm mb-2">${item.name}</p>` : ''}
                    
                    <!-- 價格資訊 -->
                    <div class="flex items-center justify-between mt-3">
                        <div>
                            ${item.price ? `
                                <span class="text-xl font-bold text-gray-800">$${item.price.toLocaleString()}</span>
                                <span class="ml-2 ${changeClass} text-sm">
                                    ${changeIcon} ${Math.abs(item.change_pct || 0).toFixed(2)}%
                                </span>
                            ` : '<span class="text-gray-400">價格載入中...</span>'}
                        </div>
                        <button onclick="searchSymbol('${item.symbol}')" 
                            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 touch-target">
                            詳情
                        </button>
                    </div>
                    
                    <!-- 目標價顯示 -->
                    ${item.target_price ? `
                        <div class="mt-2 pt-2 border-t border-gray-100 flex items-center justify-between text-sm">
                            <span class="text-gray-500">
                                <i class="fas fa-crosshairs mr-1"></i>目標價
                            </span>
                            <span class="${targetReached ? 'text-yellow-600 font-bold' : 'text-gray-700'}">
                                $${item.target_price.toLocaleString()}
                            </span>
                        </div>
                    ` : ''}
                    
                    ${item.note ? `<p class="text-gray-400 text-xs mt-2">${item.note}</p>` : ''}
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;

    } catch (e) {
        console.error('載入追蹤清單失敗', e);
        container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
    }
}


// ============================================================
// 目標價 Modal
// ============================================================

let currentTargetItem = null;

function showTargetPriceModal(itemId, symbol, currentTarget) {
    currentTargetItem = { id: itemId, symbol: symbol };
    
    // 如果 Modal 不存在，動態建立
    let modal = document.getElementById('targetPriceModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'targetPriceModal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-xl w-full max-w-sm p-6">
                <h3 class="text-lg font-bold text-gray-800 mb-4">
                    <i class="fas fa-crosshairs mr-2 text-yellow-500"></i>
                    設定目標價
                </h3>
                <p id="targetSymbolDisplay" class="text-gray-600 mb-4"></p>
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2 text-sm">目標價格</label>
                    <input type="number" id="targetPriceInput" step="0.01" placeholder="輸入目標價格" 
                        class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-yellow-500 text-base">
                    <p class="text-gray-400 text-xs mt-1">當現價達到或超過此價格時會變色提醒</p>
                </div>
                <div class="flex gap-3">
                    <button onclick="hideTargetPriceModal()" 
                        class="flex-1 px-4 py-3 border rounded-lg hover:bg-gray-50 touch-target">取消</button>
                    <button onclick="clearTargetPrice()" 
                        class="px-4 py-3 border border-red-300 text-red-500 rounded-lg hover:bg-red-50 touch-target">清除</button>
                    <button onclick="saveTargetPrice()" 
                        class="flex-1 px-4 py-3 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 touch-target">儲存</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // 設定 Modal 內容
    document.getElementById('targetSymbolDisplay').textContent = `標的：${symbol}`;
    document.getElementById('targetPriceInput').value = currentTarget || '';
    
    // 顯示 Modal
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function hideTargetPriceModal() {
    const modal = document.getElementById('targetPriceModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    currentTargetItem = null;
}

async function saveTargetPrice() {
    if (!currentTargetItem) return;
    
    const input = document.getElementById('targetPriceInput');
    const targetPrice = input.value ? parseFloat(input.value) : null;
    
    if (targetPrice !== null && (isNaN(targetPrice) || targetPrice <= 0)) {
        showToast('請輸入有效的目標價格');
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/watchlist/${currentTargetItem.id}/target-price`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ target_price: targetPrice })
        });
        
        const data = await res.json();
        
        if (data.success) {
            showToast(targetPrice ? `目標價已設定為 $${targetPrice}` : '目標價已清除');
            hideTargetPriceModal();
            loadWatchlist();  // 重新載入列表
        } else {
            showToast(data.detail || '設定失敗');
        }
    } catch (e) {
        console.error('設定目標價失敗', e);
        showToast('設定失敗');
    }
}

async function clearTargetPrice() {
    if (!currentTargetItem) return;
    
    try {
        const res = await fetch(`${API_BASE}/api/watchlist/${currentTargetItem.id}/target-price`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ target_price: null })
        });
        
        const data = await res.json();
        
        if (data.success) {
            showToast('目標價已清除');
            hideTargetPriceModal();
            loadWatchlist();
        } else {
            showToast('清除失敗');
        }
    } catch (e) {
        showToast('清除失敗');
    }
}


// ============================================================
// 追蹤清單快覽（儀表板用，含到價提醒）
// ============================================================

async function loadWatchlistOverview() {
    const container = document.getElementById('dashboardWatchlist');

    try {
        const res = await fetch(`${API_BASE}/api/watchlist/with-prices`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (!data.success || !data.data || data.data.length === 0) {
            container.innerHTML = `
                <div class="text-center py-6">
                    <i class="fas fa-star text-gray-300 text-3xl mb-2"></i>
                    <p class="text-gray-500 text-sm">尚無追蹤清單</p>
                    <button onclick="showSection('search')" class="mt-2 text-blue-600 text-sm">前往查詢股票</button>
                </div>
            `;
            return;
        }

        // 只顯示前 5 筆，優先顯示達標的
        const sortedItems = [...data.data].sort((a, b) => {
            // 達標的排前面
            if (a.target_reached && !b.target_reached) return -1;
            if (!a.target_reached && b.target_reached) return 1;
            return 0;
        });
        
        const items = sortedItems.slice(0, 5);
        let html = '<div class="space-y-2">';

        for (const item of items) {
            const changeClass = item.change_pct >= 0 ? 'text-green-600' : 'text-red-600';
            const targetClass = item.target_reached ? 'bg-yellow-50 border-l-4 border-yellow-400' : '';
            
            html += `
                <div class="flex items-center justify-between py-2 px-2 -mx-2 rounded cursor-pointer hover:bg-gray-50 ${targetClass}" 
                     onclick="searchSymbol('${item.symbol}')">
                    <div class="flex items-center">
                        <span class="font-medium text-gray-800">${item.symbol}</span>
                        ${item.target_reached ? '<span class="ml-2 text-yellow-500 text-xs">🎯</span>' : ''}
                        <span class="ml-2 text-xs px-2 py-0.5 rounded ${item.asset_type === 'crypto' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}">
                            ${item.asset_type === 'crypto' ? '幣' : '股'}
                        </span>
                    </div>
                    <div class="text-right">
                        ${item.price ? `
                            <span class="text-gray-800 font-medium">$${item.price.toLocaleString()}</span>
                            <span class="${changeClass} text-xs ml-1">${item.change_pct >= 0 ? '+' : ''}${(item.change_pct || 0).toFixed(2)}%</span>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        html += '</div>';
        
        // 如果有達標的，顯示提示
        const reachedCount = data.data.filter(i => i.target_reached).length;
        if (reachedCount > 0) {
            html = `
                <div class="mb-3 p-2 bg-yellow-100 text-yellow-800 rounded-lg text-sm text-center">
                    🎯 有 ${reachedCount} 檔達到目標價！
                </div>
            ` + html;
        }
        
        container.innerHTML = html;

    } catch (e) {
        console.error('載入追蹤清單失敗', e);
        container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
    }
}
