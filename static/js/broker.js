/**
 * åˆ¸å•†ç®¡ç†æ¨¡çµ„
 */

(function() {
    'use strict';

    let brokerList = [];

    // ============================================================
    // åˆ¸å•†ç®¡ç† API
    // ============================================================

    async function loadBrokerManager() {
        try {
            const res = await apiRequest('/api/brokers');
            const data = await res.json();
            if (data.success) {
                brokerList = data.data || [];
                renderBrokerManager();
            }
        } catch (e) {
            console.error('è¼‰å…¥åˆ¸å•†å¤±æ•—:', e);
        }
    }

    function renderBrokerManager() {
        const container = document.getElementById('brokerManagerList');
        if (!container) return;

        if (brokerList.length === 0) {
            container.innerHTML = `
                <div class="text-center py-6 text-gray-400">
                    <i class="fas fa-building text-2xl mb-2"></i>
                    <p class="text-sm">å°šæœªæ–°å¢žåˆ¸å•†</p>
                    <p class="text-xs mt-1">æ–°å¢žäº¤æ˜“æ™‚å¯å¿«é€Ÿå»ºç«‹</p>
                </div>
            `;
            return;
        }

        container.innerHTML = brokerList.map(b => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div class="flex items-center gap-3">
                    <span class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: ${b.color || '#6B7280'}"></span>
                    <span class="font-medium text-gray-800">${b.name}</span>
                    ${b.is_default ? '<span class="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">é è¨­</span>' : ''}
                </div>
                <div class="flex gap-1">
                    ${!b.is_default ? `<button onclick="setDefaultBroker(${b.id})" class="p-1.5 text-gray-400 hover:text-yellow-500" title="è¨­ç‚ºé è¨­">
                        <i class="fas fa-star text-sm"></i>
                    </button>` : ''}
                    <button onclick="editBroker(${b.id})" class="p-1.5 text-gray-400 hover:text-blue-600" title="ç·¨è¼¯">
                        <i class="fas fa-edit text-sm"></i>
                    </button>
                    <button onclick="deleteBroker(${b.id})" class="p-1.5 text-gray-400 hover:text-red-600" title="åˆªé™¤">
                        <i class="fas fa-trash text-sm"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    async function addBroker() {
        const name = prompt('è«‹è¼¸å…¥åˆ¸å•†åç¨±ï¼š');
        if (!name || !name.trim()) return;

        try {
            const res = await apiRequest('/api/brokers', {
                method: 'POST',
                body: { name: name.trim() }
            });
            const data = await res.json();
            if (data.success) {
                showToast('åˆ¸å•†å·²æ–°å¢ž');
                await loadBrokerManager();
            } else {
                showToast(data.detail || 'æ–°å¢žå¤±æ•—');
            }
        } catch (e) {
            console.error('æ–°å¢žåˆ¸å•†å¤±æ•—:', e);
            showToast('æ–°å¢žå¤±æ•—');
        }
    }

    async function editBroker(id) {
        const broker = brokerList.find(b => b.id === id);
        if (!broker) return;

        const name = prompt('ä¿®æ”¹åˆ¸å•†åç¨±ï¼š', broker.name);
        if (!name || !name.trim() || name.trim() === broker.name) return;

        try {
            const res = await apiRequest(`/api/brokers/${id}`, {
                method: 'PUT',
                body: { name: name.trim() }
            });
            const data = await res.json();
            if (data.success) {
                showToast('åˆ¸å•†å·²æ›´æ–°');
                await loadBrokerManager();
            } else {
                showToast(data.detail || 'æ›´æ–°å¤±æ•—');
            }
        } catch (e) {
            console.error('æ›´æ–°åˆ¸å•†å¤±æ•—:', e);
            showToast('æ›´æ–°å¤±æ•—');
        }
    }

    async function deleteBroker(id) {
        const broker = brokerList.find(b => b.id === id);
        if (!broker) return;

        if (!confirm(`ç¢ºå®šè¦åˆªé™¤ã€Œ${broker.name}ã€å—Žï¼Ÿ\n\nå·²é—œè¯çš„äº¤æ˜“è¨˜éŒ„å°‡æœƒç§»é™¤åˆ¸å•†è³‡è¨Šã€‚`)) return;

        try {
            const res = await apiRequest(`/api/brokers/${id}`, {
                method: 'DELETE'
            });
            const data = await res.json();
            if (data.success) {
                showToast('åˆ¸å•†å·²åˆªé™¤');
                await loadBrokerManager();
            } else {
                showToast(data.detail || 'åˆªé™¤å¤±æ•—');
            }
        } catch (e) {
            console.error('åˆªé™¤åˆ¸å•†å¤±æ•—:', e);
            showToast('åˆªé™¤å¤±æ•—');
        }
    }

    async function setDefaultBroker(id) {
        try {
            const res = await apiRequest(`/api/brokers/${id}`, {
                method: 'PUT',
                body: { is_default: true }
            });
            const data = await res.json();
            if (data.success) {
                showToast('å·²è¨­ç‚ºé è¨­åˆ¸å•†');
                await loadBrokerManager();
            }
        } catch (e) {
            console.error('è¨­å®šé è¨­åˆ¸å•†å¤±æ•—:', e);
        }
    }

    // ============================================================
    // è‡ªå‹•æ’å…¥åˆ¸å•†ç®¡ç†å€å¡Šåˆ°æŠ•è³‡è¨˜éŒ„é é¢
    // ============================================================
    
    function insertBrokerManagerSection() {
        // æ‰¾åˆ°ç¾Žè‚¡äº¤æ˜“è¨˜éŒ„å€å¡Š
        const usTransactionList = document.getElementById('usTransactionList');
        if (!usTransactionList) return;
        
        // æ‰¾åˆ°å…¶çˆ¶å®¹å™¨ï¼ˆç¾Žè‚¡äº¤æ˜“è¨˜éŒ„å¡ç‰‡ï¼‰
        const usCard = usTransactionList.closest('.bg-white');
        if (!usCard) return;
        
        // æª¢æŸ¥æ˜¯å¦å·²ç¶“å­˜åœ¨åˆ¸å•†ç®¡ç†å€å¡Š
        if (document.getElementById('brokerManagerSection')) return;
        
        // å»ºç«‹åˆ¸å•†ç®¡ç†å€å¡Š
        const brokerSection = document.createElement('div');
        brokerSection.id = 'brokerManagerSection';
        brokerSection.className = 'bg-white rounded-xl shadow p-4 mt-4';
        brokerSection.innerHTML = `
            <h3 class="font-semibold text-gray-700 mb-3 flex items-center justify-between">
                <span><i class="fas fa-building mr-2 text-purple-500"></i>åˆ¸å•†ç®¡ç†</span>
                <button onclick="addBroker()" class="text-sm bg-purple-500 hover:bg-purple-600 text-white px-3 py-1.5 rounded-lg transition-colors">
                    <i class="fas fa-plus mr-1"></i>æ–°å¢ž
                </button>
            </h3>
            <div id="brokerManagerList" class="space-y-2">
                <p class="text-center py-4 text-gray-400">è¼‰å…¥ä¸­...</p>
            </div>
        `;
        
        // æ’å…¥åˆ°ç¾Žè‚¡è¨˜éŒ„å¡ç‰‡å¾Œé¢
        usCard.parentNode.insertBefore(brokerSection, usCard.nextSibling);
        
        // è¼‰å…¥åˆ¸å•†è³‡æ–™
        loadBrokerManager();
    }

    // ============================================================
    // åˆå§‹åŒ–
    // ============================================================
    
    function initBrokerManager() {
        // å»¶é²åŸ·è¡Œï¼Œç¢ºä¿ DOM å·²è¼‰å…¥
        setTimeout(() => {
            insertBrokerManagerSection();
        }, 500);
    }

    // ç›£è½é é¢åˆ‡æ›ï¼ˆå¦‚æžœä½¿ç”¨ SPA å°Žèˆªï¼‰
    document.addEventListener('DOMContentLoaded', initBrokerManager);
    
    // å¦‚æžœé é¢å·²è¼‰å…¥ï¼Œç›´æŽ¥åŸ·è¡Œ
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        initBrokerManager();
    }

    // ============================================================
    // å°Žå‡º
    // ============================================================

    window.loadBrokerManager = loadBrokerManager;
    window.addBroker = addBroker;
    window.editBroker = editBroker;
    window.deleteBroker = deleteBroker;
    window.setDefaultBroker = setDefaultBroker;
    window.insertBrokerManagerSection = insertBrokerManagerSection;

    console.log('ðŸ¢ broker.js åˆ¸å•†ç®¡ç†æ¨¡çµ„å·²è¼‰å…¥');
})();