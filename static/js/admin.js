// ============================================================
// 管理後台 - admin.js
// ============================================================

let adminCurrentPage = 1;
let adminTotalPages = 1;

// ==================== 初始化 ====================
function initAdmin() {
    // 只有管理員才初始化
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.is_admin) {
        // 顯示管理員入口
        const adminMobileLink = document.getElementById('adminMobileLink');
        if (adminMobileLink) {
            adminMobileLink.classList.remove('hidden');
            adminMobileLink.classList.add('flex');
        }
    }
}

// ==================== API 請求封裝 (返回 JSON) ====================
async function adminApiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/static/index.html';
        return null;
    }
    
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    try {
        const response = await fetch(endpoint, {
            ...options,
            headers
        });
        
        if (response.status === 401) {
            localStorage.clear();
            window.location.href = '/static/index.html';
            return null;
        }
        
        if (response.status === 403) {
            showToast('您沒有管理員權限', 'error');
            showSection('dashboard');
            return null;
        }
        
        return await response.json();
    } catch (e) {
        console.error('Admin API 請求失敗:', e);
        return null;
    }
}

// ==================== 載入統計 ====================
async function adminLoadStats() {
    try {
        const data = await adminApiRequest('/api/admin/stats');
        if (data && data.success) {
            document.getElementById('adminStatTotal').textContent = data.stats.total_users;
            document.getElementById('adminStatTotalLogins').textContent = data.stats.total_logins;
            document.getElementById('adminStatToday').textContent = data.stats.today_logins;
            document.getElementById('adminStatBlocked').textContent = data.stats.blocked_users;
            document.getElementById('adminStatAdmin').textContent = data.stats.admin_users;
        }
    } catch (e) {
        console.error('載入統計失敗', e);
    }
}

// ==================== 用戶管理 ====================
async function adminLoadUsers() {
    const search = document.getElementById('adminSearchInput')?.value || '';
    const blockedOnly = document.getElementById('adminBlockedOnly')?.checked || false;
    
    let url = `/api/admin/users?page=${adminCurrentPage}&page_size=15`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (blockedOnly) url += `&blocked_only=true`;
    
    try {
        const data = await adminApiRequest(url);
        if (data && data.success) {
            adminRenderUsers(data.users);
            adminTotalPages = data.pagination.total_pages;
            document.getElementById('adminPageInfo').textContent = 
                `第 ${data.pagination.page} / ${adminTotalPages} 頁，共 ${data.pagination.total} 筆`;
            document.getElementById('adminPrevPage').disabled = adminCurrentPage <= 1;
            document.getElementById('adminNextPage').disabled = adminCurrentPage >= adminTotalPages;
        }
    } catch (e) {
        showToast('載入用戶失敗', 'error');
    }
}

function adminRenderUsers(users) {
    const tbody = document.getElementById('adminUserList');
    
    if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-gray-400">沒有找到用戶</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(u => `
        <tr class="hover:bg-gray-50">
            <td class="px-3 py-2">
                <div class="flex items-center">
                    <img src="${u.picture_url || '/static/logo.png'}" 
                        class="w-8 h-8 rounded-full mr-2" 
                        onerror="this.src='/static/logo.png'">
                    <div>
                        <div class="font-medium text-gray-900 text-sm">${adminEscapeHtml(u.display_name || '未命名')}</div>
                        <div class="text-xs text-gray-400">ID: ${u.id}</div>
                    </div>
                </div>
            </td>
            <td class="px-3 py-2 text-sm text-gray-500 hidden md:table-cell">
                ${adminEscapeHtml(u.email || '-')}
            </td>
            <td class="px-3 py-2">
                <div class="flex flex-wrap gap-1">
                    ${u.is_admin ? '<span class="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">管理員</span>' : ''}
                    ${u.is_blocked 
                        ? '<span class="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-800">已封鎖</span>' 
                        : '<span class="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-800">正常</span>'}
                </div>
            </td>
            <td class="px-3 py-2 text-center">
                <span class="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700">${u.login_count || 0}</span>
            </td>
            <td class="px-3 py-2 text-xs text-gray-500 hidden md:table-cell">
                ${adminFormatDate(u.last_login)}
            </td>
            <td class="px-3 py-2">
                <div class="flex gap-1 flex-wrap">
                    ${u.is_blocked 
                        ? `<button onclick="adminUnblockUser(${u.id})" class="px-2 py-1 text-xs bg-green-100 hover:bg-green-200 text-green-700 rounded">解封</button>`
                        : `<button onclick="adminBlockUser(${u.id})" class="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded">封鎖</button>`
                    }
                    <button onclick="adminKickUser(${u.id})" 
                        class="px-2 py-1 text-xs bg-yellow-100 hover:bg-yellow-200 text-yellow-700 rounded">踢出</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function adminChangePage(delta) {
    adminCurrentPage += delta;
    adminLoadUsers();
}

// ==================== 用戶操作 ====================
async function adminBlockUser(userId) {
    const reason = prompt('請輸入封鎖原因：');
    if (reason === null) return;
    
    try {
        const data = await adminApiRequest(`/api/admin/users/${userId}/block`, {
            method: 'POST',
            body: JSON.stringify({ reason: reason })
        });
        
        if (data && data.success) {
            showToast('用戶已封鎖', 'success');
            adminLoadUsers();
            adminLoadStats();
        } else {
            showToast('封鎖失敗', 'error');
        }
    } catch (e) {
        showToast('封鎖失敗：' + e.message, 'error');
    }
}

async function adminUnblockUser(userId) {
    if (!confirm('確定要解除封鎖此用戶？')) return;
    
    try {
        const data = await adminApiRequest(`/api/admin/users/${userId}/unblock`, {
            method: 'POST'
        });
        
        if (data && data.success) {
            showToast('已解除封鎖', 'success');
            adminLoadUsers();
            adminLoadStats();
        } else {
            showToast('解封失敗', 'error');
        }
    } catch (e) {
        showToast('解封失敗：' + e.message, 'error');
    }
}

async function adminKickUser(userId) {
    if (!confirm('確定要踢出此用戶？')) return;
    
    try {
        const data = await adminApiRequest(`/api/admin/users/${userId}/kick`, {
            method: 'POST'
        });
        
        if (data && data.success) {
            showToast('用戶已踢出', 'success');
        } else {
            showToast('踢出失敗', 'error');
        }
    } catch (e) {
        showToast('踢出失敗：' + e.message, 'error');
    }
}

async function adminKickAllUsers() {
    if (!confirm('確定要踢出所有用戶？這會讓所有人重新登入。')) return;
    
    try {
        const data = await adminApiRequest('/api/admin/users/kick-all', {
            method: 'POST'
        });
        
        if (data && data.success) {
            showToast('已踢出所有用戶', 'success');
        } else {
            showToast('操作失敗', 'error');
        }
    } catch (e) {
        showToast('操作失敗：' + e.message, 'error');
    }
}

// ==================== 系統管理 ====================
function adminShowSystemMessage(msg, isError = false) {
    const el = document.getElementById('adminSystemMessage');
    if (el) {
        el.textContent = msg;
        el.className = isError ? 'mt-3 text-sm text-red-500' : 'mt-3 text-sm text-green-600';
    }
}

async function adminInitializeData() {
    adminShowSystemMessage('正在初始化歷史資料...');
    
    try {
        const data = await adminApiRequest('/api/market/admin/initialize', { method: 'POST' });
        if (data && data.success) {
            adminShowSystemMessage(`✅ 初始化完成！${data.data?.count || 0} 筆資料`);
        } else {
            adminShowSystemMessage(`❌ 初始化失敗: ${data?.detail || '未知錯誤'}`, true);
        }
    } catch (e) {
        adminShowSystemMessage(`❌ 初始化失敗: ${e.message}`, true);
    }
}

async function adminUpdateIndices() {
    adminShowSystemMessage('正在更新三大指數...');
    
    try {
        const data = await adminApiRequest('/api/market/admin/update-indices', { method: 'POST' });
        if (data && data.success) {
            adminShowSystemMessage(`✅ 三大指數更新完成！${data.data?.count || 0} 筆資料`);
        } else {
            adminShowSystemMessage(`❌ 更新失敗: ${data?.detail || '未知錯誤'}`, true);
        }
    } catch (e) {
        adminShowSystemMessage(`❌ 更新失敗: ${e.message}`, true);
    }
}

async function adminUpdateSentiment() {
    adminShowSystemMessage('正在更新恐懼貪婪指數...');
    
    try {
        const data = await adminApiRequest('/api/market/admin/update-sentiment', { method: 'POST' });
        if (data && data.success) {
            adminShowSystemMessage(`✅ 恐懼貪婪指數更新完成！`);
        } else {
            adminShowSystemMessage(`❌ 更新失敗: ${data?.detail || '未知錯誤'}`, true);
        }
    } catch (e) {
        adminShowSystemMessage(`❌ 更新失敗: ${e.message}`, true);
    }
}

async function adminTriggerDailyUpdate() {
    adminShowSystemMessage('正在執行每日更新...');
    
    try {
        const data = await adminApiRequest('/api/market/admin/update', { method: 'POST' });
        if (data && data.success) {
            adminShowSystemMessage(`✅ 每日更新完成！`);
        } else {
            adminShowSystemMessage(`❌ 更新失敗: ${data?.detail || '未知錯誤'}`, true);
        }
    } catch (e) {
        adminShowSystemMessage(`❌ 更新失敗: ${e.message}`, true);
    }
}

// ==================== 訊號檢查 ====================
function adminShowSignalMessage(msg, isError = false) {
    const el = document.getElementById('adminSignalMessage');
    if (el) {
        el.textContent = msg;
        el.className = isError ? 'mt-3 text-sm text-red-500' : 'mt-3 text-sm text-green-600';
    }
}

async function adminRunSignalCheck() {
    adminShowSignalMessage('正在執行訊號檢查...');
    document.getElementById('adminSignalResult')?.classList.add('hidden');
    
    try {
        const data = await adminApiRequest('/api/admin/signal/detect', { method: 'POST' });
        if (data && data.success) {
            adminShowSignalMessage(`✅ 檢查完成：偵測到 ${data.total_signals} 個訊號`);
            
            if (data.signals_by_symbol && Object.keys(data.signals_by_symbol).length > 0) {
                document.getElementById('adminSignalResult')?.classList.remove('hidden');
                const contentEl = document.getElementById('adminSignalResultContent');
                if (contentEl) {
                    contentEl.textContent = JSON.stringify(data.signals_by_symbol, null, 2);
                }
            }
        } else {
            adminShowSignalMessage(`❌ 檢查失敗: ${data?.detail || '未知錯誤'}`, true);
        }
    } catch (e) {
        adminShowSignalMessage(`❌ 檢查失敗: ${e.message}`, true);
    }
}

async function adminSendSignalNotifications() {
    adminShowSignalMessage('正在發送訊號通知...');
    
    try {
        const data = await adminApiRequest('/api/admin/signal/notify', { method: 'POST' });
        if (data && data.success) {
            const r = data.result || {};
            adminShowSignalMessage(`✅ ${data.message} - 股票更新: ${r.stocks_updated}, 訊號偵測: ${r.signals_detected}, 通知發送: ${r.notifications_sent}`);
            
            if (r.errors && r.errors.length > 0) {
                document.getElementById('adminSignalResult')?.classList.remove('hidden');
                const contentEl = document.getElementById('adminSignalResultContent');
                if (contentEl) {
                    contentEl.textContent = '錯誤記錄:\n' + r.errors.join('\n');
                }
            }
        } else {
            adminShowSignalMessage(`❌ 發送失敗: ${data?.detail || '未知錯誤'}`, true);
        }
    } catch (e) {
        adminShowSignalMessage(`❌ 發送失敗: ${e.message}`, true);
    }
}

async function adminTestSignalDetection() {
    const symbol = document.getElementById('adminTestSymbolInput')?.value.trim();
    if (!symbol) {
        adminShowSignalMessage('請輸入股票代號', true);
        return;
    }
    
    adminShowSignalMessage(`正在測試 ${symbol.toUpperCase()} 的訊號偵測...`);
    document.getElementById('adminSignalResult')?.classList.add('hidden');
    
    try {
        const data = await adminApiRequest('/api/admin/signal/detect', { method: 'POST' });
        if (data && data.success) {
            const symbolUpper = symbol.toUpperCase();
            const symbolSignals = data.signals_by_symbol[symbolUpper] || [];
            
            adminShowSignalMessage(`✅ ${symbolUpper} 偵測到 ${symbolSignals.length} 個訊號`);
            
            document.getElementById('adminSignalResult')?.classList.remove('hidden');
            const contentEl = document.getElementById('adminSignalResultContent');
            if (contentEl) {
                contentEl.textContent = JSON.stringify({ symbol: symbolUpper, signals: symbolSignals }, null, 2);
            }
        } else {
            adminShowSignalMessage(`❌ 偵測失敗: ${data?.detail || '未知錯誤'}`, true);
        }
    } catch (e) {
        adminShowSignalMessage(`❌ 偵測失敗: ${e.message}`, true);
    }
}

async function adminTestLineNotify() {
    adminShowSignalMessage('正在發送測試訊息...');
    
    try {
        const data = await adminApiRequest('/api/admin/signal/test-push?message=管理員測試訊息', { method: 'POST' });
        if (data && data.success) {
            adminShowSignalMessage('✅ 測試訊息已發送，請檢查 LINE');
        } else {
            adminShowSignalMessage(`❌ 發送失敗: ${data?.message || data?.detail || '未知錯誤'}`, true);
        }
    } catch (e) {
        adminShowSignalMessage(`❌ 發送失敗: ${e.message}`, true);
    }
}

// ==================== 工具函數 ====================
function adminFormatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-TW', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function adminEscapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initAdmin, 100);
});
