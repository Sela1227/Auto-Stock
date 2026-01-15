/**
 * 訂閱精選模組
 */

(function() {
    'use strict';
    
    /**
     * 載入訂閱精選
     */
    async function loadSubscriptionPicks() {
        const sourcesEl = document.getElementById('subscriptionSourcesList');
        const picksEl = document.getElementById('subscriptionPicksList');
        const countEl = document.getElementById('subscriptionPicksCount');
        
        if (!sourcesEl || !picksEl) return;
        
        try {
            // 載入訂閱來源
            const sourcesRes = await apiRequest('/api/subscriptions/sources');
            const sourcesData = await sourcesRes.json();
            
            if (sourcesData.success && sourcesData.data) {
                sourcesEl.innerHTML = sourcesData.data.map(s => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2">
                        <div class="flex items-center">
                            <i class="fas fa-rss text-orange-500 mr-3"></i>
                            <div>
                                <p class="font-medium text-gray-800">${s.name}</p>
                                <p class="text-xs text-gray-500">${s.url}</p>
                            </div>
                        </div>
                        <span class="px-2 py-1 text-xs rounded ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}">
                            ${s.is_active ? '啟用' : '停用'}
                        </span>
                    </div>
                `).join('') || '<p class="text-gray-400 text-center py-4">尚無訂閱來源</p>';
            }
            
            // 載入精選股票
            const picksRes = await apiRequest('/api/subscriptions/picks');
            const picksData = await picksRes.json();
            
            if (picksData.success && picksData.data && picksData.data.length > 0) {
                if (countEl) countEl.textContent = `共 ${picksData.data.length} 檔`;
                
                picksEl.innerHTML = picksData.data.map(p => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2 cursor-pointer hover:bg-gray-100"
                         onclick="searchSymbol('${p.symbol}')">
                        <div class="flex items-center">
                            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                                <span class="font-bold text-blue-600 text-sm">${p.symbol.substring(0, 2)}</span>
                            </div>
                            <div>
                                <p class="font-medium text-gray-800">${p.symbol}</p>
                                <p class="text-xs text-gray-500">${p.source_name} · ${new Date(p.mentioned_at).toLocaleDateString()}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="text-xs text-gray-400">提及 ${p.mention_count} 次</span>
                            <button onclick="event.stopPropagation(); quickAddToWatchlist('${p.symbol}', 'stock')" 
                                    class="ml-2 px-2 py-1 text-xs bg-orange-100 text-orange-600 rounded hover:bg-orange-200">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
            } else {
                if (countEl) countEl.textContent = '';
                picksEl.innerHTML = '<p class="text-gray-400 text-center py-4">尚無精選股票</p>';
            }
            
        } catch (e) {
            console.error('載入訂閱精選失敗:', e);
            sourcesEl.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
            picksEl.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
        }
    }
    
    /**
     * 重新整理
     */
    async function refreshSubscriptionPicks() {
        const btn = event?.target?.closest('button');
        const icon = btn?.querySelector('i');
        if (icon) icon.classList.add('fa-spin');
        
        await loadSubscriptionPicks();
        
        if (icon) setTimeout(() => icon.classList.remove('fa-spin'), 500);
        showToast('已更新');
    }
    
    // 導出到全域
    window.loadSubscriptionPicks = loadSubscriptionPicks;
    window.refreshSubscriptionPicks = refreshSubscriptionPicks;
    
    console.log('📡 subscription.js 模組已載入');
})();
