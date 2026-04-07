/**
 * 佈局元件動態生成模組
 * 生成側邊欄、底部導航等重複使用的 UI 元件
 */

(function() {
    'use strict';

    // ============================================================
    // 導航項目配置
    // ============================================================

    const NAV_ITEMS = [
        { id: 'dashboard', icon: 'fa-tachometer-alt', label: '儀表板', mobileLabel: '首頁' },
        { id: 'search', icon: 'fa-search', label: '股票查詢', mobileLabel: '查詢' },
        { id: 'watchlist', icon: 'fa-star', label: '追蹤清單', mobileLabel: '追蹤' },
        { id: 'sentiment', icon: 'fa-heart-pulse', label: '恐懼貪婪', mobileLabel: '情緒' },
        { id: 'compare', icon: 'fa-chart-line', label: '走勢比較' },
        { id: 'portfolio', icon: 'fa-wallet', label: '個人投資記錄' },
        { id: 'subscription', icon: 'fa-satellite-dish', label: '訂閱精選' },
        { id: 'cagr', icon: 'fa-trophy', label: '報酬率比較' },
        { id: 'settings', icon: 'fa-cog', label: '設定', mobileLabel: '設定', showInBottomNav: true }
    ];

    // 底部導航顯示的項目
    const BOTTOM_NAV_ITEMS = ['dashboard', 'search', 'watchlist', 'sentiment', 'settings'];

    // ============================================================
    // 手機版側邊選單
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
                    閒置登出: <span id="sidebarTimer">5:00</span>
                </div>
                <button onclick="logout()" class="w-full py-2 text-red-500 hover:bg-red-50 rounded-lg flex items-center justify-center touch-target">
                    <i class="fas fa-sign-out-alt mr-2"></i>
                    <span>登出</span>
                </button>
            </div>
        `;

        // 設定第一個為 active
        const firstLink = sidebar.querySelector('.mobile-nav-link');
        if (firstLink) {
            firstLink.classList.remove('text-gray-600', 'hover:bg-gray-50');
            firstLink.classList.add('text-gray-700', 'bg-blue-50');
        }
    }

    // ============================================================
    // 電腦版側邊欄
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
                <!-- 管理員入口 (預設隱藏) -->
                <a id="adminSidebarLink" href="#" onclick="showSection('admin', event)" class="hidden flex items-center px-4 py-2 text-orange-500 hover:bg-orange-50 rounded-lg mt-4 border-t pt-4" data-section="admin">
                    <i class="fas fa-user-shield mr-3"></i>
                    <span>管理後台</span>
                </a>
            </nav>
        `;
    }

    // ============================================================
    // 手機版底部導航列
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
    // 初始化所有佈局元件
    // ============================================================

    function initLayout() {
        renderMobileSidebar();
        renderDesktopSidebar();
        renderMobileBottomNav();
        console.log('✅ 佈局元件已初始化');
    }

    // ============================================================
    // 導出到全域
    // ============================================================

    window.initLayout = initLayout;
    window.renderMobileSidebar = renderMobileSidebar;
    window.renderDesktopSidebar = renderDesktopSidebar;
    window.renderMobileBottomNav = renderMobileBottomNav;

    // 自動初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLayout);
    } else {
        initLayout();
    }

})();
