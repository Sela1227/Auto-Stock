/**
 * 交易表單模組（台股/美股）
 */

(function() {
    'use strict';
    
    let twLookupTimer = null;
    let usLookupTimer = null;
    let currentPortfolioTab = 'holdings';
    
    // ============================================================
    // 台股交易
    // ============================================================
    
    function showAddTwModal() {
        document.getElementById('twEditId').value = '';
        document.getElementById('twModalTitle').textContent = '新增台股交易';
        setTwType('buy');
        document.getElementById('twSymbol').value = '';
        document.getElementById('twName').value = '';
        document.getElementById('twNameDisplay').innerHTML = '<span class="text-gray-400">輸入代碼自動帶入</span>';
        document.getElementById('twLots').value = '';
        document.getElementById('twOddLot').value = '';
        document.getElementById('twQuantityDisplay').textContent = '= 0 股';
        document.getElementById('twPrice').value = '';
        document.getElementById('twFee').value = '';
        document.getElementById('twTax').value = '';
        document.getElementById('twDate').value = new Date().toISOString().split('T')[0];
        document.getElementById('twNote').value = '';
        
        document.getElementById('twTransactionModal').classList.remove('hidden');
        document.getElementById('twTransactionModal').classList.add('flex');
    }
    
    function closeTwModal() {
        document.getElementById('twTransactionModal').classList.add('hidden');
        document.getElementById('twTransactionModal').classList.remove('flex');
    }
    
    function setTwType(type) {
        document.getElementById('twTxType').value = type;
        if (type === 'buy') {
            document.getElementById('twBtnBuy').className = 'flex-1 py-2 rounded-lg font-medium transition-all bg-green-500 text-white';
            document.getElementById('twBtnSell').className = 'flex-1 py-2 rounded-lg font-medium transition-all bg-gray-200 text-gray-600';
            document.getElementById('twTaxField').classList.add('opacity-50');
        } else {
            document.getElementById('twBtnBuy').className = 'flex-1 py-2 rounded-lg font-medium transition-all bg-gray-200 text-gray-600';
            document.getElementById('twBtnSell').className = 'flex-1 py-2 rounded-lg font-medium transition-all bg-red-500 text-white';
            document.getElementById('twTaxField').classList.remove('opacity-50');
        }
    }
    
    function updateTwQuantity() {
        const lots = parseInt(document.getElementById('twLots').value) || 0;
        const oddLot = parseInt(document.getElementById('twOddLot').value) || 0;
        const total = lots * 1000 + oddLot;
        document.getElementById('twQuantityDisplay').textContent = `= ${total.toLocaleString()} 股`;
    }
    
    function lookupTwStock() {
        clearTimeout(twLookupTimer);
        const symbol = document.getElementById('twSymbol').value.trim();
        
        if (!symbol || symbol.length < 4) {
            document.getElementById('twNameDisplay').innerHTML = '<span class="text-gray-400">輸入代碼自動帶入</span>';
            document.getElementById('twName').value = '';
            return;
        }
        
        document.getElementById('twNameDisplay').innerHTML = '<span class="text-gray-400"><i class="fas fa-spinner fa-spin mr-1"></i>查詢中...</span>';
        
        twLookupTimer = setTimeout(async () => {
            try {
                const fullSymbol = symbol.includes('.') ? symbol : `${symbol}.TW`;
                const res = await fetch(`/api/stock/${fullSymbol}`);
                const data = await res.json();
                
                if (data.success && data.stock?.name) {
                    document.getElementById('twName').value = data.stock.name;
                    document.getElementById('twNameDisplay').innerHTML = `<span class="text-gray-800">${data.stock.name}</span>`;
                } else {
                    document.getElementById('twName').value = '';
                    document.getElementById('twNameDisplay').innerHTML = '<span class="text-red-500">查無此股票</span>';
                }
            } catch (e) {
                console.error('查詢台股失敗:', e);
                document.getElementById('twNameDisplay').innerHTML = '<span class="text-red-500">查詢失敗</span>';
            }
        }, 500);
    }
    
    async function submitTwTransaction() {
        const id = document.getElementById('twEditId').value;
        const symbol = document.getElementById('twSymbol').value.trim().toUpperCase();
        const name = document.getElementById('twName').value.trim();
        const lots = parseInt(document.getElementById('twLots').value) || 0;
        const oddLot = parseInt(document.getElementById('twOddLot').value) || 0;
        const quantity = lots * 1000 + oddLot;
        const price = parseFloat(document.getElementById('twPrice').value);
        const fee = parseFloat(document.getElementById('twFee').value) || 0;
        const tax = parseFloat(document.getElementById('twTax').value) || 0;
        const txDate = document.getElementById('twDate').value;
        const note = document.getElementById('twNote').value.trim();
        const txType = document.getElementById('twTxType').value;
        
        if (!symbol) { showToast('請輸入股票代碼'); return; }
        if (!name) { showToast('請等待股票名稱載入'); return; }
        if (quantity <= 0) { showToast('請輸入有效數量'); return; }
        if (!price || price <= 0) { showToast('請輸入有效價格'); return; }
        if (!txDate) { showToast('請選擇交易日期'); return; }
        
        const payload = {
            symbol: symbol.includes('.') ? symbol : `${symbol}.TW`,
            name,
            market: 'tw',
            transaction_type: txType,
            quantity,
            price,
            fee,
            tax,
            transaction_date: txDate,
            note: note || null,
        };
        
        try {
            let res;
            if (id) {
                res = await apiRequest(`/api/portfolio/transactions/${id}`, {
                    method: 'PUT',
                    body: payload,
                });
            } else {
                res = await apiRequest('/api/portfolio/transactions', {
                    method: 'POST',
                    body: payload,
                });
            }
            
            const data = await res.json();
            
            if (data.success) {
                showToast(id ? '交易已更新' : '交易已新增');
                closeTwModal();
                if (typeof loadPortfolio === 'function') loadPortfolio();
                if (currentPortfolioTab === 'tw-transactions' && typeof loadTransactions === 'function') {
                    loadTransactions('tw');
                }
            } else {
                showToast(data.detail || '操作失敗');
            }
        } catch (e) {
            console.error('台股交易操作失敗:', e);
            showToast('操作失敗');
        }
    }
    
    async function editTwTransaction(id) {
        try {
            const res = await apiRequest(`/api/portfolio/transactions/${id}`);
            const data = await res.json();
            
            if (data.success) {
                const t = data.data;
                document.getElementById('twEditId').value = t.id;
                document.getElementById('twModalTitle').textContent = '編輯台股交易';
                setTwType(t.transaction_type);
                
                const symbol = t.symbol.replace('.TW', '').replace('.TWO', '');
                document.getElementById('twSymbol').value = symbol;
                document.getElementById('twName').value = t.name || '';
                document.getElementById('twNameDisplay').innerHTML = t.name 
                    ? `<span class="text-gray-800">${t.name}</span>` 
                    : '<span class="text-gray-400">--</span>';
                
                const lots = Math.floor(t.quantity / 1000);
                const oddLot = t.quantity % 1000;
                document.getElementById('twLots').value = lots || '';
                document.getElementById('twOddLot').value = oddLot || '';
                updateTwQuantity();
                
                document.getElementById('twPrice').value = t.price;
                document.getElementById('twFee').value = t.fee || '';
                document.getElementById('twTax').value = t.tax || '';
                document.getElementById('twDate').value = t.transaction_date;
                document.getElementById('twNote').value = t.note || '';
                
                document.getElementById('twTransactionModal').classList.remove('hidden');
                document.getElementById('twTransactionModal').classList.add('flex');
            }
        } catch (e) {
            console.error('載入交易失敗:', e);
            showToast('載入失敗');
        }
    }
    
    // ============================================================
    // 美股交易
    // ============================================================
    
    function showAddUsModal() {
        document.getElementById('usEditId').value = '';
        document.getElementById('usModalTitle').textContent = '新增美股交易';
        setUsType('buy');
        document.getElementById('usSymbol').value = '';
        document.getElementById('usName').value = '';
        document.getElementById('usNameDisplay').innerHTML = '<span class="text-gray-400">輸入代碼自動帶入</span>';
        document.getElementById('usQuantity').value = '';
        document.getElementById('usPrice').value = '';
        document.getElementById('usFee').value = '';
        document.getElementById('usTax').value = '';
        document.getElementById('usDate').value = new Date().toISOString().split('T')[0];
        document.getElementById('usNote').value = '';
        
        document.getElementById('usTransactionModal').classList.remove('hidden');
        document.getElementById('usTransactionModal').classList.add('flex');
    }
    
    function closeUsModal() {
        document.getElementById('usTransactionModal').classList.add('hidden');
        document.getElementById('usTransactionModal').classList.remove('flex');
    }
    
    function setUsType(type) {
        document.getElementById('usTxType').value = type;
        if (type === 'buy') {
            document.getElementById('usBtnBuy').className = 'flex-1 py-2 rounded-lg font-medium transition-all bg-green-500 text-white';
            document.getElementById('usBtnSell').className = 'flex-1 py-2 rounded-lg font-medium transition-all bg-gray-200 text-gray-600';
            document.getElementById('usTaxField').classList.add('opacity-50');
        } else {
            document.getElementById('usBtnBuy').className = 'flex-1 py-2 rounded-lg font-medium transition-all bg-gray-200 text-gray-600';
            document.getElementById('usBtnSell').className = 'flex-1 py-2 rounded-lg font-medium transition-all bg-blue-500 text-white';
            document.getElementById('usTaxField').classList.remove('opacity-50');
        }
    }
    
    function lookupUsStock() {
        clearTimeout(usLookupTimer);
        const symbol = document.getElementById('usSymbol').value.trim().toUpperCase();
        
        if (!symbol || symbol.length < 1) {
            document.getElementById('usNameDisplay').innerHTML = '<span class="text-gray-400">輸入代碼自動帶入</span>';
            document.getElementById('usName').value = '';
            return;
        }
        
        document.getElementById('usNameDisplay').innerHTML = '<span class="text-gray-400"><i class="fas fa-spinner fa-spin mr-1"></i>查詢中...</span>';
        
        usLookupTimer = setTimeout(async () => {
            try {
                const res = await fetch(`/api/stock/${symbol}`);
                const data = await res.json();
                
                if (data.success && data.stock?.name) {
                    document.getElementById('usName').value = data.stock.name;
                    document.getElementById('usNameDisplay').innerHTML = `<span class="text-gray-800">${data.stock.name}</span>`;
                } else {
                    document.getElementById('usName').value = '';
                    document.getElementById('usNameDisplay').innerHTML = '<span class="text-red-500">查無此股票</span>';
                }
            } catch (e) {
                console.error('查詢美股失敗:', e);
                document.getElementById('usNameDisplay').innerHTML = '<span class="text-red-500">查詢失敗</span>';
            }
        }, 500);
    }
    
    async function submitUsTransaction() {
        const id = document.getElementById('usEditId').value;
        const symbol = document.getElementById('usSymbol').value.trim().toUpperCase();
        const name = document.getElementById('usName').value.trim();
        const quantity = parseInt(document.getElementById('usQuantity').value);
        const price = parseFloat(document.getElementById('usPrice').value);
        const fee = parseFloat(document.getElementById('usFee').value) || 0;
        const tax = parseFloat(document.getElementById('usTax').value) || 0;
        const txDate = document.getElementById('usDate').value;
        const note = document.getElementById('usNote').value.trim();
        const txType = document.getElementById('usTxType').value;
        
        if (!symbol) { showToast('請輸入股票代碼'); return; }
        if (!name) { showToast('請等待股票名稱載入'); return; }
        if (!quantity || quantity <= 0) { showToast('請輸入有效股數'); return; }
        if (!price || price <= 0) { showToast('請輸入有效價格'); return; }
        if (!txDate) { showToast('請選擇交易日期'); return; }
        
        const payload = {
            symbol,
            name,
            market: 'us',
            transaction_type: txType,
            quantity,
            price,
            fee,
            tax,
            transaction_date: txDate,
            note: note || null,
        };
        
        try {
            let res;
            if (id) {
                res = await apiRequest(`/api/portfolio/transactions/${id}`, {
                    method: 'PUT',
                    body: payload,
                });
            } else {
                res = await apiRequest('/api/portfolio/transactions', {
                    method: 'POST',
                    body: payload,
                });
            }
            
            const data = await res.json();
            
            if (data.success) {
                showToast(id ? '交易已更新' : '交易已新增');
                closeUsModal();
                if (typeof loadPortfolio === 'function') loadPortfolio();
                if (currentPortfolioTab === 'us-transactions' && typeof loadTransactions === 'function') {
                    loadTransactions('us');
                }
            } else {
                showToast(data.detail || '操作失敗');
            }
        } catch (e) {
            console.error('美股交易操作失敗:', e);
            showToast('操作失敗');
        }
    }
    
    async function editUsTransaction(id) {
        try {
            const res = await apiRequest(`/api/portfolio/transactions/${id}`);
            const data = await res.json();
            
            if (data.success) {
                const t = data.data;
                document.getElementById('usEditId').value = t.id;
                document.getElementById('usModalTitle').textContent = '編輯美股交易';
                setUsType(t.transaction_type);
                
                document.getElementById('usSymbol').value = t.symbol;
                document.getElementById('usName').value = t.name || '';
                document.getElementById('usNameDisplay').innerHTML = t.name 
                    ? `<span class="text-gray-800">${t.name}</span>` 
                    : '<span class="text-gray-400">--</span>';
                document.getElementById('usQuantity').value = t.quantity;
                document.getElementById('usPrice').value = t.price;
                document.getElementById('usFee').value = t.fee || '';
                document.getElementById('usTax').value = t.tax || '';
                document.getElementById('usDate').value = t.transaction_date;
                document.getElementById('usNote').value = t.note || '';
                
                document.getElementById('usTransactionModal').classList.remove('hidden');
                document.getElementById('usTransactionModal').classList.add('flex');
            }
        } catch (e) {
            console.error('載入交易失敗:', e);
            showToast('載入失敗');
        }
    }
    
    // ============================================================
    // 快速交易（覆寫 portfolio.js 的版本）
    // ============================================================
    
    function quickTrade(symbol, name, market, type) {
        if (market === 'tw') {
            showAddTwModal();
            setTwType(type);
            const cleanSymbol = symbol.replace('.TW', '').replace('.TWO', '');
            document.getElementById('twSymbol').value = cleanSymbol;
            document.getElementById('twName').value = name || '';
            document.getElementById('twNameDisplay').innerHTML = name 
                ? `<span class="text-gray-800">${name}</span>` 
                : '<span class="text-gray-400">--</span>';
        } else {
            showAddUsModal();
            setUsType(type);
            document.getElementById('usSymbol').value = symbol;
            document.getElementById('usName').value = name || '';
            document.getElementById('usNameDisplay').innerHTML = name 
                ? `<span class="text-gray-800">${name}</span>` 
                : '<span class="text-gray-400">--</span>';
        }
    }
    
    // ============================================================
    // 導出到全域
    // ============================================================
    
    window.showAddTwModal = showAddTwModal;
    window.closeTwModal = closeTwModal;
    window.setTwType = setTwType;
    window.updateTwQuantity = updateTwQuantity;
    window.lookupTwStock = lookupTwStock;
    window.submitTwTransaction = submitTwTransaction;
    window.editTwTransaction = editTwTransaction;
    
    window.showAddUsModal = showAddUsModal;
    window.closeUsModal = closeUsModal;
    window.setUsType = setUsType;
    window.lookupUsStock = lookupUsStock;
    window.submitUsTransaction = submitUsTransaction;
    window.editUsTransaction = editUsTransaction;
    
    window.quickTrade = quickTrade;
    
    console.log('💰 transaction.js 模組已載入');
})();
