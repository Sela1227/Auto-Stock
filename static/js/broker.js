/**
 * 券商管理模組
 */

(function() {
    'use strict';

    let brokerList = [];

    // ============================================================
    // 券商管理 API
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
            console.error('載入券商失敗:', e);
        }
    }

    function renderBrokerManager() {
        const container = document.getElementById('brokerManagerList');
        if (!container) return;

        if (brokerList.length === 0) {
            container.innerHTML = `
                <div class="text-center py-6 text-gray-400">
                    <i class="fas fa-building text-2xl mb-2"></i>
                    <p class="text-sm">尚未新增券商</p>
                    <p class="text-xs mt-1">新增交易時可快速建立</p>
                </div>
            `;
            return;
        }

        container.innerHTML = brokerList.map(b => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div class="flex items-center gap-3">
                    <span class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: ${b.color || '#6B7280'}"></span>
                    <span class="font-medium text-gray-800">${b.name}</span>
                    ${b.is_default ? '<span class="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">預設</span>' : ''}
                </div>
                <div class="flex gap-1">
                    ${!b.is_default ? `<button onclick="setDefaultBroker(${b.id})" class="p-1.5 text-gray-400 hover:text-yellow-500" title="設為預設">
                        <i class="fas fa-star text-sm"></i>
                    </button>` : ''}
                    <button onclick="editBroker(${b.id})" class="p-1.5 text-gray-400 hover:text-blue-600" title="編輯">
                        <i class="fas fa-edit text-sm"></i>
                    </button>
                    <button onclick="deleteBroker(${b.id})" class="p-1.5 text-gray-400 hover:text-red-600" title="刪除">
                        <i class="fas fa-trash text-sm"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    async function addBroker() {
        const name = prompt('請輸入券商名稱：');
        if (!name || !name.trim()) return;

        try {
            const res = await apiRequest('/api/brokers', {
                method: 'POST',
                body: { name: name.trim() }
            });
            const data = await res.json();
            if (data.success) {
                showToast('券商已新增');
                await loadBrokerManager();
            } else {
                showToast(data.detail || '新增失敗');
            }
        } catch (e) {
            console.error('新增券商失敗:', e);
            showToast('新增失敗');
        }
    }

    async function editBroker(id) {
        const broker = brokerList.find(b => b.id === id);
        if (!broker) return;

        const name = prompt('修改券商名稱：', broker.name);
        if (!name || !name.trim() || name.trim() === broker.name) return;

        try {
            const res = await apiRequest(`/api/brokers/${id}`, {
                method: 'PUT',
                body: { name: name.trim() }
            });
            const data = await res.json();
            if (data.success) {
                showToast('券商已更新');
                await loadBrokerManager();
            } else {
                showToast(data.detail || '更新失敗');
            }
        } catch (e) {
            console.error('更新券商失敗:', e);
            showToast('更新失敗');
        }
    }

    async function deleteBroker(id) {
        const broker = brokerList.find(b => b.id === id);
        if (!broker) return;

        if (!confirm(`確定要刪除「${broker.name}」嗎？\n\n已關聯的交易記錄將會移除券商資訊。`)) return;

        try {
            const res = await apiRequest(`/api/brokers/${id}`, {
                method: 'DELETE'
            });
            const data = await res.json();
            if (data.success) {
                showToast('券商已刪除');
                await loadBrokerManager();
            } else {
                showToast(data.detail || '刪除失敗');
            }
        } catch (e) {
            console.error('刪除券商失敗:', e);
            showToast('刪除失敗');
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
                showToast('已設為預設券商');
                await loadBrokerManager();
            }
        } catch (e) {
            console.error('設定預設券商失敗:', e);
        }
    }

    // ============================================================
    // 自動插入券商管理區塊到投資記錄頁面
    // ============================================================
    
    function insertBrokerManagerSection() {
        // 找到美股交易記錄區塊
        const usTransactionList = document.getElementById('usTransactionList');
        if (!usTransactionList) return;
        
        // 找到其父容器（美股交易記錄卡片）
        const usCard = usTransactionList.closest('.bg-white');
        if (!usCard) return;
        
        // 檢查是否已經存在券商管理區塊
        if (document.getElementById('brokerManagerSection')) return;
        
        // 建立券商管理區塊
        const brokerSection = document.createElement('div');
        brokerSection.id = 'brokerManagerSection';
        brokerSection.className = 'bg-white rounded-xl shadow p-4 mt-4';
        brokerSection.innerHTML = `
            <h3 class="font-semibold text-gray-700 mb-3 flex items-center justify-between">
                <span><i class="fas fa-building mr-2 text-purple-500"></i>券商管理</span>
                <button onclick="addBroker()" class="text-sm bg-purple-500 hover:bg-purple-600 text-white px-3 py-1.5 rounded-lg transition-colors">
                    <i class="fas fa-plus mr-1"></i>新增
                </button>
            </h3>
            <div id="brokerManagerList" class="space-y-2">
                <p class="text-center py-4 text-gray-400">載入中...</p>
            </div>
        `;
        
        // 插入到美股記錄卡片後面
        usCard.parentNode.insertBefore(brokerSection, usCard.nextSibling);
        
        // 載入券商資料
        loadBrokerManager();
    }

    // ============================================================
    // 初始化
    // ============================================================
    
    function initBrokerManager() {
        // 延遲執行，確保 DOM 已載入
        setTimeout(() => {
            insertBrokerManagerSection();
        }, 500);
    }

    // 監聽頁面切換（如果使用 SPA 導航）
    document.addEventListener('DOMContentLoaded', initBrokerManager);
    
    // 如果頁面已載入，直接執行
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        initBrokerManager();
    }

    // ============================================================
    // 導出
    // ============================================================

    window.loadBrokerManager = loadBrokerManager;
    window.addBroker = addBroker;
    window.editBroker = editBroker;
    window.deleteBroker = deleteBroker;
    window.setDefaultBroker = setDefaultBroker;
    window.insertBrokerManagerSection = insertBrokerManagerSection;

})();
