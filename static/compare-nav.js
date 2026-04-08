/**
 * SELA 報酬率比較功能 - 導航連結注入
 * 將此檔案放到 static/ 目錄，並在 dashboard.html 的 </body> 前引入
 * <script src="/static/compare-nav.js"></script>
 */

(function() {
    'use strict';
    
    // 等待 DOM 載入完成
    document.addEventListener('DOMContentLoaded', function() {
        injectCompareLinks();
    });
    
    // 如果 DOM 已經載入完成，直接執行
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(injectCompareLinks, 100);
    }
    
    function injectCompareLinks() {
        // 桌面版側邊欄連結 HTML
        const desktopLinkHTML = `
            <a href="/static/compare.html" class="nav-link flex items-center px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg">
                <i class="fas fa-chart-bar mr-3"></i>
                <span>報酬率比較</span>
            </a>
        `;
        
        // 手機版側邊欄連結 HTML
        const mobileLinkHTML = `
            <a href="/static/compare.html" class="mobile-nav-link flex items-center px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg touch-target">
                <i class="fas fa-chart-bar mr-3 w-6"></i>
                <span>報酬率比較</span>
            </a>
        `;
        
        // 找到「設定」連結並在其後插入
        // 桌面版
        const desktopSettingsLinks = document.querySelectorAll('a.nav-link');
        desktopSettingsLinks.forEach(function(link) {
            if (link.textContent.includes('設定') && !link.nextElementSibling?.textContent?.includes('報酬率')) {
                link.insertAdjacentHTML('afterend', desktopLinkHTML);
            }
        });
        
        // 手機版側邊欄
        const mobileSettingsLinks = document.querySelectorAll('a.mobile-nav-link');
        mobileSettingsLinks.forEach(function(link) {
            if (link.textContent.includes('設定') && !link.nextElementSibling?.textContent?.includes('報酬率')) {
                link.insertAdjacentHTML('afterend', mobileLinkHTML);
            }
        });
        
        // 也可以在儀表板區域加入快捷入口
        addDashboardQuickAccess();
        
        console.log('✅ 報酬率比較連結已注入');
    }
    
    function addDashboardQuickAccess() {
        // 找到儀表板區塊
        const dashboardSection = document.getElementById('section-dashboard');
        if (!dashboardSection) return;
        
        // 檢查是否已經有快捷入口
        if (dashboardSection.querySelector('.compare-quick-access')) return;
        
        // 在儀表板開頭加入快捷卡片
        const quickAccessHTML = `
            <div class="compare-quick-access bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl shadow-lg p-4 mb-6 text-white">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="font-bold text-lg">🏆 報酬率比較</h3>
                        <p class="text-indigo-100 text-sm">比較股票、加密貨幣的年化報酬</p>
                    </div>
                    <a href="/static/compare.html" 
                       class="px-4 py-2 bg-white text-indigo-600 rounded-lg font-medium hover:bg-indigo-50 transition">
                        立即比較 →
                    </a>
                </div>
            </div>
        `;
        
        // 找到第一個子元素並在前面插入
        const firstChild = dashboardSection.querySelector('h2');
        if (firstChild && firstChild.nextElementSibling) {
            firstChild.nextElementSibling.insertAdjacentHTML('beforebegin', quickAccessHTML);
        }
    }
})();
