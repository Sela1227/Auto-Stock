/**
 * 追蹤清單模組 (P3 優化版)
 * 
 * 優化內容：
 * 1. 事件委託 - 減少監聽器數量
 * 2. AppState 整合 - 統一狀態管理
 * 3. DOM 快取 - 使用 $() 函數
 * 
 * 包含：清單顯示、新增刪除、匯出匯入、目標價設定、標籤整合
 */

(function() {
    'use strict';

    // ============================================================
    // 私有變數
    // ============================================================

    let watchlistData = [];
    let sortConfig = JSON.parse(localStorage.getItem('watchlistSort') || '{"field":"added_at","order":"desc"}');
    let currentTargetItemId = null;
    let watchlistTagsMap = {};

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
                        <button data-action="sort" data-field="${opt.field}"
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
        const container = $('watchlistContent');
        if (!container) return;

        watchlistData = data;

        // 同步到 AppState
        if (window.AppState) {
            AppState.setWatchlist(data);
        }

        // 標籤篩選
        const filterTagId = typeof getFilterTagId === 'function' ? getFilterTagId() : null;
        let filteredData = data;

        if (filterTagId) {
            filteredData = data.filter(item => {
                const itemTags = watchlistTagsMap[item.id] || [];
                return itemTags.some(t => t.id === filterTagId);
            });
        }

        const sortedData = sortWatchlistData(filteredData);

        // 標籤篩選器
        let html = '';
        if (typeof renderTagFilter === 'function') {
            html += renderTagFilter(filterTagId);
        }

        html += renderSortControls();
        html += '<div class="space-y-3" id="watchlistCards">';

        for (const item of sortedData) {
            html += renderSingleCard(item);
        }

        html += '</div>';
        container.innerHTML = html;

        // ✅ P3: 初始化事件委託
        initWatchlistEventDelegation();
    }

    function renderSingleCard(item) {
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
                const isAbove = item.target_direction !== 'below';
                const dirIcon = isAbove ? 'fa-arrow-up' : 'fa-arrow-down';
                const dirText = isAbove ? '↑' : '↓';
                
                if (targetReached) {
                    // 已達標：黃色閃爍，更大更明顯
                    targetBadge = `<span class="ml-2 px-3 py-1 text-sm font-bold rounded-full bg-yellow-400 text-yellow-900 animate-pulse shadow">
                        <i class="fas fa-bell mr-1"></i>${dirText} 已達標 $${item.target_price.toLocaleString()}
                    </span>`;
                } else {
                    // 未達標：帶邊框，更明顯
                    const diff = ((item.target_price - item.price) / item.price * 100).toFixed(1);
                    const badgeStyle = isAbove 
                        ? 'bg-green-100 text-green-700 border border-green-400' 
                        : 'bg-red-100 text-red-700 border border-red-400';
                    targetBadge = `<span class="ml-2 px-3 py-1 text-sm font-medium rounded-full ${badgeStyle}">
                        <i class="fas ${dirIcon} mr-1"></i>目標 $${item.target_price.toLocaleString()} (${diff > 0 ? '+' : ''}${diff}%)
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

        // 標籤 badges
        const itemTags = watchlistTagsMap[item.id] || [];
        const tagBadges = typeof renderTagBadges === 'function' ? renderTagBadges(itemTags) : '';

        // ✅ P3: 使用 data-action 替代 onclick
        const tradeButtons = isCrypto ? '' : `
            <div class="flex gap-2 mr-2">
                <button data-action="trade" data-symbol="${item.symbol}" data-name="${item.name || ''}" data-market="${market}" data-type="buy"
                        class="px-3 py-2 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600 touch-target">
                    <i class="fas fa-arrow-down mr-1"></i>買入
                </button>
                <button data-action="trade" data-symbol="${item.symbol}" data-name="${item.name || ''}" data-market="${market}" data-type="sell"
                        class="px-3 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 touch-target">
                    <i class="fas fa-arrow-up mr-1"></i>賣出
                </button>
            </div>
        `;

        return `
            <div class="stock-card bg-white rounded-xl shadow-sm p-4 border-l-4 ${cardBorderClass}" data-id="${item.id}" data-symbol="${item.symbol}">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center flex-wrap gap-1">
                            <span class="font-bold text-lg text-gray-800">${item.symbol}</span>
                            <span class="px-2 py-0.5 rounded text-xs ${typeClass}">${typeText}</span>
                            ${targetReached ? '<span class="px-2 py-0.5 rounded text-xs bg-yellow-500 text-white"><i class="fas fa-bell"></i> 到價</span>' : ''}
                            ${nameDisplay}
                        </div>
                        ${tagBadges ? `<div class="flex flex-wrap gap-1 mt-1">${tagBadges}</div>` : ''}
                        ${priceInfo}
                        ${item.note ? `<p class="text-gray-500 text-sm mt-2 italic"><i class="fas fa-sticky-note mr-1"></i>${item.note}</p>` : ''}
                    </div>
                    <button data-action="remove" data-symbol="${item.symbol}" class="p-2 text-gray-400 hover:text-red-500 touch-target">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="flex items-center justify-between mt-3 pt-3 border-t flex-wrap gap-2">
                    <span class="text-gray-400 text-xs"><i class="fas fa-clock mr-1"></i>加入於 ${new Date(item.added_at).toLocaleDateString()}</span>
                    <div class="flex items-center">
                        <button data-action="assign-tag" data-id="${item.id}" data-symbol="${item.symbol}"
                                class="px-3 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm hover:bg-gray-200 touch-target mr-2"
                                title="設定標籤">
                            <i class="fas fa-tags"></i>
                        </button>
                        <button data-action="target-price" data-id="${item.id}" data-symbol="${item.symbol}" data-target="${item.target_price || ''}" data-direction="${item.target_direction || 'above'}"
                                class="px-3 py-2 ${hasTarget ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'} rounded-lg text-sm hover:bg-yellow-200 touch-target mr-2"
                                title="${hasTarget ? '修改目標價' : '設定目標價'}">
                            <i class="fas fa-crosshairs"></i>
                        </button>
                        ${tradeButtons}
                        <button data-action="analyze" data-symbol="${item.symbol}" class="px-4 py-2 bg-orange-500 text-white rounded-lg text-sm hover:bg-orange-600 touch-target">
                            <i class="fas fa-chart-line mr-1"></i>詳細分析
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // ============================================================
    // 事件委託 (P3 核心優化)
    // ============================================================

    let delegationInitialized = false;

    function initWatchlistEventDelegation() {
        const container = $('watchlistContent');
        if (!container || delegationInitialized) return;

        container.addEventListener('click', handleWatchlistClick);
        delegationInitialized = true;
    }

    function handleWatchlistClick(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        e.preventDefault();
        const action = target.dataset.action;

        switch (action) {
            case 'sort':
                changeWatchlistSort(target.dataset.field);
                break;

            case 'remove':
                removeFromWatchlist(target.dataset.symbol);
                break;

            case 'analyze':
                if (typeof searchSymbol === 'function') {
                    searchSymbol(target.dataset.symbol);
                }
                break;

            case 'trade':
                if (typeof quickTrade === 'function') {
                    quickTrade(
                        target.dataset.symbol,
                        target.dataset.name,
                        target.dataset.market,
                        target.dataset.type
                    );
                }
                break;

            case 'target-price':
                showTargetPriceModal(
                    parseInt(target.dataset.id),
                    target.dataset.symbol,
                    target.dataset.target ? parseFloat(target.dataset.target) : null,
                    target.dataset.direction || 'above'  // 🔧 修正：加入 direction 參數
                );
                break;

            case 'assign-tag':
                if (typeof showAssignTagModal === 'function') {
                    showAssignTagModal(parseInt(target.dataset.id), target.dataset.symbol);
                }
                break;

            case 'filter-tag':
                if (typeof setFilterTagId === 'function') {
                    const tagId = target.dataset.tagId ? parseInt(target.dataset.tagId) : null;
                    setFilterTagId(tagId);
                    renderWatchlistCards(watchlistData);
                }
                break;
        }
    }

    // ============================================================
    // API 操作
    // ============================================================

    async function loadWatchlist() {
        const container = $('watchlistContent');
        const currentUser = typeof getCurrentUser === 'function' ? getCurrentUser() : window.currentUser;

        if (!currentUser || !currentUser.id) {
            console.error('loadWatchlist: 用戶未登入');
            if (container) {
                container.innerHTML = '<p class="text-red-500 text-center py-4">請先登入</p>';
            }
            return;
        }

        // ✅ 檢查 AppState 是否已有完整資料（含價格）
        if (window.AppState && AppState.watchlistLoaded && AppState.watchlist.length > 0) {
            const hasPrice = AppState.watchlist.some(item => item.price !== null);
            if (hasPrice) {
                renderWatchlistCards(AppState.watchlist);
                return;
            }
        }

        // 🆕 階段 1：先載入基本資料（毫秒級）
        try {
            if (typeof loadTags === 'function') {
                await loadTags();
            }

            const basicRes = await apiRequest('/api/watchlist/basic');
            const basicData = await basicRes.json();

            if (!basicData.success || !basicData.data || basicData.data.length === 0) {
                if (container) {
                    container.innerHTML = `
                        <div class="text-center py-12">
                            <i class="fas fa-star text-4xl text-gray-300 mb-3"></i>
                            <p class="text-gray-500">尚無追蹤清單</p>
                            <button data-action="show-add-modal" class="mt-4 px-4 py-2 bg-orange-500 text-white rounded-lg">
                                <i class="fas fa-plus mr-2"></i>新增追蹤
                            </button>
                        </div>
                    `;
                    initWatchlistEventDelegation();
                }
                return;
            }

            // 更新標籤 map
            watchlistTagsMap = {};
            basicData.data.forEach(item => {
                watchlistTagsMap[item.id] = item.tags || [];
            });

            // 🆕 立即渲染（價格顯示「載入中」）
            renderWatchlistCards(basicData.data);

            // 🆕 階段 2：背景載入價格
            const priceRes = await apiRequest('/api/watchlist/with-prices');
            const priceData = await priceRes.json();

            if (priceData.success && priceData.data) {
                priceData.data.forEach(item => {
                    watchlistTagsMap[item.id] = item.tags || [];
                });

                // 🆕 平滑更新（不閃爍）
                updateWatchlistPrices(priceData.data);
            }

        } catch (e) {
            console.error('載入追蹤清單失敗:', e);
            if (container) {
                container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗，請稍後再試</p>';
            }
        }
    }

    /**
     * 🆕 平滑更新價格（不重新渲染整個清單）
     */
    function updateWatchlistPrices(data) {
        // 更新全域資料
        watchlistData = data;
        if (window.AppState) {
            AppState.setWatchlist(data);
        }

        // 逐一更新卡片價格
        data.forEach(item => {
            const card = document.querySelector(`.stock-card[data-symbol="${item.symbol}"]`);
            if (!card) return;

            // 找到價格區域並更新
            const priceContainer = card.querySelector('.flex.items-baseline');
            if (priceContainer && item.price !== null) {
                const change = item.change_pct || 0;
                const changeClass = change >= 0 ? 'text-green-600' : 'text-red-600';
                const changeIcon = change >= 0 ? '▲' : '▼';
                const ma20Badge = getMa20Badge(item);

                // 目標價 badge
                let targetBadge = '';
                const hasTarget = item.target_price !== null && item.target_price !== undefined;
                if (hasTarget) {
                    const isAbove = item.target_direction !== 'below';
                    const dirIcon = isAbove ? 'fa-arrow-up' : 'fa-arrow-down';
                    const dirText = isAbove ? '↑' : '↓';
                    
                    if (item.target_reached) {
                        targetBadge = `<span class="ml-2 px-3 py-1 text-sm font-bold rounded-full bg-yellow-400 text-yellow-900 animate-pulse shadow">
                            <i class="fas fa-bell mr-1"></i>${dirText} 已達標 $${item.target_price.toLocaleString()}
                        </span>`;
                    } else {
                        const diff = ((item.target_price - item.price) / item.price * 100).toFixed(1);
                        const badgeStyle = isAbove 
                            ? 'bg-green-100 text-green-700 border border-green-400' 
                            : 'bg-red-100 text-red-700 border border-red-400';
                        targetBadge = `<span class="ml-2 px-3 py-1 text-sm font-medium rounded-full ${badgeStyle}">
                            <i class="fas ${dirIcon} mr-1"></i>目標 $${item.target_price.toLocaleString()} (${diff > 0 ? '+' : ''}${diff}%)
                        </span>`;
                    }
                }

                priceContainer.innerHTML = `
                    <span class="text-xl font-bold text-gray-800">$${item.price.toLocaleString()}</span>
                    <span class="${changeClass} text-sm font-medium">${changeIcon} ${Math.abs(change).toFixed(2)}%</span>
                    ${ma20Badge}
                    ${targetBadge}
                `;

                // 淡入效果
                priceContainer.style.opacity = '0';
                priceContainer.style.transition = 'opacity 0.3s';
                setTimeout(() => { priceContainer.style.opacity = '1'; }, 50);
            }

            // 更新名稱
            if (item.name) {
                const nameSpan = card.querySelector('.text-gray-500.text-sm.ml-2');
                if (nameSpan) {
                    nameSpan.textContent = item.name;
                }
            }

            // 更新到價提示
            if (item.target_reached) {
                card.classList.add('border-yellow-500', 'ring-2', 'ring-yellow-300');
                card.classList.remove('border-blue-500', 'border-purple-500');
            }
        });
    }


    async function loadAllWatchlistTags(items) {
        watchlistTagsMap = {};

        const promises = items.map(async item => {
            try {
                if (typeof getWatchlistTags === 'function') {
                    const tags = await getWatchlistTags(item.id);
                    watchlistTagsMap[item.id] = tags;
                }
            } catch (e) {
                watchlistTagsMap[item.id] = [];
            }
        });

        await Promise.all(promises);
    }

    async function addToWatchlist() {
        const symbol = $('addSymbol')?.value?.trim().toUpperCase();
        const assetType = $('addAssetType')?.value || 'stock';
        const note = $('addNote')?.value?.trim() || null;

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

                // ✅ P3: 樂觀更新 AppState
                if (window.AppState) {
                    AppState.addToWatchlist({
                        id: data.data?.id,
                        symbol,
                        asset_type: assetType,
                        note,
                        added_at: new Date().toISOString()
                    });
                }

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

                // ✅ P3: 更新 AppState
                if (window.AppState) {
                    AppState.removeFromWatchlist(symbol);
                }

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
        const modal = $('addWatchlistModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            $('addSymbol')?.focus();
        }
    }

    function hideAddWatchlistModal() {
        const modal = $('addWatchlistModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            if ($('addSymbol')) $('addSymbol').value = '';
            if ($('addNote')) $('addNote').value = '';
        }
    }

    function toggleWatchlistMenu() {
        const menu = $('watchlistMenu');
        if (menu) {
            menu.classList.toggle('hidden');
        }
    }

    // ============================================================
    // 匯出匯入
    // ============================================================

    function showImportWatchlistModal() {
        const modal = $('importWatchlistModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
        const menu = $('watchlistMenu');
        if (menu) menu.classList.add('hidden');
    }

    function hideImportWatchlistModal() {
        const modal = $('importWatchlistModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        const preview = $('importWatchlistPreview');
        if (preview) preview.innerHTML = '';
    }

    async function exportWatchlist() {
        try {
            const res = await apiRequest('/api/watchlist/export');
            const data = await res.json();

            if (!data.success) {
                showToast('匯出失敗');
                return;
            }

            const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `watchlist_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showToast('匯出成功');
        } catch (e) {
            console.error('匯出失敗:', e);
            showToast('匯出失敗');
        }
    }

    function previewWatchlistFile(event) {
        const file = event.target.files[0];
        if (!file) return;

        const preview = $('importWatchlistPreview');
        if (!preview) return;

        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                let items = [];
                const content = e.target.result;

                if (file.name.endsWith('.json')) {
                    items = JSON.parse(content);
                } else if (file.name.endsWith('.csv')) {
                    const lines = content.split('\n').filter(l => l.trim());
                    const headers = lines[0].split(',').map(h => h.trim());

                    for (let i = 1; i < lines.length; i++) {
                        const values = lines[i].split(',').map(v => v.trim());
                        const item = {};
                        headers.forEach((h, idx) => {
                            item[h] = values[idx];
                        });
                        items.push(item);
                    }
                }

                preview.innerHTML = `
                    <div class="mt-4 p-3 bg-gray-50 rounded-lg">
                        <p class="text-sm text-gray-600 mb-2">預覽 (${items.length} 筆):</p>
                        <ul class="text-sm space-y-1 max-h-40 overflow-y-auto">
                            ${items.slice(0, 10).map(item => `
                                <li class="flex justify-between">
                                    <span class="font-medium">${item.symbol}</span>
                                    <span class="text-gray-500">${item.asset_type || 'stock'}</span>
                                </li>
                            `).join('')}
                            ${items.length > 10 ? `<li class="text-gray-400">...還有 ${items.length - 10} 筆</li>` : ''}
                        </ul>
                    </div>
                `;
            } catch (err) {
                preview.innerHTML = '<p class="text-red-500 text-sm mt-2">檔案格式錯誤</p>';
            }
        };
        reader.readAsText(file);
    }

    async function importWatchlist() {
        const fileInput = $('importWatchlistFile');
        const file = fileInput?.files[0];

        if (!file) {
            showToast('請選擇檔案');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const token = localStorage.getItem('token');
            const res = await fetch('/api/watchlist/import', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });

            const data = await res.json();

            if (data.success) {
                showToast(`匯入成功: ${data.imported} 筆`);
                hideImportWatchlistModal();

                // 清除 AppState 快取，強制重新載入
                if (window.AppState) {
                    AppState.set('watchlistLoaded', false);
                }

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

    function showTargetPriceModal(itemId, symbol, currentTarget, direction) {
        currentTargetItemId = itemId;

        const modal = $('targetPriceModal');
        const symbolEl = $('targetPriceSymbol');
        const input = $('targetPriceInput');

        if (symbolEl) symbolEl.textContent = symbol;
        if (input) input.value = currentTarget || '';

        // 設定方向
        const dir = direction || 'above';
        const radioAbove = document.getElementById('directionAbove');
        const radioBelow = document.getElementById('directionBelow');
        if (radioAbove) radioAbove.checked = (dir === 'above');
        if (radioBelow) radioBelow.checked = (dir === 'below');
        
        // 更新方向選擇樣式
        if (typeof updateDirectionStyle === 'function') {
            updateDirectionStyle();
        }

        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            if (input) setTimeout(() => input.focus(), 100);
        }
    }

    function hideTargetPriceModal() {
        const modal = $('targetPriceModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        currentTargetItemId = null;
    }

    async function saveTargetPrice() {
        if (!currentTargetItemId) return;

        const input = $('targetPriceInput');
        const targetPrice = parseFloat(input?.value);

        if (isNaN(targetPrice) || targetPrice <= 0) {
            showToast('請輸入有效的目標價');
            return;
        }

        try {
            const res = await apiRequest(`/api/watchlist/${currentTargetItemId}/target-price`, {
                method: 'PUT',
                body: { 
                    target_price: targetPrice,
                    target_direction: document.querySelector('input[name="targetDirection"]:checked')?.value || 'above'
                }
            });

            const data = await res.json();

            if (data.success) {
                showToast('目標價已設定');
                hideTargetPriceModal();
                // 🔧 清除 AppState 快取，強制重新載入
                if (window.AppState) {
                    AppState.watchlistLoaded = false;
                }
                await loadWatchlist();
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

        try {
            // 🔧 使用 PUT 方法，傳入 null 來清除目標價
            const res = await apiRequest(`/api/watchlist/${currentTargetItemId}/target-price`, {
                method: 'PUT',
                body: { target_price: null, target_direction: null }
            });

            const data = await res.json();

            if (data.success) {
                showToast('已清除目標價');
                hideTargetPriceModal();
                // 🔧 清除 AppState 快取，強制重新載入
                if (window.AppState) {
                    AppState.watchlistLoaded = false;
                }
                await loadWatchlist();
            } else {
                showToast(data.detail || '清除失敗');
            }
        } catch (e) {
            console.error('清除目標價失敗:', e);
            showToast('清除失敗');
        }
    }

    // ============================================================
    // 儀表板快覽
    // ============================================================

    async function loadWatchlistOverview() {
        const container = $('dashboardWatchlist');
        if (!container) return;

        const currentUser = typeof getCurrentUser === 'function' ? getCurrentUser() : window.currentUser;

        if (!currentUser || !currentUser.id) {
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
                        <button data-action="goto-search" class="mt-2 text-blue-600 text-sm">前往查詢股票</button>
                    </div>
                `;
                return;
            }

            const items = data.data.slice(0, 5);
            let html = '<div class="space-y-2" id="dashboardWatchlistItems">';

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
                    <button data-action="trade" data-symbol="${item.symbol}" data-name="${item.name || ''}" data-market="${market}" data-type="buy"
                            class="p-1.5 bg-green-100 text-green-600 rounded text-xs hover:bg-green-200">
                        <i class="fas fa-plus"></i>
                    </button>
                `;

                html += `
                    <div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                        <div class="flex items-center cursor-pointer" data-action="analyze" data-symbol="${item.symbol}">
                            <span class="font-medium text-gray-800">${item.symbol}</span>
                            <span class="text-gray-500 text-sm ml-2">${priceText}</span>
                            ${changeText}
                        </div>
                        <div class="flex items-center gap-1">
                            ${tradeButtons}
                            <button data-action="analyze" data-symbol="${item.symbol}" class="p-1.5 bg-orange-100 text-orange-600 rounded text-xs hover:bg-orange-200">
                                <i class="fas fa-chart-line"></i>
                            </button>
                        </div>
                    </div>
                `;
            }

            html += '</div>';
            container.innerHTML = html;

            // 初始化儀表板事件委託
            container.addEventListener('click', handleWatchlistClick);

        } catch (e) {
            console.error('載入追蹤快覽失敗:', e);
            container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
        }
    }

    // ============================================================
    // 導出
    // ============================================================

    // 掛載到 SELA 命名空間
    if (window.SELA) {
        window.SELA.watchlist = {
            load: loadWatchlist,
            loadOverview: loadWatchlistOverview,
            add: addToWatchlist,
            remove: removeFromWatchlist,
            changeSort: changeWatchlistSort,
            exportData: exportWatchlist,
            importData: importWatchlist
        };
    }

    // 全域導出（向後兼容）
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

})();
