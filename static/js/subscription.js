/**
 * 訂閱精選模組
 */

(function() {
    'use strict';
    
    let subscriptionSources = [];
    
    /**
     * 載入訂閱資料
     */
    async function loadSubscriptionData() {
        const container = document.getElementById('subscriptionSourcesList');
        const picksContainer = document.getElementById('subscriptionPicksList');
        const countEl = document.getElementById('subscriptionPicksCount');
        
        if (!container) return;
        
        try {
            // 載入所有訂閱來源
            const sourcesRes = await fetch('/api/subscription/sources');
            const sourcesData = await sourcesRes.json();
            
            if (sourcesData.success) {
                subscriptionSources = sourcesData.data || [];
            }
            
            // 載入用戶訂閱狀態
            const myRes = await apiRequest('/api/subscription/my');
            const myData = await myRes.json();
            const mySubscriptions = myData.success ? (myData.data || []).map(s => s.source_id) : [];
            
            if (subscriptionSources.length === 0) {
                container.innerHTML = '<p class="text-gray-400 text-center py-4">尚無訂閱來源</p>';
            } else {
                container.innerHTML = '';
                for (const source of subscriptionSources) {
                    const isSubscribed = mySubscriptions.includes(source.id);
                    container.innerHTML += `
                        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2">
                            <div class="flex items-center flex-1 min-w-0">
                                <i class="fas fa-rss text-orange-500 mr-3 flex-shrink-0"></i>
                                <div class="min-w-0">
                                    <p class="font-medium text-gray-800 truncate">${source.name}</p>
                                    <p class="text-xs text-gray-500 truncate">${source.description || ''}</p>
                                </div>
                            </div>
                            <button onclick="toggleSubscription(${source.id}, ${isSubscribed})" 
                                    class="ml-3 px-3 py-1.5 text-sm rounded-lg flex-shrink-0 ${isSubscribed 
                                        ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                                        : 'bg-gray-200 text-gray-600 hover:bg-gray-300'}">
                                <i class="fas fa-${isSubscribed ? 'check' : 'plus'} mr-1"></i>
                                ${isSubscribed ? '已訂閱' : '訂閱'}
                            </button>
                        </div>
                    `;
                }
            }
            
            // 載入精選股票
            await loadSubscriptionPicks();
            
        } catch (e) {
            console.error('載入訂閱資料失敗:', e);
            container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
        }
    }
    
    /**
     * 切換訂閱狀態
     */
    async function toggleSubscription(sourceId, isCurrentlySubscribed) {
        try {
            const endpoint = isCurrentlySubscribed
                ? `/api/subscription/unsubscribe/${sourceId}`
                : `/api/subscription/subscribe/${sourceId}`;
            
            const res = await apiRequest(endpoint, { method: 'POST' });
            const data = await res.json();
            
            if (data.success) {
                showToast(isCurrentlySubscribed ? '已取消訂閱' : '已訂閱');
                loadSubscriptionData();
            } else {
                showToast(data.detail || '操作失敗');
            }
        } catch (e) {
            console.error('切換訂閱失敗:', e);
            showToast('操作失敗');
        }
    }
    
    /**
     * 載入精選股票
     */
    async function loadSubscriptionPicks() {
        const container = document.getElementById('subscriptionPicksList');
        const countEl = document.getElementById('subscriptionPicksCount');
        
        if (!container) return;
        
        try {
            const res = await apiRequest('/api/subscription/picks');
            const data = await res.json();
            
            if (data.success && data.data && data.data.length > 0) {
                if (countEl) countEl.textContent = `共 ${data.data.length} 檔`;
                
                container.innerHTML = data.data.map(p => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2 cursor-pointer hover:bg-gray-100"
                         onclick="searchSymbol('${p.symbol}')">
                        <div class="flex items-center">
                            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                                <span class="font-bold text-blue-600 text-sm">${p.symbol.substring(0, 2)}</span>
                            </div>
                            <div>
                                <p class="font-medium text-gray-800">${p.symbol}</p>
                                <p class="text-xs text-gray-500">${p.source_name || ''} · ${new Date(p.mentioned_at).toLocaleDateString()}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="text-xs text-gray-400">提及 ${p.mention_count || 1} 次</span>
                            <button onclick="event.stopPropagation(); quickAddToWatchlist('${p.symbol}', 'stock')" 
                                    class="ml-2 px-2 py-1 text-xs bg-orange-100 text-orange-600 rounded hover:bg-orange-200">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                `).join('');
            } else {
                if (countEl) countEl.textContent = '';
                container.innerHTML = '<p class="text-gray-400 text-center py-4">尚無精選股票</p>';
            }
        } catch (e) {
            console.error('載入精選股票失敗:', e);
            container.innerHTML = '<p class="text-gray-400 text-center py-4">尚無精選股票</p>';
        }
    }
    
    /**
     * 重新整理
     */
    async function refreshSubscriptionPicks() {
        const btn = event?.target?.closest('button');
        const icon = btn?.querySelector('i');
        if (icon) icon.classList.add('fa-spin');
        
        await loadSubscriptionData();
        
        if (icon) setTimeout(() => icon.classList.remove('fa-spin'), 500);
        showToast('已更新');
    }
    
    // 導出到全域
    window.loadSubscriptionData = loadSubscriptionData;
    window.loadSubscriptionPicks = loadSubscriptionPicks;
    window.toggleSubscription = toggleSubscription;
    window.refreshSubscriptionPicks = refreshSubscriptionPicks;
    
    console.log('📡 subscription.js 模組已載入');
})();
