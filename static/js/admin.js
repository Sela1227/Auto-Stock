// ============================================================
// ç®¡ç†å¾Œå° - admin.js
// ============================================================

let adminCurrentPage = 1;
let adminTotalPages = 1;

// ==================== åˆå§‹åŒ– ====================
function initAdmin() {
    // åªæœ‰ç®¡ç†å“¡æ‰åˆå§‹åŒ–
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.is_admin) {
        // é¡¯ç¤ºç®¡ç†å“¡å…¥å£
        const adminMobileLink = document.getElementById('adminMobileLink');
        if (adminMobileLink) {
            adminMobileLink.classList.remove('hidden');
            adminMobileLink.classList.add('flex');
        }
    }
}

// ==================== API è«‹æ±‚å°è£ (è¿”å›ž JSON) ====================
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
            showToast('æ‚¨æ²’æœ‰ç®¡ç†å“¡æ¬Šé™', 'error');
            showSection('dashboard');
            return null;
        }
        
        return await response.json();
    } catch (e) {
        console.error('Admin API è«‹æ±‚å¤±æ•—:', e);
        return null;
    }
}

// ==================== è¼‰å…¥çµ±è¨ˆ ====================
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
        console.error('è¼‰å…¥çµ±è¨ˆå¤±æ•—', e);
    }
}

// ==================== ç”¨æˆ¶ç®¡ç† ====================
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
            const pageInfo = document.getElementById('adminPageInfo');
            if (pageInfo) {
                pageInfo.textContent = `ç¬¬ ${data.pagination.page} / ${adminTotalPages} é ï¼Œå…± ${data.pagination.total} ç­†`;
            }
            const prevBtn = document.getElementById('adminPrevPage');
            const nextBtn = document.getElementById('adminNextPage');
            if (prevBtn) prevBtn.disabled = adminCurrentPage <= 1;
            if (nextBtn) nextBtn.disabled = adminCurrentPage >= adminTotalPages;
        }
    } catch (e) {
        showToast('è¼‰å…¥ç”¨æˆ¶å¤±æ•—', 'error');
    }
}

function adminRenderUsers(users) {
    const tbody = document.getElementById('adminUserList');
    
    if (!users || users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-gray-400">æ²’æœ‰æ‰¾åˆ°ç”¨æˆ¶</td></tr>';
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
                        <div class="font-medium text-gray-900 text-sm">${adminEscapeHtml(u.display_name || 'æœªå‘½å')}</div>
                        <div class="text-xs text-gray-400">ID: ${u.id}</div>
                    </div>
                </div>
            </td>
            <td class="px-3 py-2 text-sm text-gray-500 hidden md:table-cell">
                ${adminEscapeHtml(u.email || '-')}
            </td>
            <td class="px-3 py-2">
                <div class="flex flex-wrap gap-1">
                    ${u.is_admin ? '<span class="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">ç®¡ç†å“¡</span>' : ''}
                    ${u.is_blocked 
                        ? '<span class="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-800">å·²å°éŽ–</span>' 
                        : '<span class="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-800">æ­£å¸¸</span>'}
                </div>
            </td>
            <td class="px-3 py-2 text-center">
                <span class="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700">${u.login_count || 0}</span>
            </td>
            <td class="px-3 py-2">
                <div class="flex gap-1 flex-wrap">
                    ${u.is_blocked 
                        ? `<button onclick="adminUnblockUser(${u.id})" class="px-2 py-1 text-xs bg-green-100 hover:bg-green-200 text-green-700 rounded">è§£å°</button>`
                        : `<button onclick="adminBlockUser(${u.id})" class="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded">å°éŽ–</button>`
                    }
                    <button onclick="adminKickUser(${u.id})" 
                        class="px-2 py-1 text-xs bg-yellow-100 hover:bg-yellow-200 text-yellow-700 rounded">è¸¢å‡º</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function adminChangePage(delta) {
    adminCurrentPage += delta;
    adminLoadUsers();
}

// ==================== ç”¨æˆ¶æ“ä½œ ====================
async function adminBlockUser(userId) {
    const reason = prompt('è«‹è¼¸å…¥å°éŽ–åŽŸå› ï¼š');
    if (reason === null) return;
    
    try {
        const data = await adminApiRequest(`/api/admin/users/${userId}/block`, {
            method: 'POST',
            body: JSON.stringify({ reason: reason })
        });
        
        if (data && data.success) {
            showToast('ç”¨æˆ¶å·²å°éŽ–', 'success');
            adminLoadUsers();
            adminLoadStats();
        } else {
            showToast('å°éŽ–å¤±æ•—', 'error');
        }
    } catch (e) {
        showToast('å°éŽ–å¤±æ•—ï¼š' + e.message, 'error');
    }
}

async function adminUnblockUser(userId) {
    if (!confirm('ç¢ºå®šè¦è§£é™¤å°éŽ–æ­¤ç”¨æˆ¶ï¼Ÿ')) return;
    
    try {
        const data = await adminApiRequest(`/api/admin/users/${userId}/unblock`, {
            method: 'POST'
        });
        
        if (data && data.success) {
            showToast('å·²è§£é™¤å°éŽ–', 'success');
            adminLoadUsers();
            adminLoadStats();
        } else {
            showToast('è§£å°å¤±æ•—', 'error');
        }
    } catch (e) {
        showToast('è§£å°å¤±æ•—ï¼š' + e.message, 'error');
    }
}

async function adminKickUser(userId) {
    if (!confirm('ç¢ºå®šè¦è¸¢å‡ºæ­¤ç”¨æˆ¶ï¼Ÿ')) return;
    
    try {
        const data = await adminApiRequest(`/api/admin/users/${userId}/kick`, {
            method: 'POST'
        });
        
        if (data && data.success) {
            showToast('ç”¨æˆ¶å·²è¸¢å‡º', 'success');
        } else {
            showToast('æ“ä½œå¤±æ•—', 'error');
        }
    } catch (e) {
        showToast('æ“ä½œå¤±æ•—ï¼š' + e.message, 'error');
    }
}

async function adminKickAllUsers() {
    if (!confirm('ç¢ºå®šè¦è¸¢å‡ºæ‰€æœ‰ç”¨æˆ¶ï¼Ÿæ­¤æ“ä½œå°‡ä½¿æ‰€æœ‰ç”¨æˆ¶é‡æ–°ç™»å…¥ã€‚')) return;
    
    try {
        const data = await adminApiRequest('/api/admin/users/kick-all', {
            method: 'POST'
        });
        
        if (data && data.success) {
            showToast(`å·²è¸¢å‡º ${data.kicked_count} å€‹ç”¨æˆ¶`, 'success');
        } else {
            showToast('æ“ä½œå¤±æ•—', 'error');
        }
    } catch (e) {
        showToast('æ“ä½œå¤±æ•—ï¼š' + e.message, 'error');
    }
}

// ==================== ç³»çµ±ç®¡ç† ====================
function adminShowSystemMessage(msg, isError = false) {
    const el = document.getElementById('adminSystemMessage');
    if (el) {
        el.textContent = msg;
        el.className = isError ? 'mt-3 text-sm text-red-500' : 'mt-3 text-sm text-green-600';
    }
}

async function adminInitializeData() {
    adminShowSystemMessage('æ­£åœ¨åˆå§‹åŒ–æ­·å²è³‡æ–™...');
    
    try {
        const data = await adminApiRequest('/api/market/admin/initialize', { method: 'POST' });
        if (data && data.success) {
            adminShowSystemMessage(`âœ… åˆå§‹åŒ–å®Œæˆï¼${data.data?.count || 0} ç­†è³‡æ–™`);
        } else {
            adminShowSystemMessage(`âŒ åˆå§‹åŒ–å¤±æ•—: ${data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSystemMessage(`âŒ åˆå§‹åŒ–å¤±æ•—: ${e.message}`, true);
    }
}

async function adminUpdateIndices() {
    adminShowSystemMessage('æ­£åœ¨æ›´æ–°ä¸‰å¤§æŒ‡æ•¸...');
    
    try {
        const data = await adminApiRequest('/api/market/admin/update-indices', { method: 'POST' });
        if (data && data.success) {
            adminShowSystemMessage(`âœ… ä¸‰å¤§æŒ‡æ•¸æ›´æ–°å®Œæˆï¼${data.data?.count || 0} ç­†è³‡æ–™`);
        } else {
            adminShowSystemMessage(`âŒ æ›´æ–°å¤±æ•—: ${data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSystemMessage(`âŒ æ›´æ–°å¤±æ•—: ${e.message}`, true);
    }
}

async function adminUpdateSentiment() {
    adminShowSystemMessage('æ­£åœ¨æ›´æ–°ææ‡¼è²ªå©ªæŒ‡æ•¸...');
    
    try {
        const data = await adminApiRequest('/api/market/admin/update-sentiment', { method: 'POST' });
        if (data && data.success) {
            adminShowSystemMessage(`âœ… ææ‡¼è²ªå©ªæŒ‡æ•¸æ›´æ–°å®Œæˆï¼`);
        } else {
            adminShowSystemMessage(`âŒ æ›´æ–°å¤±æ•—: ${data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSystemMessage(`âŒ æ›´æ–°å¤±æ•—: ${e.message}`, true);
    }
}

async function adminTriggerDailyUpdate() {
    adminShowSystemMessage('æ­£åœ¨åŸ·è¡Œæ¯æ—¥æ›´æ–°...');
    
    try {
        const data = await adminApiRequest('/api/market/admin/update', { method: 'POST' });
        if (data && data.success) {
            adminShowSystemMessage(`âœ… æ¯æ—¥æ›´æ–°å®Œæˆï¼`);
        } else {
            adminShowSystemMessage(`âŒ æ›´æ–°å¤±æ•—: ${data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSystemMessage(`âŒ æ›´æ–°å¤±æ•—: ${e.message}`, true);
    }
}

// ==================== è¨Šè™Ÿæª¢æŸ¥ ====================
function adminShowSignalMessage(msg, isError = false) {
    const el = document.getElementById('adminSignalMessage');
    if (el) {
        el.textContent = msg;
        el.className = isError ? 'mt-3 text-sm text-red-500' : 'mt-3 text-sm text-green-600';
    }
}

async function adminRunSignalCheck() {
    adminShowSignalMessage('æ­£åœ¨åŸ·è¡Œè¨Šè™Ÿæª¢æŸ¥...');
    document.getElementById('adminSignalResult')?.classList.add('hidden');
    
    try {
        const data = await adminApiRequest('/api/admin/signal/detect', { method: 'POST' });
        if (data && data.success) {
            adminShowSignalMessage(`âœ… æª¢æŸ¥å®Œæˆï¼šåµæ¸¬åˆ° ${data.total_signals} å€‹è¨Šè™Ÿ`);
            
            if (data.signals_by_symbol && Object.keys(data.signals_by_symbol).length > 0) {
                document.getElementById('adminSignalResult')?.classList.remove('hidden');
                const contentEl = document.getElementById('adminSignalResultContent');
                if (contentEl) {
                    contentEl.textContent = JSON.stringify(data.signals_by_symbol, null, 2);
                }
            }
        } else {
            adminShowSignalMessage(`âŒ æª¢æŸ¥å¤±æ•—: ${data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSignalMessage(`âŒ æª¢æŸ¥å¤±æ•—: ${e.message}`, true);
    }
}

async function adminSendSignalNotifications() {
    adminShowSignalMessage('æ­£åœ¨ç™¼é€è¨Šè™Ÿé€šçŸ¥...');
    
    try {
        const data = await adminApiRequest('/api/admin/signal/notify', { method: 'POST' });
        if (data && data.success) {
            const r = data.result || {};
            adminShowSignalMessage(`âœ… ${data.message} - è‚¡ç¥¨æ›´æ–°: ${r.stocks_updated}, è¨Šè™Ÿåµæ¸¬: ${r.signals_detected}, é€šçŸ¥ç™¼é€: ${r.notifications_sent}`);
            
            if (r.errors && r.errors.length > 0) {
                document.getElementById('adminSignalResult')?.classList.remove('hidden');
                const contentEl = document.getElementById('adminSignalResultContent');
                if (contentEl) {
                    contentEl.textContent = 'éŒ¯èª¤è¨˜éŒ„:\n' + r.errors.join('\n');
                }
            }
        } else {
            adminShowSignalMessage(`âŒ ç™¼é€å¤±æ•—: ${data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSignalMessage(`âŒ ç™¼é€å¤±æ•—: ${e.message}`, true);
    }
}

async function adminTestSignalDetection() {
    const symbol = document.getElementById('adminTestSymbolInput')?.value.trim();
    if (!symbol) {
        adminShowSignalMessage('è«‹è¼¸å…¥è‚¡ç¥¨ä»£è™Ÿ', true);
        return;
    }
    
    adminShowSignalMessage(`æ­£åœ¨æ¸¬è©¦ ${symbol.toUpperCase()} çš„è¨Šè™Ÿåµæ¸¬...`);
    document.getElementById('adminSignalResult')?.classList.add('hidden');
    
    try {
        const data = await adminApiRequest('/api/admin/signal/detect', { method: 'POST' });
        if (data && data.success) {
            const symbolUpper = symbol.toUpperCase();
            const symbolSignals = data.signals_by_symbol[symbolUpper] || [];
            
            adminShowSignalMessage(`âœ… ${symbolUpper} åµæ¸¬åˆ° ${symbolSignals.length} å€‹è¨Šè™Ÿ`);
            
            document.getElementById('adminSignalResult')?.classList.remove('hidden');
            const contentEl = document.getElementById('adminSignalResultContent');
            if (contentEl) {
                contentEl.textContent = JSON.stringify({ symbol: symbolUpper, signals: symbolSignals }, null, 2);
            }
        } else {
            adminShowSignalMessage(`âŒ åµæ¸¬å¤±æ•—: ${data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSignalMessage(`âŒ åµæ¸¬å¤±æ•—: ${e.message}`, true);
    }
}

async function adminTestLineNotify() {
    adminShowSignalMessage('æ­£åœ¨ç™¼é€æ¸¬è©¦è¨Šæ¯...');
    
    try {
        const data = await adminApiRequest('/api/admin/signal/test-push?message=ç®¡ç†å“¡æ¸¬è©¦è¨Šæ¯', { method: 'POST' });
        if (data && data.success) {
            adminShowSignalMessage('âœ… æ¸¬è©¦è¨Šæ¯å·²ç™¼é€ï¼Œè«‹æª¢æŸ¥ LINE');
        } else {
            adminShowSignalMessage(`âŒ ç™¼é€å¤±æ•—: ${data?.message || data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSignalMessage(`âŒ ç™¼é€å¤±æ•—: ${e.message}`, true);
    }
}

// ==================== è¨‚é–±æºç®¡ç† ====================
function adminShowSubscriptionMessage(msg, isError = false) {
    const el = document.getElementById('adminSubscriptionMessage');
    if (el) {
        el.textContent = msg;
        el.className = isError ? 'mt-3 text-sm text-red-500' : 'mt-3 text-sm text-green-600';
    }
}

async function adminFetchSubscriptions() {
    adminShowSubscriptionMessage('æ­£åœ¨æŠ“å–è¨‚é–±ç²¾é¸...');
    
    try {
        const data = await adminApiRequest('/api/subscription/admin/fetch', { method: 'POST' });
        if (data && data.success) {
            adminShowSubscriptionMessage(`âœ… æŠ“å–å®Œæˆï¼æ–°å¢ž ${data.new_articles || 0} ç¯‡æ–‡ç« ï¼Œ${data.new_mentions || 0} å€‹æåŠ`);
        } else {
            adminShowSubscriptionMessage(`âŒ æŠ“å–å¤±æ•—: ${data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSubscriptionMessage(`âŒ æŠ“å–å¤±æ•—: ${e.message}`, true);
    }
}

async function adminBackfillSubscriptions() {
    const days = prompt('å›žè£œå¹¾å¤©çš„æ–‡ç« ï¼Ÿ', '7');
    if (!days) return;
    
    adminShowSubscriptionMessage('æ­£åœ¨å›žè£œæ­·å²æ–‡ç« ...');
    
    try {
        const data = await adminApiRequest(`/api/subscription/admin/backfill?days=${days}`, { method: 'POST' });
        if (data && data.success) {
            adminShowSubscriptionMessage(`âœ… å›žè£œå®Œæˆï¼æ–°å¢ž ${data.new_articles || 0} ç¯‡æ–‡ç« ï¼Œ${data.new_mentions || 0} å€‹æåŠ`);
        } else {
            adminShowSubscriptionMessage(`âŒ å›žè£œå¤±æ•—: ${data?.detail || 'æœªçŸ¥éŒ¯èª¤'}`, true);
        }
    } catch (e) {
        adminShowSubscriptionMessage(`âŒ å›žè£œå¤±æ•—: ${e.message}`, true);
    }
}

// ==================== å·¥å…·å‡½æ•¸ ====================
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

// é é¢è¼‰å…¥æ™‚åˆå§‹åŒ–
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initAdmin, 100);
});