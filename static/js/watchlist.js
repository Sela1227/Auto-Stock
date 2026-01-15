/**
 * 追蹤清單模組
 * 包含：清單顯示、新增刪除、匯出匯入、目標價設定
 */

(function() {
    'use strict';
    
    // ============================================================
    // 私有變數
    // ============================================================
    
    let watchlistData = [];
    let sortConfig = JSON.parse(localStorage.getItem('watchlistSort') || '{"field":"added_at","order":"desc"}');
    let currentTargetItemId = null;
    
    // ============================================================
    // 排序功能
    // ============================================================
    
    function getSortConfig() {
        return sortConfig;
    }
    
    function setSort(field, order) {
        sortConfig = { field, order };
        localStorage.setItem('watchlistSort', JSON.stringify(sortConfig));
    }
    
    function sortWatchlistData(data) {
        const { field, order } = sortConfig;
        const multiplier = order === 'asc' ? 1 : -1;
        
        return [...data].sort((a, b) => {
            let aVal, bVal;
            
            // 🆕 MA20 距離排序
            if (field === 'ma20_diff') {
                aVal = (a.ma20 && a.price) ? ((a.price - a.ma20) / a.ma20 * 100) : -999;
                bVal = (b.ma20 && b.price) ? ((b.price - b.ma20) / b.ma20 * 100) : -999;
            } else {
                aVal = a[field];
                bVal = b[field];
            }
            
            if (aVal === null || aVal === undefined) aVal = field === 'change_pct' ? -999 : '';
            if (bVal === null || bVal === undefined) bVal = field === 'change_pct' ? -999 : '';
            
            if (typeof aVal === 'string') {
                return aVal.localeCompare(bVal) * multiplier;
            }
            return (aVal - bVal) * multiplier;
        });
    }
    
    function changeWatchlistSort(field) {
        if (sortConfig.field === field) {
            setSort(field, sortConfig.order === 'asc' ? 'desc' : 'asc');
        } else {
            setSort(field, 'desc');
        }
        renderWatchlistCards(watchlistData);
    }
    
    function renderSortControls() {
        const options = [
            { field: 'added_at', label: '加入時間', icon: 'fa-clock' },
            { field: 'symbol', label: '代號', icon: 'fa-sort-alpha-down' },
            { field: 'change_pct', label: '漲跌幅', icon: 'fa-percent' },
            { field: 'price', label: '價格', icon: 'fa-dollar-sign' },
            { field: 'ma20_diff', label: 'MA20距離', icon: 'fa-chart-line' }
        ];
        
        return `
            <div class="flex items-center gap-2 mb-4 flex-wrap">
                <span class="text-sm text-gray-500"><i class="fas fa-sort mr-1"></i>排序:</span>
                <div class="flex gap-1 flex-wrap">
                    ${options.map(opt => `
                        <button onclick="changeWatchlistSort('${opt.field}')" 
                                class="px-3 py-1.5 text-xs rounded-full transition-all ${sortConfig.field === opt.field 
                                    ? 'bg-blue-500 text-white' 
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}">
                            <i class="fas ${opt.icon} mr-1"></i>${opt.label}
                            ${sortConfig.field === opt.field 
                                ? `<i class="fas fa-arrow-${sortConfig.order === 'asc' ? 'up' : 'down'} ml-1"></i>` 
                                : ''}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // ============================================================
    // 渲染卡片
    // ============================================================
    
    function getMa20Badge(item) {
        if (!item.ma20 || !item.price) return '';
        
        const diff = ((item.price - item.ma20) / item.ma20 * 100).toFixed(1);
        const isAbove = item.price >= item.ma20;
        
        return `<span class="ml-2 px-2 py-0.5 text-xs rounded-full ${isAbove ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
            MA20 ${isAbove ? '↑' : '↓'}${Math.abs(diff)}%
        </span>`;
    }
    
    function renderWatchlistCards(data) {
        const container = document.getElementById('watchlistContent');
        if (!container) return;
        
        watchlistData = data;
        const sortedData = sortWatchlistData(data);
        
        let html = renderSortControls();
        html += '<div class="space-y-3">';
        
        for (const item of sortedData) {
            const typeClass = item.asset_type === 'crypto' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700';
            const typeText = item.asset_type === 'crypto' ? '幣' : '股';
            
            const hasTarget = item.target_price !== null && item.target_price !== undefined;
            const targetReached = item.target_reached === true;
            const cardBorderClass = targetReached 
                ? 'border-yellow-500 ring-2 ring-yellow-300' 
                : (item.asset_type === 'crypto' ? 'border-purple-500' : 'border-blue-500');
            
            let priceInfo = '';
            if (item.price !== null && item.price !== undefined) {
                const change = item.change_pct || 0;
                const changeClass = change >= 0 ? 'text-green-600' : 'text-red-600';
                const changeIcon = change >= 0 ? '▲' : '▼';
                const ma20Badge = getMa20Badge(item);
                
                let targetBadge = '';
                if (hasTarget) {
                    if (targetReached) {
                        targetBadge = `<span class="ml-2 px-2 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-700 animate-pulse">
                            <i class="fas fa-bell mr-1"></i>已達標 $${item.target_price.toLocaleString()}
                        </span>`;
                    } else {
                        const diff = ((item.target_price - item.price) / item.price * 100).toFixed(1);
                        targetBadge = `<span class="ml-2 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                            <i class="fas fa-crosshairs mr-1"></i>目標 $${item.target_price.toLocaleString()} (${diff > 0 ? '+' : ''}${diff}%)
                        </span>`;
                    }
                }
                
                priceInfo = `
                    <div class="flex items-baseline gap-2 mt-2 flex-wrap">
                        <span class="text-xl font-bold text-gray-800">$${item.price.toLocaleString()}</span>
                        <span class="${changeClass} text-sm font-medium">${changeIcon} ${Math.abs(change).toFixed(2)}%</span>
                        ${ma20Badge}
                        ${targetBadge}
                    </div>
                `;
            } else {
                priceInfo = `<div class="flex items-baseline gap-2 mt-2"><span class="text-gray-400 text-sm">價格更新中...</span></div>`;
            }
            
            const nameDisplay = item.name ? `<span class="text-gray-500 text-sm ml-2">${item.name}</span>` : '';
            const isCrypto = item.asset_type === 'crypto';
            const isTw = item.symbol.includes('.TW') || /^\d+$/.test(item.symbol);
            const market = isTw ? 'tw' : 'us';
            
            const tradeButtons = isCrypto ? '' : `
                <div class="flex gap-2 mr-2">
                    <button onclick="quickTrade('${item.symbol}', '${item.name || ''}', '${market}', 'buy')" 
                            class="px-3 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 touch-target">
                        <i class="fas fa-arrow-down mr-1"></i>買入
                    </button>
                    <button onclick="quickTrade('${item.symbol}', '${item.name || ''}', '${market}', 'sell')" 
                            class="px-3 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 touch-target">
                        <i class="fas fa-arrow-up mr-1"></i>賣出
                    </button>
                </div>
            `;
            
            const targetPriceBtn = `
                <button onclick="showTargetPriceModal(${item.id}, '${item.symbol}', ${item.target_price || 'null'})" 
                        class="px-3 py-2 ${hasTarget ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'} rounded-lg text-sm hover:bg-yellow-200 touch-target mr-2"
                        title="${hasTarget ? '修改目標價' : '設定目標價'}">
                    <i class="fas fa-crosshairs"></i>
                </button>
            `;
            
            html += `
                <div class="stock-card bg-white rounded-xl shadow-sm p-4 border-l-4 ${cardBorderClass}">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <div class="flex items-center flex-wrap">
                                <span class="font-bold text-lg text-gray-800">${item.symbol}</span>
                                <span class="ml-2 px-2 py-0.5 rounded text-xs ${typeClass}">${typeText}</span>
                                ${targetReached ? '<span class="ml-2 px-2 py-0.5 rounded text-xs bg-yellow-500 text-white"><i class="fas fa-bell"></i> 到價</span>' : ''}
                                ${nameDisplay}
                            </div>
                            ${priceInfo}
                            ${item.note ? `<p class="text-gray-500 text-sm mt-2 italic"><i class="fas fa-sticky-note mr-1"></i>${item.note}</p>` : ''}
                        </div>
                        <button onclick="removeFromWatchlist('${item.symbol}')" class="p-2 text-gray-400 hover:text-red-500 touch-target">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                    <div class="flex items-center justify-between mt-3 pt-3 border-t flex-wrap gap-2">
                        <span class="text-gray-400 text-xs"><i class="fas fa-clock mr-1"></i>加入於 ${new Date(item.added_at).toLocaleDateString()}</span>
                        <div class="flex items-center">
                            ${targetPriceBtn}
                            ${tradeButtons}
                            <button onclick="searchSymbol('${item.symbol}')" class="px-4 py-2 bg-orange-500 text-white rounded-lg text-sm hover:bg-orange-600 touch-target">
                                <i class="fas fa-chart-line mr-1"></i>詳細分析
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    // ============================================================
    // API 操作
    // ============================================================
    
    async function loadWatchlist() {
        const container = document.getElementById('watchlistContent');
        const currentUser = typeof getCurrentUser === 'function' ? getCurrentUser() : window.currentUser;
        
        if (!currentUser || !currentUser.id) {
            console.error('loadWatchlist: 用戶未登入');
            if (container) {
                container.innerHTML = '<p class="text-red-500 text-center py-4">請先登入</p>';
            }
            return;
        }
        
        if (container) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-spinner fa-spin text-2xl text-blue-600"></i>
                    <p class="mt-2 text-gray-500">載入中...</p>
                </div>
            `;
        }
        
        try {
            const res = await apiRequest('/api/watchlist/with-prices');
            const data = await res.json();
            
            if (!data.success || !data.data || data.data.length === 0) {
                if (container) {
                    container.innerHTML = `
                        <div class="text-center py-12">
                            <i class="fas fa-star text-4xl text-gray-300 mb-3"></i>
                            <p class="text-gray-500">尚無追蹤清單</p>
                            <button onclick="showAddWatchlistModal()" class="mt-4 px-4 py-2 bg-orange-500 text-white rounded-lg">
                                <i class="fas fa-plus mr-2"></i>新增追蹤
                            </button>
                        </div>
                    `;
                }
                return;
            }
            
            renderWatchlistCards(data.data);
            
        } catch (e) {
            console.error('載入追蹤清單失敗:', e);
            if (container) {
                container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗，請稍後再試</p>';
            }
        }
    }
    
    async function addToWatchlist() {
        const symbol = document.getElementById('addSymbol')?.value?.trim().toUpperCase();
        const assetType = document.getElementById('addAssetType')?.value || 'stock';
        const note = document.getElementById('addNote')?.value?.trim() || null;
        
        if (!symbol) {
            showToast('請輸入代號');
            return;
        }
        
        try {
            const res = await apiRequest('/api/watchlist', {
                method: 'POST',
                body: { symbol, asset_type: assetType, note }
            });
            
            const data = await res.json();
            
            if (data.success) {
                showToast('已新增至追蹤清單');
                hideAddWatchlistModal();
                loadWatchlist();
                if (typeof loadWatchlistOverview === 'function') {
                    loadWatchlistOverview();
                }
            } else {
                showToast(data.detail || '新增失敗');
            }
        } catch (e) {
            console.error('新增追蹤失敗:', e);
            showToast('新增失敗');
        }
    }
    
    async function removeFromWatchlist(symbol) {
        if (!confirm(`確定要移除 ${symbol} 嗎？`)) return;
        
        try {
            const res = await apiRequest(`/api/watchlist/${encodeURIComponent(symbol)}`, {
                method: 'DELETE'
            });
            
            const data = await res.json();
            
            if (data.success) {
                showToast('已移除');
                loadWatchlist();
                if (typeof loadWatchlistOverview === 'function') {
                    loadWatchlistOverview();
                }
            } else {
                showToast(data.detail || '移除失敗');
            }
        } catch (e) {
            console.error('移除追蹤失敗:', e);
            showToast('移除失敗');
        }
    }
    
    // ============================================================
    // Modal 控制
    // ============================================================
    
    function showAddWatchlistModal() {
        const modal = document.getElementById('addWatchlistModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    function hideAddWatchlistModal() {
        const modal = document.getElementById('addWatchlistModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        const symbolInput = document.getElementById('addSymbol');
        const noteInput = document.getElementById('addNote');
        if (symbolInput) symbolInput.value = '';
        if (noteInput) noteInput.value = '';
    }
    
    function toggleWatchlistMenu() {
        const menu = document.getElementById('watchlistMenu');
        if (menu) menu.classList.toggle('hidden');
    }
    
    function showImportWatchlistModal() {
        toggleWatchlistMenu();
        const modal = document.getElementById('importWatchlistModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }
    
    function hideImportWatchlistModal() {
        const modal = document.getElementById('importWatchlistModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        const fileInput = document.getElementById('importWatchlistFile');
        if (fileInput) fileInput.value = '';
        const preview = document.getElementById('importWatchlistPreview');
        if (preview) preview.innerHTML = '';
    }
    
    // ============================================================
    // 匯出匯入
    // ============================================================
    
    async function exportWatchlist(format) {
        toggleWatchlistMenu();
        
        try {
            const res = await apiRequest(`/api/watchlist/export?format=${format}`);
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || '匯出失敗');
            }
            
            const blob = await res.blob();
            const filename = res.headers.get('Content-Disposition')?.split('filename=')[1] || `watchlist.${format}`;
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            
            showToast('匯出成功！');
        } catch (e) {
            console.error('匯出失敗:', e);
            showToast(e.message || '匯出失敗');
        }
    }
    
    function previewWatchlistFile(input) {
        const file = input.files[0];
        if (!file) return;
        
        const preview = document.getElementById('importWatchlistPreview');
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                let items = [];
                const content = e.target.result;
                
                if (file.name.endsWith('.json')) {
                    const data = JSON.parse(content);
                    items = data.items || data;
                } else if (file.name.endsWith('.csv')) {
                    const lines = content.split('\n').filter(l => l.trim());
                    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
                    
                    for (let i = 1; i < lines.length; i++) {
                        const values = lines[i].split(',');
                        const obj = {};
                        headers.forEach((h, idx) => obj[h] = values[idx]?.trim());
                        if (obj.symbol) items.push(obj);
                    }
                }
                
                preview.innerHTML = `
                    <div class="p-3 bg-green-50 rounded-lg">
                        <p class="text-green-700 font-medium"><i class="fas fa-check-circle mr-2"></i>找到 ${items.length} 筆資料</p>
                        <p class="text-sm text-gray-600 mt-1">代號: ${items.slice(0, 5).map(i => i.symbol).join(', ')}${items.length > 5 ? '...' : ''}</p>
                    </div>
                `;
                preview.dataset.items = JSON.stringify(items);
            } catch (err) {
                preview.innerHTML = `<p class="text-red-500"><i class="fas fa-times-circle mr-2"></i>檔案解析失敗: ${err.message}</p>`;
            }
        };
        
        reader.readAsText(file);
    }
    
    async function importWatchlist() {
        const preview = document.getElementById('importWatchlistPreview');
        const itemsStr = preview?.dataset?.items;
        
        if (!itemsStr) {
            showToast('請先選擇檔案');
            return;
        }
        
        try {
            const items = JSON.parse(itemsStr);
            
            const res = await apiRequest('/api/watchlist/import', {
                method: 'POST',
                body: { items }
            });
            
            const data = await res.json();
            
            if (data.success) {
                showToast(data.message);
                hideImportWatchlistModal();
                loadWatchlist();
                if (typeof loadWatchlistOverview === 'function') {
                    loadWatchlistOverview();
                }
            } else {
                showToast(data.detail || '匯入失敗');
            }
        } catch (e) {
            console.error('匯入失敗:', e);
            showToast('匯入失敗');
        }
    }
    
    // ============================================================
    // 目標價設定
    // ============================================================
    
    function showTargetPriceModal(itemId, symbol, currentTarget) {
        currentTargetItemId = itemId;
        const symbolEl = document.getElementById('targetPriceSymbol');
        const inputEl = document.getElementById('targetPriceInput');
        const modal = document.getElementById('targetPriceModal');
        
        if (symbolEl) symbolEl.textContent = symbol;
        if (inputEl) inputEl.value = currentTarget || '';
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
        if (inputEl) inputEl.focus();
    }
    
    function hideTargetPriceModal() {
        const modal = document.getElementById('targetPriceModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        currentTargetItemId = null;
    }
    
    async function saveTargetPrice() {
        if (!currentTargetItemId) return;
        
        const input = document.getElementById('targetPriceInput');
        const targetPrice = input?.value ? parseFloat(input.value) : null;
        
        try {
            const res = await apiRequest(`/api/watchlist/${currentTargetItemId}/target-price`, {
                method: 'PUT',
                body: { target_price: targetPrice }
            });
            
            const data = await res.json();
            
            if (data.success) {
                showToast(data.message);
                hideTargetPriceModal();
                loadWatchlist();
            } else {
                showToast(data.detail || '設定失敗');
            }
        } catch (e) {
            console.error('設定目標價失敗:', e);
            showToast('設定失敗');
        }
    }
    
    async function clearTargetPrice() {
        if (!currentTargetItemId) return;
        const input = document.getElementById('targetPriceInput');
        if (input) input.value = '';
        await saveTargetPrice();
    }
    
    // ============================================================
    // 🆕 快速新增到追蹤清單（從其他頁面呼叫）
    // ============================================================
    
    async function quickAddToWatchlist(symbol, assetType = 'stock') {
        const currentUser = typeof getCurrentUser === 'function' ? getCurrentUser() : window.currentUser;
        
        if (!currentUser || !currentUser.id) {
            showToast('請先登入');
            return;
        }
        
        try {
            const res = await apiRequest('/api/watchlist', {
                method: 'POST',
                body: { symbol, asset_type: assetType, note: '' }
            });
            
            const data = await res.json();
            
            if (data.success) {
                showToast(`${symbol} 已加入追蹤清單`);
                // 重新載入追蹤清單（如果在該頁面）
                if (typeof loadWatchlist === 'function') {
                    loadWatchlist();
                }
                if (typeof loadWatchlistOverview === 'function') {
                    loadWatchlistOverview();
                }
            } else {
                showToast(data.detail || '新增失敗');
            }
        } catch (e) {
            console.error('快速新增追蹤失敗:', e);
            showToast('新增失敗');
        }
    }
    
    // ============================================================
    // 儀表板快覽
    // ============================================================
    
    async function loadWatchlistOverview() {
        const container = document.getElementById('dashboardWatchlist');
        if (!container) return;
        
        const currentUser = typeof getCurrentUser === 'function' ? getCurrentUser() : window.currentUser;
        
        if (!currentUser || !currentUser.id) {
            console.error('loadWatchlistOverview: 用戶未登入');
            container.innerHTML = '<p class="text-red-500 text-center py-4">請先登入</p>';
            return;
        }
        
        try {
            const res = await apiRequest('/api/watchlist/with-prices');
            const data = await res.json();
            
            if (!data.success) {
                container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
                return;
            }
            
            if (!data.data || data.data.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-6">
                        <i class="fas fa-star text-gray-300 text-3xl mb-2"></i>
                        <p class="text-gray-500 text-sm">尚無追蹤清單</p>
                        <button onclick="showSection('search')" class="mt-2 text-blue-600 text-sm">前往查詢股票</button>
                    </div>
                `;
                return;
            }
            
            const items = data.data.slice(0, 5);
            let html = '<div class="space-y-2">';
            
            for (const item of items) {
                const change = item.change_pct || 0;
                const changeClass = change >= 0 ? 'text-green-600' : 'text-red-600';
                
                const priceText = item.price !== null && item.price !== undefined
                    ? `$${item.price.toLocaleString()}`
                    : '--';
                
                const changeText = item.price !== null && item.price !== undefined
                    ? `<span class="${changeClass} text-sm ml-1">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</span>`
                    : '';
                
                const isCrypto = item.asset_type === 'crypto';
                const isTw = item.symbol.includes('.TW') || /^\d+$/.test(item.symbol);
                const market = isTw ? 'tw' : 'us';
                
                const tradeButtons = isCrypto ? '' : `
                    <div class="flex gap-1 ml-2">
                        <button onclick="event.stopPropagation(); quickTrade('${item.symbol}', '${item.name || ''}', '${market}', 'buy')" 
                                class="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200" title="買入">買</button>
                        <button onclick="event.stopPropagation(); quickTrade('${item.symbol}', '${item.name || ''}', '${market}', 'sell')" 
                                class="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200" title="賣出">賣</button>
                    </div>
                `;
                
                html += `
                    <div class="flex items-center justify-between py-2 border-b last:border-0 cursor-pointer hover:bg-gray-50 -mx-2 px-2 rounded"
                         onclick="searchSymbol('${item.symbol}')">
                        <div class="flex items-center">
                            <span class="font-medium text-gray-800 w-20">${item.symbol}</span>
                            <span class="text-xs px-2 py-0.5 rounded ${item.asset_type === 'crypto' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}">
                                ${item.asset_type === 'crypto' ? '幣' : '股'}
                            </span>
                        </div>
                        <div class="flex items-center">
                            <div class="text-right">
                                <span class="text-gray-700 font-medium">${priceText}</span>
                                ${changeText}
                            </div>
                            ${tradeButtons}
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            
            if (data.data.length > 5) {
                html += `
                    <div class="text-center mt-3">
                        <button onclick="showSection('watchlist')" class="text-blue-600 text-sm hover:underline">
                            查看全部 (${data.data.length})
                        </button>
                    </div>
                `;
            }
            
            container.innerHTML = html;
            
        } catch (e) {
            console.error('載入追蹤清單失敗', e);
            container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
        }
    }
    
    // ============================================================
    // 導出到全域
    // ============================================================
    
    window.loadWatchlist = loadWatchlist;
    window.loadWatchlistOverview = loadWatchlistOverview;
    window.addToWatchlist = addToWatchlist;
    window.removeFromWatchlist = removeFromWatchlist;
    window.changeWatchlistSort = changeWatchlistSort;
    window.showAddWatchlistModal = showAddWatchlistModal;
    window.hideAddWatchlistModal = hideAddWatchlistModal;
    window.toggleWatchlistMenu = toggleWatchlistMenu;
    window.showImportWatchlistModal = showImportWatchlistModal;
    window.hideImportWatchlistModal = hideImportWatchlistModal;
    window.exportWatchlist = exportWatchlist;
    window.previewWatchlistFile = previewWatchlistFile;
    window.importWatchlist = importWatchlist;
    window.showTargetPriceModal = showTargetPriceModal;
    window.hideTargetPriceModal = hideTargetPriceModal;
    window.saveTargetPrice = saveTargetPrice;
    window.clearTargetPrice = clearTargetPrice;
    window.quickAddToWatchlist = quickAddToWatchlist;
    
    console.log('⭐ watchlist.js 模組已載入');
})();
