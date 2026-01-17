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
                <div class="text-center py-8 text-gray-400">
                    <i class="fas fa-building text-3xl mb-2"></i>
                    <p>尚未新增券商</p>
                </div>
            `;
            return;
        }

        container.innerHTML = brokerList.map(b => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-3">
                    <span class="w-4 h-4 rounded-full" style="background-color: ${b.color || '#6B7280'}"></span>
                    <span class="font-medium">${b.name}</span>
                    ${b.is_default ? '<span class="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">預設</span>' : ''}
                </div>
                <div class="flex gap-2">
                    <button onclick="editBroker(${b.id})" class="text-gray-500 hover:text-blue-600">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteBroker(${b.id})" class="text-gray-500 hover:text-red-600">
                        <i class="fas fa-trash"></i>
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
    // 導出
    // ============================================================

    window.loadBrokerManager = loadBrokerManager;
    window.addBroker = addBroker;
    window.editBroker = editBroker;
    window.deleteBroker = deleteBroker;
    window.setDefaultBroker = setDefaultBroker;

    console.log('🏢 broker.js 券商管理模組已載入');
})();
