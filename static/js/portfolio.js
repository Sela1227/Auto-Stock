/**
 * 個人投資記錄模組
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
        
        // 更新標籤樣式
        const activeClass = 'px-4 py-2 text-sm font-medium border-b-2 border-blue-500 text-blue-600 whitespace-nowrap';
        const inactiveClass = 'px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 whitespace-nowrap';
        
        document.getElementById('tabHoldings').className = tab === 'holdings' ? activeClass : inactiveClass;
        document.getElementById('tabTwTransactions').className = tab === 'tw-transactions' ? activeClass : inactiveClass;
        document.getElementById('tabUsTransactions').className = tab === 'us-transactions' ? activeClass : inactiveClass;
        
        // 顯示對應內容
        document.getElementById('portfolioHoldings').classList.toggle('hidden', tab !== 'holdings');
        document.getElementById('portfolioTwTransactions').classList.toggle('hidden', tab !== 'tw-transactions');
        document.getElementById('portfolioUsTransactions').classList.toggle('hidden', tab !== 'us-transactions');
        
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
    }
    
    async function loadPortfolioSummary() {
        try {
            const res = await apiRequest('/api/portfolio/summary');
            const data = await res.json();
            
            if (data.success) {
                const s = data.data;
                
                // 匯率
                const rateEl = document.getElementById('exchangeRateValue');
                const rateTimeEl = document.getElementById('exchangeRateTime');
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
                    const totalValueEl = document.getElementById('totalValueTwd');
                    if (totalValueEl) {
                        totalValueEl.textContent = s.total.current_value_twd 
                            ? `NT$${Math.round(s.total.current_value_twd).toLocaleString()}` : '--';
                    }
                    
                    const totalProfit = s.total.total_profit_twd || 0;
                    const totalProfitEl = document.getElementById('totalProfitTwd');
                    if (totalProfitEl) {
                        totalProfitEl.textContent = `${totalProfit >= 0 ? '+' : ''}NT$${Math.round(Math.abs(totalProfit)).toLocaleString()}`;
                        totalProfitEl.className = totalProfit >= 0 ? 'font-bold text-green-200' : 'font-bold text-red-200';
                    }
                    
                    const totalReturn = s.total.return_rate;
                    const totalReturnEl = document.getElementById('totalReturnRate');
                    if (totalReturnEl && totalReturn !== null && totalReturn !== undefined) {
                        totalReturnEl.textContent = `${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%`;
                        totalReturnEl.className = totalReturn >= 0 ? 'font-bold text-green-200' : 'font-bold text-red-200';
                    }
                    
                    const totalPosEl = document.getElementById('totalPositions');
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
        const valueEl = document.getElementById(`${market}CurrentValue`);
        if (valueEl) {
            valueEl.textContent = value > 0 ? `${currency}${Math.round(value).toLocaleString()}` : '--';
        }
        
        const profit = (data.realized_profit || 0) + (data.unrealized_profit || 0);
        const profitEl = document.getElementById(`${market}Profit`);
        if (profitEl) {
            profitEl.textContent = value > 0 
                ? `${profit >= 0 ? '+' : ''}${currency}${Math.round(Math.abs(profit)).toLocaleString()}` : '--';
            profitEl.className = profit >= 0 ? 'font-bold text-green-200' : 'font-bold text-red-200';
        }
        
        const returnRate = data.return_rate;
        const returnEl = document.getElementById(`${market}ReturnRate`);
        if (returnEl && returnRate !== null && returnRate !== undefined) {
            returnEl.textContent = `${returnRate >= 0 ? '+' : ''}${returnRate.toFixed(2)}%`;
            returnEl.className = returnRate >= 0 ? 'font-bold text-green-200' : 'font-bold text-red-200';
        }
        
        const posEl = document.getElementById(`${market}Positions`);
        if (posEl) posEl.textContent = data.positions || 0;
        
        // 摘要行
        const summaryEl = document.getElementById(`${market}SummaryLine`);
        if (summaryEl) {
            summaryEl.innerHTML = data.positions > 0
                ? `${data.positions} 檔 · 損益 <span class="${profit >= 0 ? 'text-green-600' : 'text-red-600'}">${profit >= 0 ? '+' : ''}${currency}${Math.round(Math.abs(profit)).toLocaleString()}</span>`
                : '尚無持股';
        }
    }
    
    async function loadHoldings() {
        const twContainer = document.getElementById('holdingsTW');
        const usContainer = document.getElementById('holdingsUS');
        
        try {
            const res = await apiRequest('/api/portfolio/holdings');
            const data = await res.json();
            
            if (data.success) {
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
        
        return `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer" 
                 onclick="searchSymbol('${h.symbol}')">
                <div class="flex-1 min-w-0">
                    <div class="flex items-center">
                        <span class="font-semibold text-gray-800">${h.symbol}</span>
                        <span class="text-gray-500 text-sm ml-2 truncate">${h.name || ''}</span>
                    </div>
                    <div class="text-xs text-gray-500">
                        ${h.quantity_display} @ ${currency}${h.avg_cost?.toFixed(2) || '--'}
                    </div>
                </div>
                <div class="text-right flex-shrink-0 ml-3">
                    <div class="font-semibold text-gray-800">${currency}${h.current_price?.toLocaleString() || '--'}</div>
                    <div class="text-sm ${profitClass}">
                        ${h.unrealized_profit !== null ? `${profitPrefix}${currency}${Math.abs(h.unrealized_profit).toLocaleString()}` : '--'}
                        ${h.unrealized_profit_pct !== null ? `(${profitPrefix}${h.unrealized_profit_pct.toFixed(1)}%)` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    async function loadTransactions(market) {
        const container = document.getElementById(market === 'tw' ? 'twTransactionList' : 'usTransactionList');
        if (!container) return;
        
        try {
            const res = await apiRequest(`/api/portfolio/transactions?market=${market}&limit=50`);
            const data = await res.json();
            
            if (data.success && data.data.length > 0) {
                container.innerHTML = data.data.map(t => renderTransactionCard(t)).join('');
            } else {
                container.innerHTML = '<p class="text-gray-400 text-center py-4">尚無交易紀錄</p>';
            }
        } catch (e) {
            console.error('載入交易紀錄失敗:', e);
            container.innerHTML = '<p class="text-red-500 text-center py-4">載入失敗</p>';
        }
    }
    
    function renderTransactionCard(t) {
        const isBuy = t.transaction_type === 'buy';
        const typeClass = isBuy ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700';
        const typeText = isBuy ? '買入' : '賣出';
        const currency = t.market === 'tw' ? 'NT$' : '$';
        
        return `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex-1 min-w-0">
                    <div class="flex items-center space-x-2">
                        <span class="px-2 py-0.5 rounded text-xs font-medium ${typeClass}">${typeText}</span>
                        <span class="font-semibold text-gray-800">${t.symbol}</span>
                        <span class="text-gray-500 text-sm truncate">${t.name || ''}</span>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                        ${t.transaction_date} · ${t.quantity_display} @ ${currency}${t.price}
                    </div>
                </div>
                <div class="flex items-center space-x-2 flex-shrink-0 ml-3">
                    <span class="font-semibold text-gray-800">${currency}${Math.round(t.total_amount).toLocaleString()}</span>
                    <button onclick="deleteTransaction(${t.id}, '${t.market}')" class="p-1 text-gray-400 hover:text-red-500">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    // ============================================================
    // 交易操作
    // ============================================================
    
    async function deleteTransaction(id, market) {
        if (!confirm('確定要刪除此交易紀錄嗎？')) return;
        
        try {
            const res = await apiRequest(`/api/portfolio/transactions/${id}`, {
                method: 'DELETE'
            });
            
            const data = await res.json();
            
            if (data.success) {
                showToast('已刪除');
                loadPortfolio();
            } else {
                showToast(data.detail || '刪除失敗');
            }
        } catch (e) {
            console.error('刪除交易失敗:', e);
            showToast('刪除失敗');
        }
    }
    
    // ============================================================
    // 匯出匯入
    // ============================================================
    
    function togglePortfolioMenu() {
        const menu = document.getElementById('portfolioMenu');
        if (menu) menu.classList.toggle('hidden');
    }
    
    async function exportPortfolio(format, market) {
        togglePortfolioMenu();
        
        try {
            let url = `/api/portfolio/export?format=${format}`;
            if (market) url += `&market=${market}`;
            
            const res = await apiRequest(url);
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || '匯出失敗');
            }
            
            const blob = await res.blob();
            const filename = res.headers.get('Content-Disposition')?.split('filename=')[1] || `portfolio.${format}`;
            
            const dlUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = dlUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(dlUrl);
            
            showToast('匯出成功！');
        } catch (e) {
            console.error('匯出失敗:', e);
            showToast(e.message || '匯出失敗');
        }
    }
    
    function showImportPortfolioModal() {
        togglePortfolioMenu();
        const modal = document.getElementById('importPortfolioModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }
    
    function hideImportPortfolioModal() {
        const modal = document.getElementById('importPortfolioModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        const fileInput = document.getElementById('importPortfolioFile');
        if (fileInput) fileInput.value = '';
        const preview = document.getElementById('importPortfolioPreview');
        if (preview) preview.innerHTML = '';
    }
    
    function previewPortfolioFile(input) {
        const file = input.files[0];
        if (!file) return;
        
        const preview = document.getElementById('importPortfolioPreview');
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                let items = [];
                const content = e.target.result;
                
                if (file.name.endsWith('.json')) {
                    const data = JSON.parse(content);
                    items = data.items || data;
                } else if (file.name.endsWith('.csv')) {
                    const lines = content.split('\n').filter(l => l.trim());
                    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
                    
                    for (let i = 1; i < lines.length; i++) {
                        const values = lines[i].split(',');
                        const obj = {};
                        headers.forEach((h, idx) => obj[h] = values[idx]?.trim());
                        if (obj.symbol && obj.quantity && obj.price) items.push(obj);
                    }
                }
                
                preview.innerHTML = `
                    <div class="p-3 bg-green-50 rounded-lg">
                        <p class="text-green-700 font-medium"><i class="fas fa-check-circle mr-2"></i>找到 ${items.length} 筆交易紀錄</p>
                        <p class="text-sm text-gray-600 mt-1">前幾筆: ${items.slice(0, 3).map(i => `${i.symbol} ${i.transaction_type || 'buy'} ${i.quantity}股`).join(', ')}${items.length > 3 ? '...' : ''}</p>
                    </div>
                `;
                preview.dataset.items = JSON.stringify(items);
            } catch (err) {
                preview.innerHTML = `<p class="text-red-500"><i class="fas fa-times-circle mr-2"></i>檔案解析失敗: ${err.message}</p>`;
            }
        };
        
        reader.readAsText(file);
    }
    
    async function importPortfolio() {
        const preview = document.getElementById('importPortfolioPreview');
        const itemsStr = preview?.dataset?.items;
        
        if (!itemsStr) {
            showToast('請先選擇檔案');
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
            showAddTwModal();
            document.getElementById('twSymbol').value = symbol;
            document.getElementById('twName').value = name;
            document.getElementById('twNameDisplay').innerHTML = `<span class="text-gray-800">${name}</span>`;
            setTwType(type);
        } else {
            showAddUsModal();
            document.getElementById('usSymbol').value = symbol;
            document.getElementById('usName').value = name;
            document.getElementById('usNameDisplay').innerHTML = `<span class="text-gray-800">${name}</span>`;
            setUsType(type);
        }
    }
    
    // ============================================================
    // 導出到全域
    // ============================================================
    
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
    
    console.log('💼 portfolio.js 模組已載入');
})();
