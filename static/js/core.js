/**
 * 核心模組
 * 包含：認證、API 請求、頁面切換、初始化
 */

(function() {
    'use strict';
    
    // ============================================================
    // 全域變數
    // ============================================================
    
    const API_BASE = '';  // 同域名
    let token = localStorage.getItem('token');
    let currentUser = JSON.parse(localStorage.getItem('user') || 'null');
    let sessionTimer = null;
    let lastActivity = Date.now();
    
    // 設備資訊
    const deviceInfo = {
        isMobile: window.innerWidth < 768,
        isTouch: 'ontouchstart' in window,
        isLineApp: /Line\//i.test(navigator.userAgent),
        isIOS: /iPhone|iPad/i.test(navigator.userAgent),
        isAndroid: /Android/i.test(navigator.userAgent),
    };
    
    // ============================================================
    // API 請求封裝
    // ============================================================
    
    async function apiRequest(endpoint, options = {}) {
        if (!token) {
            console.error('API 請求失敗: 無 token');
            clearAllUserData();
            window.location.href = '/static/index.html';
            throw new Error('未登入');
        }
        
        const headers = {
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };
        
        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }
        
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers
            });
            
            if (res.status === 401) {
                console.error('Token 無效，重新登入');
                clearAllUserData();
                window.location.href = '/static/index.html';
                throw new Error('Token 無效');
            }
            
            return res;
        } catch (e) {
            console.error(`API 請求失敗 ${endpoint}:`, e);
            throw e;
        }
    }
    
    // ============================================================
    // 自動登出功能
    // ============================================================
    
    function getSessionTimeout() {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const isAdmin = user.is_admin === true;
        return isAdmin ? 60 * 60 * 1000 : 10 * 60 * 1000;
    }
    
    function resetSessionTimer() {
        lastActivity = Date.now();
    }
    
    function checkSessionTimeout() {
        const SESSION_TIMEOUT = getSessionTimeout();
        const elapsed = Date.now() - lastActivity;
        const remaining = SESSION_TIMEOUT - elapsed;
        
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const isAdmin = user.is_admin === true;
        const timeoutMinutes = isAdmin ? 60 : 10;
        
        if (remaining <= 0) {
            showToast(`閒置超過 ${timeoutMinutes} 分鐘，已自動登出`);
            setTimeout(() => logout(), 1500);
        } else {
            const mins = Math.floor(remaining / 60000);
            const secs = Math.floor((remaining % 60000) / 1000);
            const timeStr = `${mins}:${secs.toString().padStart(2, '0')}`;
            
            const timerEl = document.getElementById('sessionTimer');
            const sidebarTimerEl = document.getElementById('sidebarTimer');
            if (timerEl) timerEl.textContent = `閒置登出: ${timeStr}`;
            if (sidebarTimerEl) sidebarTimerEl.textContent = timeStr;
        }
    }
    
    function startSessionMonitor() {
        ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click'].forEach(event => {
            document.addEventListener(event, resetSessionTimer, { passive: true });
        });
        sessionTimer = setInterval(checkSessionTimeout, 1000);
    }
    
    function stopSessionMonitor() {
        if (sessionTimer) {
            clearInterval(sessionTimer);
            sessionTimer = null;
        }
    }
    
    // ============================================================
    // 登入驗證
    // ============================================================
    
    async function checkAuth() {
        if (!token) {
            console.log('無 token，跳轉登入頁');
            clearAllUserData();
            window.location.href = '/static/index.html';
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/auth/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!res.ok) {
                console.error('Token 驗證失敗，狀態碼:', res.status);
                throw new Error('Unauthorized');
            }
            
            const serverUser = await res.json();
            
            // 驗證本地用戶與伺服器用戶一致
            const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
            if (storedUser.id && storedUser.id !== serverUser.id) {
                console.error('用戶 ID 不一致! 本地:', storedUser.id, '伺服器:', serverUser.id);
                clearAllUserData();
                window.location.href = '/static/index.html';
                return;
            }
            
            if (storedUser.line_user_id && storedUser.line_user_id !== serverUser.line_user_id) {
                console.error('LINE ID 不一致! 本地:', storedUser.line_user_id, '伺服器:', serverUser.line_user_id);
                clearAllUserData();
                window.location.href = '/static/index.html';
                return;
            }
            
            currentUser = serverUser;
            
            // 更新本地存儲
            localStorage.setItem('user', JSON.stringify({
                id: serverUser.id,
                display_name: serverUser.display_name,
                picture_url: serverUser.picture_url || '',
                line_user_id: serverUser.line_user_id,
                is_admin: serverUser.is_admin || false
            }));
            
            console.log('登入驗證成功: 用戶 ID =', serverUser.id, ', LINE ID =', serverUser.line_user_id);
            
            // 更新 UI
            updateUserUI();
            
            // 顯示主內容
            document.getElementById('loading-screen').style.display = 'none';
            document.getElementById('app-content').style.display = 'block';
            
            startSessionMonitor();
            
            // 載入儀表板
            if (typeof loadDashboard === 'function') {
                loadDashboard();
            }
            
        } catch (e) {
            console.error('驗證失敗:', e);
            clearAllUserData();
            window.location.href = '/static/index.html';
        }
    }
    
    function updateUserUI() {
        if (!currentUser) return;
        
        const nameEl = document.getElementById('userName');
        const avatarEl = document.getElementById('userAvatar');
        const sidebarNameEl = document.getElementById('sidebarUserName');
        const sidebarAvatarEl = document.getElementById('sidebarAvatar');
        
        if (nameEl) nameEl.textContent = currentUser.display_name;
        if (avatarEl) avatarEl.src = currentUser.picture_url || 'https://via.placeholder.com/40';
        if (sidebarNameEl) sidebarNameEl.textContent = currentUser.display_name;
        if (sidebarAvatarEl) sidebarAvatarEl.src = currentUser.picture_url || 'https://via.placeholder.com/40';
        
        // 管理員入口
        if (currentUser.is_admin) {
            const adminLink = document.getElementById('adminLink');
            const adminSidebarLink = document.getElementById('adminSidebarLink');
            const adminMobileLink = document.getElementById('adminMobileLink');
            if (adminLink) adminLink.classList.remove('hidden');
            if (adminSidebarLink) adminSidebarLink.classList.remove('hidden');
            if (adminMobileLink) {
                adminMobileLink.classList.remove('hidden');
                adminMobileLink.classList.add('flex');
            }
            
            // 觸發管理員更新
            if (typeof triggerAdminUpdates === 'function') {
                triggerAdminUpdates();
            }
        }
    }
    
    function clearAllUserData() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('login_time');
        sessionStorage.clear();
        currentUser = null;
        token = null;
    }

    function logout() {
        stopSessionMonitor();
        clearAllUserData();
        window.location.href = '/static/index.html';
    }
    
    function getCurrentUser() {
        return currentUser;
    }
    
    function getToken() {
        return token;
    }
    
    // ============================================================
    // 手機版選單
    // ============================================================
    
    function openMobileSidebar() {
        document.getElementById('mobileSidebar').classList.add('open');
        document.getElementById('sidebarOverlay').classList.add('open');
        document.body.style.overflow = 'hidden';
    }
    
    function closeMobileSidebar() {
        document.getElementById('mobileSidebar').classList.remove('open');
        document.getElementById('sidebarOverlay').classList.remove('open');
        document.body.style.overflow = '';
    }
    
    function mobileNavTo(section) {
        closeMobileSidebar();
        showSection(section);
        
        // 更新底部導航和側邊選單高亮
        document.querySelectorAll('.bottom-nav-item, .mobile-nav-link').forEach(el => {
            el.classList.remove('active', 'bg-blue-50', 'text-gray-700');
            if (el.dataset.section === section) {
                el.classList.add('active');
                if (el.classList.contains('mobile-nav-link')) {
                    el.classList.add('bg-blue-50', 'text-gray-700');
                }
            } else if (el.classList.contains('mobile-nav-link')) {
                el.classList.add('text-gray-600');
            }
        });
    }
    
    // ============================================================
    // 頁面切換
    // ============================================================
    
    function showSection(name, evt) {
        document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
        const section = document.getElementById(`section-${name}`);
        if (section) {
            section.classList.remove('hidden');
        }
        
        // 更新電腦版導航高亮
        document.querySelectorAll('.nav-link').forEach(l => {
            l.classList.remove('bg-blue-50', 'text-gray-700');
            l.classList.add('text-gray-600');
            if (l.dataset.section === name) {
                l.classList.add('bg-blue-50', 'text-gray-700');
                l.classList.remove('text-gray-600');
            }
        });
        
        if (evt && evt.target) {
            const navLink = evt.target.closest('.nav-link');
            if (navLink) {
                navLink.classList.add('bg-blue-50', 'text-gray-700');
                navLink.classList.remove('text-gray-600');
            }
        }
        
        // 更新底部導航高亮
        document.querySelectorAll('.bottom-nav-item').forEach(el => {
            el.classList.remove('active');
            if (el.dataset.section === name) {
                el.classList.add('active');
            }
        });

        // 載入對應資料
        if (name === 'watchlist' && typeof loadWatchlist === 'function') loadWatchlist();
        if (name === 'sentiment' && typeof loadSentimentDetail === 'function') loadSentimentDetail();
        if (name === 'settings' && typeof loadSettings === 'function') loadSettings();
        if (name === 'portfolio' && typeof loadPortfolio === 'function') loadPortfolio();
        if (name === 'subscription' && typeof loadSubscriptionData === 'function') loadSubscriptionData();
        
        // 🆕 報酬率比較
        if (name === 'cagr' && typeof initCagr === 'function') initCagr();
        
        // 🆕 管理後台
        if (name === 'admin') {
            if (typeof adminLoadStats === 'function') adminLoadStats();
            if (typeof adminLoadUsers === 'function') adminLoadUsers();
        }
    }
    
    // ============================================================
    // Toast 提示
    // ============================================================
    
    function showToast(message, type = 'info', duration = 3000) {
        // 嘗試使用 toastContainer (如果存在)
        const container = document.getElementById('toastContainer');
        if (container) {
            const toast = document.createElement('div');
            toast.className = 'toast bg-gray-800 text-white px-4 py-3 rounded-lg shadow-lg mb-2 transform transition-all duration-300 translate-y-full opacity-0';
            toast.textContent = message;
            container.appendChild(toast);
            
            requestAnimationFrame(() => {
                toast.classList.remove('translate-y-full', 'opacity-0');
            });
            
            setTimeout(() => {
                toast.classList.add('translate-y-full', 'opacity-0');
                setTimeout(() => toast.remove(), 300);
            }, duration);
            return;
        }
        
        // 備用：使用簡單的 toast 元素
        const toastEl = document.getElementById('toast');
        const toastMsg = document.getElementById('toastMessage');
        if (toastEl && toastMsg) {
            toastMsg.textContent = message;
            toastEl.classList.remove('hidden');
            setTimeout(() => toastEl.classList.add('hidden'), duration);
        }
    }
    
    // ============================================================
    // 初始化
    // ============================================================
    
    function init() {
        console.log('🚀 SELA 系統初始化中...');
        console.log('Device info:', deviceInfo);
        
        // 檢查登入狀態
        checkAuth();
    }
    
    // DOM 載入完成後初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // ============================================================
    // 導出到全域
    // ============================================================
    
    window.API_BASE = API_BASE;
    window.apiRequest = apiRequest;
    window.getCurrentUser = getCurrentUser;
    window.getToken = getToken;
    window.checkAuth = checkAuth;
    window.logout = logout;
    window.clearAllUserData = clearAllUserData;
    window.showSection = showSection;
    window.openMobileSidebar = openMobileSidebar;
    window.closeMobileSidebar = closeMobileSidebar;
    window.mobileNavTo = mobileNavTo;
    window.showToast = showToast;
    window.deviceInfo = deviceInfo;
    
    // 兼容舊代碼
    window.token = token;
    window.currentUser = currentUser;
    
    console.log('🎯 core.js 核心模組已載入');
})();
