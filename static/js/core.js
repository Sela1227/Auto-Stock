/**
 * SELA 核心模組 (P0 優化版)
 * 
 * 優化內容：
 * 1. DOM 快取 - 減少重複查詢
 * 2. 批量更新 - 減少瀏覽器重排
 * 3. 統一命名空間 - 減少全域污染
 * 
 * 向後兼容：保留所有 window.xxx 導出
 */

(function() {
    'use strict';
    
    // ============================================================
    // DOM 快取系統 (P0 核心優化)
    // ============================================================
    
    const _domCache = new Map();
    const _querySelectorCache = new Map();
    
    /**
     * 快取版 getElementById
     * 第一次查詢後快取，後續直接返回
     * @param {string} id - 元素 ID
     * @param {boolean} force - 強制重新查詢
     * @returns {HTMLElement|null}
     */
    function $(id, force = false) {
        if (!force && _domCache.has(id)) {
            return _domCache.get(id);
        }
        const el = document.getElementById(id);
        if (el) {
            _domCache.set(id, el);
        }
        return el;
    }
    
    /**
     * 快取版 querySelector
     * @param {string} selector - CSS 選擇器
     * @param {boolean} force - 強制重新查詢
     * @returns {HTMLElement|null}
     */
    function $q(selector, force = false) {
        if (!force && _querySelectorCache.has(selector)) {
            return _querySelectorCache.get(selector);
        }
        const el = document.querySelector(selector);
        if (el) {
            _querySelectorCache.set(selector, el);
        }
        return el;
    }
    
    /**
     * 清除 DOM 快取
     * 當 DOM 結構變化時調用（如動態載入內容後）
     */
    function clearDomCache() {
        _domCache.clear();
        _querySelectorCache.clear();
        console.log('🗑️ DOM 快取已清除');
    }
    
    /**
     * 預載入常用 DOM 元素到快取
     */
    function preloadDomCache() {
        const commonIds = [
            'loading-screen', 'app-content',
            'userName', 'userAvatar', 'sidebarUserName', 'sidebarAvatar',
            'sessionTimer', 'sidebarTimer',
            'mobileSidebar', 'sidebarOverlay',
            'toast', 'toastMessage', 'toastContainer',
            'searchSymbol', 'searchResult',
            'adminLink', 'adminSidebarLink', 'adminMobileLink'
        ];
        commonIds.forEach(id => $(id));
        console.log(`📦 已預載入 ${_domCache.size} 個 DOM 元素到快取`);
    }
    
    // ============================================================
    // 批量 DOM 更新 (P0 核心優化)
    // ============================================================
    
    /**
     * 批量更新多個元素
     * 使用 requestAnimationFrame 確保在同一幀內完成
     * @param {Array} updates - [{id: 'xxx', prop: 'textContent', value: 'xxx'}, ...]
     */
    function batchUpdate(updates) {
        requestAnimationFrame(() => {
            updates.forEach(({ id, prop, value, html, className, classList }) => {
                const el = $(id);
                if (!el) return;
                
                if (prop && value !== undefined) {
                    el[prop] = value;
                }
                if (html !== undefined) {
                    el.innerHTML = html;
                }
                if (className !== undefined) {
                    el.className = className;
                }
                if (classList) {
                    if (classList.add) el.classList.add(...classList.add);
                    if (classList.remove) el.classList.remove(...classList.remove);
                    if (classList.toggle) {
                        Object.entries(classList.toggle).forEach(([cls, force]) => {
                            el.classList.toggle(cls, force);
                        });
                    }
                }
            });
        });
    }
    
    /**
     * 安全設置 innerHTML（批量版）
     * 先構建完整 HTML 字串，再一次性更新
     * @param {string} id - 元素 ID
     * @param {string|Array} html - HTML 字串或字串陣列
     */
    function setHtml(id, html) {
        const el = $(id);
        if (!el) return;
        
        requestAnimationFrame(() => {
            el.innerHTML = Array.isArray(html) ? html.join('') : html;
        });
    }
    
    /**
     * 使用 DocumentFragment 批量添加子元素
     * 比多次 appendChild 效能好 10 倍
     * @param {string} containerId - 容器元素 ID
     * @param {Array} items - 要添加的項目
     * @param {Function} renderFn - 渲染函數 (item) => HTMLElement
     */
    function appendBatch(containerId, items, renderFn) {
        const container = $(containerId);
        if (!container) return;
        
        const fragment = document.createDocumentFragment();
        items.forEach(item => {
            const el = renderFn(item);
            if (el) fragment.appendChild(el);
        });
        
        requestAnimationFrame(() => {
            container.appendChild(fragment);
        });
    }
    
    // ============================================================
    // 全域變數
    // ============================================================
    
    const API_BASE = '';
    let token = localStorage.getItem('token');
    let currentUser = JSON.parse(localStorage.getItem('user') || 'null');
    let sessionTimer = null;
    let lastActivity = Date.now();
    
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
            
            // ✅ 使用快取版 DOM 查詢
            const timerEl = $('sessionTimer');
            const sidebarTimerEl = $('sidebarTimer');
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
            
            const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
            if (storedUser.id && storedUser.id !== serverUser.id) {
                console.error('用戶 ID 不一致!');
                clearAllUserData();
                window.location.href = '/static/index.html';
                return;
            }
            
            if (storedUser.line_user_id && storedUser.line_user_id !== serverUser.line_user_id) {
                console.error('LINE ID 不一致!');
                clearAllUserData();
                window.location.href = '/static/index.html';
                return;
            }
            
            currentUser = serverUser;
            
            localStorage.setItem('user', JSON.stringify({
                id: serverUser.id,
                display_name: serverUser.display_name,
                picture_url: serverUser.picture_url || '',
                line_user_id: serverUser.line_user_id,
                is_admin: serverUser.is_admin || false
            }));
            
            console.log('登入驗證成功: 用戶 ID =', serverUser.id);
            
            updateUserUI();
            
            // ✅ 使用快取版 DOM 查詢
            const loadingScreen = $('loading-screen');
            const appContent = $('app-content');
            if (loadingScreen) loadingScreen.style.display = 'none';
            if (appContent) appContent.style.display = 'block';
            
            startSessionMonitor();
            
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
        
        // ✅ 使用批量更新減少重排
        batchUpdate([
            { id: 'userName', prop: 'textContent', value: currentUser.display_name },
            { id: 'sidebarUserName', prop: 'textContent', value: currentUser.display_name },
        ]);
        
        // 頭像單獨處理（src 屬性）
        const avatarUrl = currentUser.picture_url || 'https://via.placeholder.com/40';
        const avatarEl = $('userAvatar');
        const sidebarAvatarEl = $('sidebarAvatar');
        if (avatarEl) avatarEl.src = avatarUrl;
        if (sidebarAvatarEl) sidebarAvatarEl.src = avatarUrl;
        
        // 管理員入口
        if (currentUser.is_admin) {
            const adminLink = $('adminLink');
            const adminSidebarLink = $('adminSidebarLink');
            const adminMobileLink = $('adminMobileLink');
            if (adminLink) adminLink.classList.remove('hidden');
            if (adminSidebarLink) adminSidebarLink.classList.remove('hidden');
            if (adminMobileLink) {
                adminMobileLink.classList.remove('hidden');
                adminMobileLink.classList.add('flex');
            }
            
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
        // ✅ 使用快取版 DOM 查詢
        const sidebar = $('mobileSidebar');
        const overlay = $('sidebarOverlay');
        if (sidebar) sidebar.classList.add('open');
        if (overlay) overlay.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
    
    function closeMobileSidebar() {
        const sidebar = $('mobileSidebar');
        const overlay = $('sidebarOverlay');
        if (sidebar) sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('open');
        document.body.style.overflow = '';
    }
    
    function mobileNavTo(section) {
        closeMobileSidebar();
        showSection(section);
        
        // ✅ 只查詢一次，不在迴圈中重複查詢
        document.querySelectorAll('.bottom-nav-item, .mobile-nav-link').forEach(el => {
            const isActive = el.dataset.section === section;
            el.classList.remove('active', 'bg-blue-50', 'text-gray-700');
            
            if (isActive) {
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
    // 頁面切換 (優化版)
    // ============================================================
    
    // 快取所有 section 元素
    let _sectionsCache = null;
    function getAllSections() {
        if (!_sectionsCache) {
            _sectionsCache = document.querySelectorAll('.section');
        }
        return _sectionsCache;
    }
    
    // 快取所有導航連結
    let _navLinksCache = null;
    function getAllNavLinks() {
        if (!_navLinksCache) {
            _navLinksCache = document.querySelectorAll('.nav-link');
        }
        return _navLinksCache;
    }
    
    // 快取所有底部導航
    let _bottomNavCache = null;
    function getAllBottomNav() {
        if (!_bottomNavCache) {
            _bottomNavCache = document.querySelectorAll('.bottom-nav-item');
        }
        return _bottomNavCache;
    }
    
    function showSection(name, evt) {
        // ✅ 使用快取的 section 列表
        getAllSections().forEach(s => s.classList.add('hidden'));
        
        const section = $(`section-${name}`);
        if (section) {
            section.classList.remove('hidden');
        }
        
        // ✅ 使用快取的導航連結
        getAllNavLinks().forEach(l => {
            const isActive = l.dataset.section === name;
            l.classList.toggle('bg-blue-50', isActive);
            l.classList.toggle('text-gray-700', isActive);
            l.classList.toggle('text-gray-600', !isActive);
        });
        
        if (evt && evt.target) {
            const navLink = evt.target.closest('.nav-link');
            if (navLink) {
                navLink.classList.add('bg-blue-50', 'text-gray-700');
                navLink.classList.remove('text-gray-600');
            }
        }
        
        // ✅ 使用快取的底部導航
        getAllBottomNav().forEach(el => {
            el.classList.toggle('active', el.dataset.section === name);
        });

        // 載入對應資料
        if (name === 'watchlist' && typeof loadWatchlist === 'function') loadWatchlist();
        if (name === 'sentiment' && typeof loadSentimentDetail === 'function') loadSentimentDetail();
        if (name === 'settings' && typeof loadSettings === 'function') loadSettings();
        if (name === 'portfolio' && typeof loadPortfolio === 'function') loadPortfolio();
        if (name === 'subscription' && typeof loadSubscriptionData === 'function') loadSubscriptionData();
        if (name === 'cagr' && typeof initCagr === 'function') initCagr();
        
        if (name === 'admin') {
            if (typeof adminLoadStats === 'function') adminLoadStats();
            if (typeof adminLoadUsers === 'function') adminLoadUsers();
        }
    }
    
    // ============================================================
    // Toast 提示 (優化版)
    // ============================================================
    
    function showToast(message, type = 'info', duration = 3000) {
        // ✅ 使用快取版 DOM 查詢
        const container = $('toastContainer');
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
        
        const toastEl = $('toast');
        const toastMsg = $('toastMessage');
        if (toastEl && toastMsg) {
            toastMsg.textContent = message;
            toastEl.classList.remove('hidden');
            setTimeout(() => toastEl.classList.add('hidden'), duration);
        }
    }
    
    // ============================================================
    // 工具函數
    // ============================================================
    
    /**
     * 摺疊面板切換
     */
    function toggleCollapsible(button) {
        const content = button.nextElementSibling;
        const icon = button.querySelector('i');
        
        if (content.style.maxHeight) {
            content.style.maxHeight = null;
            if (icon) icon.style.transform = '';
        } else {
            content.style.maxHeight = content.scrollHeight + 'px';
            if (icon) icon.style.transform = 'rotate(180deg)';
        }
    }
    
    // ============================================================
    // 初始化
    // ============================================================
    
    function init() {
        console.log('🚀 SELA 系統初始化中... (P0 優化版)');
        console.log('Device info:', deviceInfo);
        
        // ✅ 預載入常用 DOM 元素
        preloadDomCache();
        
        checkAuth();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // ============================================================
    // SELA 命名空間 (P0 新增)
    // ============================================================
    
    window.SELA = {
        // DOM 工具
        $,
        $q,
        clearDomCache,
        preloadDomCache,
        
        // 批量更新
        batchUpdate,
        setHtml,
        appendBatch,
        
        // 狀態
        getCurrentUser,
        getToken,
        deviceInfo,
        
        // API
        apiRequest,
        
        // UI
        showSection,
        showToast,
        
        // 版本
        version: '0.8.2-p0'
    };
    
    // ============================================================
    // 向後兼容：導出到全域
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
    window.toggleCollapsible = toggleCollapsible;
    
    // 兼容舊代碼
    window.token = token;
    window.currentUser = currentUser;
    
    // ✅ 新增：導出 DOM 快取工具供其他模組使用
    window.$ = $;
    window.$q = $q;
    window.clearDomCache = clearDomCache;
    window.batchUpdate = batchUpdate;
    window.setHtml = setHtml;
    
    console.log('🎯 core.js 核心模組已載入 (P0 優化版)');
})();
