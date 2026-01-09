        // ========== 追蹤清單 - 使用快取版本 ==========
        // 改用 /api/watchlist/with-prices API，直接取得價格
        
        async function loadWatchlist() {
            const container = document.getElementById('watchlistContent');
            
            if (!currentUser || !currentUser.id) {
                console.error('loadWatchlist: 用戶未登入');
                container.innerHTML = '<p class="text-red-500 text-center py-4">請先登入</p>';
                return;
            }
            
            // 顯示載入中
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-spinner fa-spin text-2xl text-blue-600"></i>
                    <p class="mt-2 text-gray-500">載入中...</p>
                </div>
            `;
            
            try {
                // ★ 改用新 API：一次取得清單 + 價格
                const res = await apiRequest('/api/watchlist/with-prices');
                const data = await res.json();
                
                console.log('追蹤清單(含價格):', data);
                
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
                
                // 顯示快取更新時間（如果有）
                let cacheInfo = '';
                if (data.cache_info && data.cache_info.oldest_update) {
                    const updateTime = new Date(data.cache_info.oldest_update);
                    const now = new Date();
                    const diffMin = Math.round((now - updateTime) / 60000);
                    cacheInfo = `<p class="text-xs text-gray-400 text-right mb-2">價格更新於 ${diffMin} 分鐘前</p>`;
                }
                
                let html = cacheInfo + '<div class="space-y-3">';
                
                for (const item of data.data) {
                    const typeClass = item.asset_type === 'crypto' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700';
                    const typeText = item.asset_type === 'crypto' ? '幣' : '股';
                    
                    // 價格顯示（直接從 API 回應取得）
                    let priceInfo = '';
                    if (item.price !== null) {
                        const change = item.change_pct || 0;
                        const changeClass = change >= 0 ? 'text-green-600' : 'text-red-600';
                        const changeIcon = change >= 0 ? '▲' : '▼';
                        priceInfo = `
                            <div class="flex items-baseline gap-2 mt-2">
                                <span class="text-xl font-bold text-gray-800">$${item.price.toLocaleString()}</span>
                                <span class="${changeClass} text-sm font-medium">${changeIcon} ${Math.abs(change).toFixed(2)}%</span>
                            </div>
                        `;
                    } else {
                        priceInfo = `
                            <div class="flex items-baseline gap-2 mt-2">
                                <span class="text-gray-400 text-sm">價格未更新</span>
                            </div>
                        `;
                    }
                    
                    // 顯示股票名稱
                    const nameDisplay = item.name ? `<span class="text-gray-500 text-sm ml-2">${item.name}</span>` : '';
                    
                    html += `
                        <div class="stock-card bg-white rounded-xl shadow-sm p-4 border-l-4 ${item.asset_type === 'crypto' ? 'border-purple-500' : 'border-blue-500'}">
                            <div class="flex items-start justify-between">
                                <div class="flex-1">
                                    <div class="flex items-center flex-wrap">
                                        <span class="font-bold text-lg text-gray-800">${item.symbol}</span>
                                        <span class="ml-2 px-2 py-0.5 rounded text-xs ${typeClass}">${typeText}</span>
                                        ${nameDisplay}
                                    </div>
                                    ${priceInfo}
                                    ${item.note ? `<p class="text-gray-500 text-sm mt-2 italic"><i class="fas fa-sticky-note mr-1"></i>${item.note}</p>` : ''}
                                </div>
                                <button onclick="removeFromWatchlist('${item.symbol}')" class="p-2 text-gray-400 hover:text-red-500 touch-target">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                            <div class="flex items-center justify-between mt-3 pt-3 border-t">
                                <span class="text-gray-400 text-xs"><i class="fas fa-clock mr-1"></i>加入於 ${new Date(item.added_at).toLocaleDateString()}</span>
                                <button onclick="searchSymbol('${item.symbol}')" class="px-4 py-2 bg-orange-500 text-white rounded-lg text-sm hover:bg-orange-600 touch-target">
                                    <i class="fas fa-chart-line mr-1"></i>詳細分析
                                </button>
                            </div>
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
        
        // ========== 首頁追蹤清單快覽 ==========
        async function loadWatchlistOverview() {
            const container = document.getElementById('dashboardWatchlist');
            
            try {
                // ★ 同樣使用快取 API
                const res = await apiRequest('/api/watchlist/with-prices');
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
                
                // 只顯示前 5 筆
                const items = data.data.slice(0, 5);
                let html = '<div class="space-y-2">';
                
                for (const item of items) {
                    const change = item.change_pct || 0;
                    const changeClass = change >= 0 ? 'text-green-600' : 'text-red-600';
                    const changeText = item.price !== null 
                        ? `<span class="${changeClass} text-sm">${change >= 0 ? '+' : ''}${change.toFixed(2)}%</span>`
                        : '';
                    
                    const priceText = item.price !== null
                        ? `<span class="text-gray-700 font-medium">$${item.price.toLocaleString()}</span>`
                        : '<span class="text-gray-400 text-sm">--</span>';
                    
                    html += `
                        <div class="flex items-center justify-between py-2 border-b last:border-0 cursor-pointer hover:bg-gray-50 -mx-2 px-2 rounded" 
                             onclick="searchSymbol('${item.symbol}')">
                            <div class="flex items-center">
                                <span class="font-medium text-gray-800 w-20">${item.symbol}</span>
                                <span class="text-xs px-2 py-0.5 rounded ${item.asset_type === 'crypto' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}">
                                    ${item.asset_type === 'crypto' ? '幣' : '股'}
                                </span>
                            </div>
                            <div class="text-right">
                                ${priceText}
                                ${changeText}
                            </div>
                        </div>
                    `;
                }
                
                html += '</div>';
                
                // 如果超過 5 筆，顯示「查看全部」
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
                console.error('載入追蹤清單快覽失敗', e);
                container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
            }
        }
