/**
 * 個人投資記錄模組 (P3 優化版)
 * 
 * 優化內容：
 * 1. 事件委託 - 減少監聽器數量
 * 2. AppState 整合 - 統一狀態管理
 * 3. DOM 快取 - 使用 $() 函數
 * 
 * 包含：持股總覽、交易紀錄、匯出匯入
 */

(function() {
    'use strict';

    // ============================================================
    // 私有變數
    // ============================================================

    let currentPortfolioTab = 'holdings';

    // ============================================================
    // Tab 切換
    // ============================================================

    function switchPortfolioTab(tab) {
        currentPortfolioTab = tab;

        const activeClass = 'px-4 py-2 text-sm font-medium border-b-2 border-blue-500 text-blue-600 whitespace-nowrap';
        const inactiveClass = 'px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 whitespace-nowrap';

        // ✅ P3: 使用 $() 快取
        const tabHoldings = $('tabHoldings');
        const tabTw = $('tabTwTransactions');
        const tabUs = $('tabUsTransactions');

        if (tabHoldings) tabHoldings.className = tab === 'holdings' ? activeClass : inactiveClass;
        if (tabTw) tabTw.className = tab === 'tw-transactions' ? activeClass : inactiveClass;
        if (tabUs) tabUs.className = tab === 'us-transactions' ? activeClass : inactiveClass;

        // 顯示對應內容
        const holdingsEl = $('portfolioHoldings');
        const twEl = $('portfolioTwTransactions');
        const usEl = $('portfolioUsTransactions');

        if (holdingsEl) holdingsEl.classList.toggle('hidden', tab !== 'holdings');
        if (twEl) twEl.classList.toggle('hidden', tab !== 'tw-transactions');
        if (usEl) usEl.classList.toggle('hidden', tab !== 'us-transactions');

        // 載入資料
        if (tab === 'holdings') loadHoldings();
        else if (tab === 'tw-transactions') loadTransactions('tw');
        else if (tab === 'us-transactions') loadTransactions('us');
    }

    // ============================================================
    // 載入功能
    // ============================================================

    async function loadPortfolio() {
        await loadPortfolioSummary();
        await loadHoldings();

        // ✅ P3: 初始化事件委託
        initPortfolioEventDelegation();
    }

    async function loadPortfolioSummary() {
        try {
            const res = await apiRequest('/api/portfolio/summary');
            const data = await res.json();

            if (data.success) {
                const s = data.data;

                // ✅ P3: 同步到 AppState
                if (window.AppState) {
                    AppState.setPortfolio({ summary: s });
                }

                // 匯率
                const rateEl = $('exchangeRateValue');
                const rateTimeEl = $('exchangeRateTime');
                if (rateEl) rateEl.textContent = s.exchange_rate?.toFixed(2) || '--';
                if (rateTimeEl && s.exchange_rate_updated_at) {
                    const time = new Date(s.exchange_rate_updated_at).toLocaleTimeString('zh-TW', {hour: '2-digit', minute: '2-digit'});
                    rateTimeEl.textContent = `(${time})`;
                }

                // 台股
                updateSummarySection('tw', s.tw, 'NT$');

                // 美股
                updateSummarySection('us', s.us, '$');

                // 合計
                if (s.total) {
                    const totalValueEl = $('totalValueTwd');
                    if (totalValueEl) {
                        totalValueEl.textContent = s.total.current_value_twd
                            ? `NT$${Math.round(s.total.current_value_twd).toLocaleString()}` : '--';
                    }

                    const totalProfit = s.total.total_profit_twd || 0;
                    const totalProfitEl = $('totalProfitTwd');
                    if (totalProfitEl) {
                        totalProfitEl.textContent = `${totalProfit >= 0 ? '+' : ''}NT$${Math.round(Math.abs(totalProfit)).toLocaleString()}`;
                        totalProfitEl.className = totalProfit >= 0 ? 'font-bold text-green-200' : 'font-bold text-red-200';
                    }

                    const totalReturn = s.total.return_rate;
                    const totalReturnEl = $('totalReturnRate');
                    if (totalReturnEl && totalReturn !== null && totalReturn !== undefined) {
                        totalReturnEl.textContent = `${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%`;
                        totalReturnEl.className = totalReturn >= 0 ? 'font-bold text-green-200' : 'font-bold text-red-200';
                    }

                    const totalPosEl = $('totalPositions');
                    if (totalPosEl) totalPosEl.textContent = s.total.positions || 0;
                }
            }
        } catch (e) {
            console.error('載入投資摘要失敗:', e);
        }
    }

    function updateSummarySection(market, data, currency) {
        if (!data) return;

        const value = data.current_value || 0;
        const valueEl = $(`${market}CurrentValue`);
        if (valueEl) {
            valueEl.textContent = value > 0 ? `${currency}${Math.round(value).toLocaleString()}` : '--';
        }

        const profit = (data.realized_profit || 0) + (data.unrealized_profit || 0);
        const profitEl = $(`${market}Profit`);
        if (profitEl) {
            profitEl.textContent = value > 0
                ? `${profit >= 0 ? '+' : ''}${currency}${Math.round(Math.abs(profit)).toLocaleString()}` : '--';
            profitEl.className = profit >= 0 ? 'font-bold text-green-200' : 'font-bold text-red-200';
        }

        const returnRate = data.return_rate;
        const returnEl = $(`${market}ReturnRate`);
        if (returnEl && returnRate !== null && returnRate !== undefined) {
            returnEl.textContent = `${returnRate >= 0 ? '+' : ''}${returnRate.toFixed(2)}%`;
            returnEl.className = returnRate >= 0 ? 'font-bold text-green-200' : 'font-bold text-red-200';
        }

        const posEl = $(`${market}Positions`);
        if (posEl) posEl.textContent = data.positions || 0;

        // 摘要行
        const summaryEl = $(`${market}SummaryLine`);
        if (summaryEl) {
            summaryEl.innerHTML = data.positions > 0
                ? `${data.positions} 檔 · 損益 <span class="${profit >= 0 ? 'text-green-600' : 'text-red-600'}">${profit >= 0 ? '+' : ''}${currency}${Math.round(Math.abs(profit)).toLocaleString()}</span>`
                : '尚無持股';
        }
    }

    async function loadHoldings() {
        const twContainer = $('holdingsTW');
        const usContainer = $('holdingsUS');

        try {
            const res = await apiRequest('/api/portfolio/holdings');
            const data = await res.json();

            if (data.success) {
                // ✅ P3: 同步到 AppState
                if (window.AppState) {
                    AppState.setPortfolio({
                        tw: data.data.tw || [],
                        us: data.data.us || []
                    });
                }

                if (twContainer) {
                    twContainer.innerHTML = data.data.tw && data.data.tw.length > 0
                        ? data.data.tw.map(h => renderHoldingCard(h, 'tw')).join('')
                        : '<p class="text-gray-400 text-center py-4">尚無台股持股</p>';
                }

                if (usContainer) {
                    usContainer.innerHTML = data.data.us && data.data.us.length > 0
                        ? data.data.us.map(h => renderHoldingCard(h, 'us')).join('')
                        : '<p class="text-gray-400 text-center py-4">尚無美股持股</p>';
                }
            }
        } catch (e) {
            console.error('載入持股失敗:', e);
            if (twContainer) twContainer.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
            if (usContainer) usContainer.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
        }
    }

    function renderHoldingCard(h, market) {
        const profitClass = (h.unrealized_profit || 0) >= 0 ? 'text-green-600' : 'text-red-600';
        const profitPrefix = (h.unrealized_profit || 0) >= 0 ? '+' : '';
        const currency = market === 'tw' ? 'NT$' : '$';
        
        // 🔧 安全處理 return_rate（可能是 null 或 undefined）
        const returnRateDisplay = (h.return_rate != null) 
            ? `${h.return_rate >= 0 ? '+' : ''}${h.return_rate.toFixed(2)}%` 
            : '--';

        // ✅ P3: 使用 data-action 替代 onclick
        return `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                 data-action="analyze" data-symbol="${h.symbol}">
                <div class="flex-1 min-w-0">
                    <div class="flex items-center">
                        <span class="font-semibold text-gray-800">${h.symbol}</span>
                        <span class="text-gray-500 text-sm ml-2 truncate">${h.name || ''}</span>
                    </div>
                    <div class="text-xs text-gray-500">
                        ${h.quantity_display || h.quantity || 0} @ ${currency}${h.avg_cost?.toFixed(2) || '--'}
                    </div>
                </div>
                <div class="text-right">
                    <div class="font-semibold ${profitClass}">
                        ${profitPrefix}${currency}${Math.round(Math.abs(h.unrealized_profit || 0)).toLocaleString()}
                    </div>
                    <div class="text-xs ${profitClass}">
                        ${returnRateDisplay}
                    </div>
                </div>
            </div>
        `;
    }

    async function loadTransactions(market) {
        const container = $(market === 'tw' ? 'twTransactionList' : 'usTransactionList');
        if (!container) return;

        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-spinner fa-spin text-blue-600"></i>
            </div>
        `;

        try {
            const res = await apiRequest(`/api/portfolio/transactions/${market}`);
            const data = await res.json();

            if (data.success && data.data && data.data.length > 0) {
                container.innerHTML = data.data.map(t => renderTransactionCard(t, market)).join('');
            } else {
                container.innerHTML = `<p class="text-gray-400 text-center py-4">尚無交易紀錄</p>`;
            }
        } catch (e) {
            console.error('載入交易紀錄失敗:', e);
            container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
        }
    }

    function renderTransactionCard(t, market) {
        const typeClass = t.transaction_type === 'buy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';
        const typeText = t.transaction_type === 'buy' ? '買入' : '賣出';
        const currency = market === 'tw' ? 'NT$' : '$';

        // ✅ P3: 使用 data-action 替代 onclick
        return `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg" data-id="${t.id}">
                <div class="flex-1">
                    <div class="flex items-center gap-2">
                        <span class="font-semibold">${t.symbol}</span>
                        <span class="px-2 py-0.5 text-xs rounded ${typeClass}">${typeText}</span>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                        ${t.quantity_display} @ ${currency}${t.price?.toFixed(2)} · ${new Date(t.transaction_date).toLocaleDateString()}
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="font-medium">${currency}${Math.round(t.total_amount).toLocaleString()}</span>
                    <button data-action="edit-transaction" data-id="${t.id}" data-market="${market}"
                            class="p-1.5 text-gray-400 hover:text-blue-500" title="編輯">
                        <i class="fas fa-edit text-xs"></i>
                    </button>
                    <button data-action="delete-transaction" data-id="${t.id}" data-market="${market}"
                            class="p-1.5 text-gray-400 hover:text-red-500">
                        <i class="fas fa-trash text-xs"></i>
                    </button>
                </div>
            </div>
        `;
    }

    async function deleteTransaction(id, market) {
        if (!confirm('確定要刪除此交易紀錄嗎？')) return;

        try {
            const res = await apiRequest(`/api/portfolio/transactions/${id}`, {
                method: 'DELETE'
            });

            const data = await res.json();

            if (data.success) {
                showToast('已刪除');
                loadTransactions(market);
                loadPortfolioSummary();
                loadHoldings();
            } else {
                showToast(data.detail || '刪除失敗');
            }
        } catch (e) {
            console.error('刪除失敗:', e);
            showToast('刪除失敗');
        }
    }

    // ============================================================
    // 事件委託 (P3 核心優化)
    // ============================================================

    let delegationInitialized = false;

    function initPortfolioEventDelegation() {
        const section = $('section-portfolio');
        if (!section || delegationInitialized) return;

        section.addEventListener('click', handlePortfolioClick);
        delegationInitialized = true;
    }

    function handlePortfolioClick(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        e.preventDefault();
        const action = target.dataset.action;

        switch (action) {
            case 'analyze':
                if (typeof searchSymbol === 'function') {
                    searchSymbol(target.dataset.symbol);
                }
                break;

            case 'delete-transaction':
                deleteTransaction(
                    parseInt(target.dataset.id),
                    target.dataset.market
                );
                break;

            case 'switch-tab':
                switchPortfolioTab(target.dataset.tab);
                break;

            case 'export':
                exportPortfolio();
                break;

            case 'show-import':
                showImportPortfolioModal();
                break;
        }
    }

    // ============================================================
    // 匯出匯入
    // ============================================================

    function togglePortfolioMenu() {
        const menu = $('portfolioMenu');
        if (menu) {
            menu.classList.toggle('hidden');
        }
    }

    async function exportPortfolio() {
        try {
            const res = await apiRequest('/api/portfolio/export');
            const data = await res.json();

            if (!data.success) {
                showToast('匯出失敗');
                return;
            }

            const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `portfolio_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showToast('匯出成功');
            const menu = $('portfolioMenu');
            if (menu) menu.classList.add('hidden');
        } catch (e) {
            console.error('匯出失敗:', e);
            showToast('匯出失敗');
        }
    }

    function showImportPortfolioModal() {
        const modal = $('importPortfolioModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
        const menu = $('portfolioMenu');
        if (menu) menu.classList.add('hidden');
    }

    function hideImportPortfolioModal() {
        const modal = $('importPortfolioModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        const preview = $('importPortfolioPreview');
        if (preview) preview.innerHTML = '';
    }

    function previewPortfolioFile(event) {
        const file = event.target.files[0];
        if (!file) return;

        const preview = $('importPortfolioPreview');
        if (!preview) return;

        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const items = JSON.parse(e.target.result);
                preview.innerHTML = `
                    <div class="mt-4 p-3 bg-gray-50 rounded-lg">
                        <p class="text-sm text-gray-600 mb-2">預覽 (${items.length} 筆):</p>
                        <ul class="text-sm space-y-1 max-h-40 overflow-y-auto">
                            ${items.slice(0, 10).map(item => `
                                <li class="flex justify-between">
                                    <span class="font-medium">${item.symbol}</span>
                                    <span class="text-gray-500">${item.transaction_type} ${item.quantity}</span>
                                </li>
                            `).join('')}
                            ${items.length > 10 ? `<li class="text-gray-400">...還有 ${items.length - 10} 筆</li>` : ''}
                        </ul>
                    </div>
                `;
            } catch (err) {
                preview.innerHTML = '<p class="text-red-500 text-sm mt-2">檔案格式錯誤</p>';
            }
        };
        reader.readAsText(file);
    }

    async function importPortfolio() {
        const textarea = $('importPortfolioData');
        const itemsStr = textarea?.value?.trim();

        if (!itemsStr) {
            showToast('請輸入資料');
            return;
        }

        try {
            const items = JSON.parse(itemsStr);

            const res = await apiRequest('/api/portfolio/import', {
                method: 'POST',
                body: { items }
            });

            const data = await res.json();

            if (data.success) {
                showToast(data.message);
                hideImportPortfolioModal();

                // ✅ P3: 清除 AppState 快取
                if (window.AppState) {
                    AppState.set('portfolioLoaded', false);
                }

                loadPortfolio();
            } else {
                showToast(data.detail || '匯入失敗');
            }
        } catch (e) {
            console.error('匯入失敗:', e);
            showToast('匯入失敗');
        }
    }

    // ============================================================
    // 快速交易（從追蹤清單）
    // ============================================================

    function quickTrade(symbol, name, market, type) {
        if (market === 'tw') {
            if (typeof showAddTwModal === 'function') showAddTwModal();
            const symEl = $('twSymbol');
            const nameEl = $('twName');
            const nameDisplay = $('twNameDisplay');
            if (symEl) symEl.value = symbol;
            if (nameEl) nameEl.value = name;
            if (nameDisplay) nameDisplay.innerHTML = `<span class="text-gray-800">${name}</span>`;
            if (typeof setTwType === 'function') setTwType(type);
        } else {
            if (typeof showAddUsModal === 'function') showAddUsModal();
            const symEl = $('usSymbol');
            const nameEl = $('usName');
            const nameDisplay = $('usNameDisplay');
            if (symEl) symEl.value = symbol;
            if (nameEl) nameEl.value = name;
            if (nameDisplay) nameDisplay.innerHTML = `<span class="text-gray-800">${name}</span>`;
            if (typeof setUsType === 'function') setUsType(type);
        }
    }

    // ============================================================
    // 導出
    // ============================================================

    // 掛載到 SELA 命名空間
    if (window.SELA) {
        window.SELA.portfolio = {
            load: loadPortfolio,
            loadSummary: loadPortfolioSummary,
            loadHoldings,
            loadTransactions,
            switchTab: switchPortfolioTab,
            exportData: exportPortfolio,
            importData: importPortfolio,
            quickTrade
        };
    }

    // 全域導出（向後兼容）
    window.loadPortfolio = loadPortfolio;
    window.loadPortfolioSummary = loadPortfolioSummary;
    window.loadHoldings = loadHoldings;
    window.loadTransactions = loadTransactions;
    window.switchPortfolioTab = switchPortfolioTab;
    window.deleteTransaction = deleteTransaction;
    window.togglePortfolioMenu = togglePortfolioMenu;
    window.exportPortfolio = exportPortfolio;
    window.showImportPortfolioModal = showImportPortfolioModal;
    window.hideImportPortfolioModal = hideImportPortfolioModal;
    window.previewPortfolioFile = previewPortfolioFile;
    window.importPortfolio = importPortfolio;
    window.quickTrade = quickTrade;

})();
