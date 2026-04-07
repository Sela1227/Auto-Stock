/**
 * ä½ˆå±€å…ƒä»¶å‹•æ…‹ç”Ÿæˆæ¨¡çµ„
 * ç”Ÿæˆå´é‚Šæ¬„ã€åº•éƒ¨å°Žèˆªç­‰é‡è¤‡ä½¿ç”¨çš„ UI å…ƒä»¶
 */

(function() {
    'use strict';

    // ============================================================
    // å°Žèˆªé …ç›®é…ç½®
    // ============================================================

    const NAV_ITEMS = [
        { id: 'dashboard', icon: 'fa-tachometer-alt', label: 'å„€è¡¨æ¿', mobileLabel: 'é¦–é ' },
        { id: 'search', icon: 'fa-search', label: 'è‚¡ç¥¨æŸ¥è©¢', mobileLabel: 'æŸ¥è©¢' },
        { id: 'watchlist', icon: 'fa-star', label: 'è¿½è¹¤æ¸…å–®', mobileLabel: 'è¿½è¹¤' },
        { id: 'sentiment', icon: 'fa-heart-pulse', label: 'ææ‡¼è²ªå©ª', mobileLabel: 'æƒ…ç·’' },
        { id: 'compare', icon: 'fa-chart-line', label: 'èµ°å‹¢æ¯”è¼ƒ' },
        { id: 'portfolio', icon: 'fa-wallet', label: 'å€‹äººæŠ•è³‡è¨˜éŒ„' },
        { id: 'subscription', icon: 'fa-satellite-dish', label: 'è¨‚é–±ç²¾é¸' },
        { id: 'cagr', icon: 'fa-trophy', label: 'å ±é…¬çŽ‡æ¯”è¼ƒ' },
        { id: 'settings', icon: 'fa-cog', label: 'è¨­å®š', mobileLabel: 'è¨­å®š', showInBottomNav: true }
    ];

    // åº•éƒ¨å°Žèˆªé¡¯ç¤ºçš„é …ç›®
    const BOTTOM_NAV_ITEMS = ['dashboard', 'search', 'watchlist', 'sentiment', 'settings'];

    // ============================================================
    // æ‰‹æ©Ÿç‰ˆå´é‚Šé¸å–®
    // ============================================================

    function renderMobileSidebar() {
        const sidebar = document.getElementById('mobileSidebar');
        if (!sidebar) return;

        const navItems = NAV_ITEMS.map(item => `
            <a href="#" onclick="mobileNavTo('${item.id}')" class="mobile-nav-link flex items-center px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg touch-target" data-section="${item.id}">
                <i class="fas ${item.icon} mr-3 w-5"></i>
                <span>${item.label}</span>
            </a>
        `).join('');

        sidebar.innerHTML = `
            <div class="p-4 border-b flex items-center justify-between">
                <div class="flex items-center">
                    <img src="/static/logo.png" alt="SELA" class="w-10 h-10 rounded-lg mr-2">
                    <span class="font-bold text-lg">SELA</span>
                </div>
                <button onclick="closeMobileSidebar()" class="p-2 text-gray-500 hover:text-gray-700">
                    <i class="fas fa-times text-xl"></i>
                </button>
            </div>
            <nav class="p-4 space-y-2">
                ${navItems}
            </nav>
            <div class="absolute bottom-0 left-0 right-0 p-4 border-t">
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center">
                        <img id="sidebarAvatar" class="w-10 h-10 rounded-full mr-3" src="" alt="">
                        <span id="sidebarUserName" class="text-gray-700 font-medium"></span>
                    </div>
                </div>
                <div class="text-xs text-gray-400 mb-2">
                    é–’ç½®ç™»å‡º: <span id="sidebarTimer">5:00</span>
                </div>
                <button onclick="logout()" class="w-full py-2 text-red-500 hover:bg-red-50 rounded-lg flex items-center justify-center touch-target">
                    <i class="fas fa-sign-out-alt mr-2"></i>
                    <span>ç™»å‡º</span>
                </button>
            </div>
        `;

        // è¨­å®šç¬¬ä¸€å€‹ç‚º active
        const firstLink = sidebar.querySelector('.mobile-nav-link');
        if (firstLink) {
            firstLink.classList.remove('text-gray-600', 'hover:bg-gray-50');
            firstLink.classList.add('text-gray-700', 'bg-blue-50');
        }
    }

    // ============================================================
    // é›»è…¦ç‰ˆå´é‚Šæ¬„
    // ============================================================

    function renderDesktopSidebar() {
        const sidebar = document.getElementById('desktopSidebar');
        if (!sidebar) return;

        const navItems = NAV_ITEMS.map((item, index) => `
            <a href="#" onclick="showSection('${item.id}', event)" class="nav-link flex items-center px-4 py-2 ${index === 0 ? 'text-gray-700 bg-blue-50' : 'text-gray-600 hover:bg-gray-50'} rounded-lg" data-section="${item.id}">
                <i class="fas ${item.icon} mr-3"></i>
                <span>${item.label}</span>
            </a>
        `).join('');

        sidebar.innerHTML = `
            <nav class="p-4 space-y-2">
                ${navItems}
                <!-- ç®¡ç†å“¡å…¥å£ (é è¨­éš±è—) -->
                <a id="adminSidebarLink" href="#" onclick="showSection('admin', event)" class="hidden flex items-center px-4 py-2 text-orange-500 hover:bg-orange-50 rounded-lg mt-4 border-t pt-4" data-section="admin">
                    <i class="fas fa-user-shield mr-3"></i>
                    <span>ç®¡ç†å¾Œå°</span>
                </a>
            </nav>
        `;
    }

    // ============================================================
    // æ‰‹æ©Ÿç‰ˆåº•éƒ¨å°Žèˆªåˆ—
    // ============================================================

    function renderMobileBottomNav() {
        const nav = document.getElementById('mobileBottomNav');
        if (!nav) return;

        const navItems = BOTTOM_NAV_ITEMS.map((id, index) => {
            const item = NAV_ITEMS.find(n => n.id === id);
            if (!item) return '';
            return `
                <a href="#" onclick="mobileNavTo('${item.id}')" class="bottom-nav-item ${index === 0 ? 'active' : ''}" data-section="${item.id}">
                    <i class="fas ${item.icon}"></i>
                    <span>${item.mobileLabel || item.label}</span>
                </a>
            `;
        }).join('');

        nav.innerHTML = navItems;
    }

    // ============================================================
    // åˆå§‹åŒ–æ‰€æœ‰ä½ˆå±€å…ƒä»¶
    // ============================================================

    function initLayout() {
        renderMobileSidebar();
        renderDesktopSidebar();
        renderMobileBottomNav();
        console.log('âœ… ä½ˆå±€å…ƒä»¶å·²åˆå§‹åŒ–');
    }

    // ============================================================
    // å°Žå‡ºåˆ°å…¨åŸŸ
    // ============================================================

    window.initLayout = initLayout;
    window.renderMobileSidebar = renderMobileSidebar;
    window.renderDesktopSidebar = renderDesktopSidebar;
    window.renderMobileBottomNav = renderMobileBottomNav;

    // è‡ªå‹•åˆå§‹åŒ–
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLayout);
    } else {
        initLayout();
    }

})();