/**
 * 交易表單模組 (P4 優化版)
 * 
 * 優化內容：
 * 1. DOM 快取 - 使用 $() 函數
 * 2. 減少重複查詢
 * 3. 券商選擇功能
 * 
 * 包含：台股/美股交易表單
 */

(function() {
    'use strict';

    let twLookupTimer = null;
    let usLookupTimer = null;
    let userBrokers = [];  // 🔧 券商列表快取

    // ============================================================
    // 券商管理
    // ============================================================

    async function loadBrokers() {
        try {
            const res = await apiRequest('/api/brokers');
            const data = await res.json();
            if (data.success) {
                userBrokers = data.data || [];
                renderBrokerSelect('twBroker');
                renderBrokerSelect('usBroker');
            }
        } catch (e) {
            console.error('載入券商失敗:', e);
        }
    }

    function renderBrokerSelect(selectId) {
        const select = $(selectId);
        if (!select) return;

        let html = '<option value="">不指定券商</option>';
        userBrokers.forEach(b => {
            const defaultMark = b.is_default ? ' ⭐' : '';
            html += `<option value="${b.id}" ${b.is_default ? 'selected' : ''}>${b.name}${defaultMark}</option>`;
        });
        html += '<option value="__new__">+ 新增券商...</option>';
        select.innerHTML = html;
    }

    async function handleBrokerChange(selectId) {
        const select = $(selectId);
        if (!select) return;

        if (select.value === '__new__') {
            const name = prompt('請輸入券商名稱：');
            if (name && name.trim()) {
                try {
                    const res = await apiRequest('/api/brokers', {
                        method: 'POST',
                        body: { name: name.trim() }
                    });
                    const data = await res.json();
                    if (data.success) {
                        showToast('券商已新增');
                        await loadBrokers();
                        // 選中新增的券商
                        if (data.data?.id) {
                            select.value = data.data.id;
                        }
                    } else {
                        showToast(data.detail || '新增失敗');
                        select.value = '';
                    }
                } catch (e) {
                    console.error('新增券商失敗:', e);
                    showToast('新增失敗');
                    select.value = '';
                }
            } else {
                select.value = '';
            }
        }
    }

    // ============================================================
    // 台股交易
    // ============================================================

    function showAddTwModal() {
        // ✅ P4: 使用 $() 快取
        $('twEditId').value = '';
        $('twModalTitle').textContent = '新增台股交易';
        setTwType('buy');
        $('twSymbol').value = '';
        $('twName').value = '';
        $('twNameDisplay').innerHTML = '<span class="text-gray-400">輸入代碼自動帶入</span>';
        $('twLots').value = '';
        $('twOddLot').value = '';
        $('twQuantityDisplay').textContent = '= 0 股';
        $('twPrice').value = '';
        $('twFee').value = '0';
        $('twTax').value = '0';
        $('twDate').value = new Date().toISOString().split('T')[0];
        $('twNote').value = '';

        // 🔧 載入券商列表
        loadBrokers();

        const modal = $('twTransactionModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    function closeTwModal() {
        const modal = $('twTransactionModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    function setTwType(type) {
        const buyBtn = $('twTypeBuy');
        const sellBtn = $('twTypeSell');
        const typeInput = $('twType');

        if (type === 'buy') {
            if (buyBtn) {
                buyBtn.classList.add('bg-green-500', 'text-white');
                buyBtn.classList.remove('bg-gray-100', 'text-gray-700');
            }
            if (sellBtn) {
                sellBtn.classList.remove('bg-red-500', 'text-white');
                sellBtn.classList.add('bg-gray-100', 'text-gray-700');
            }
        } else {
            if (sellBtn) {
                sellBtn.classList.add('bg-red-500', 'text-white');
                sellBtn.classList.remove('bg-gray-100', 'text-gray-700');
            }
            if (buyBtn) {
                buyBtn.classList.remove('bg-green-500', 'text-white');
                buyBtn.classList.add('bg-gray-100', 'text-gray-700');
            }
        }
        if (typeInput) typeInput.value = type;
    }

    function updateTwQuantity() {
        const lots = parseInt($('twLots')?.value) || 0;
        const oddLot = parseInt($('twOddLot')?.value) || 0;
        const total = lots * 1000 + oddLot;

        const display = $('twQuantityDisplay');
        if (display) display.textContent = `= ${total.toLocaleString()} 股`;

        const hidden = $('twQuantity');
        if (hidden) hidden.value = total;
    }

    function lookupTwStock() {
        clearTimeout(twLookupTimer);
        twLookupTimer = setTimeout(async () => {
            const symbol = $('twSymbol')?.value?.trim();
            if (!symbol || symbol.length < 4) return;

            try {
                // 🔧 修正：使用正確的 API 路徑
                const res = await apiRequest(`/api/stock/${symbol}.TW`);
                const data = await res.json();

                const nameDisplay = $('twNameDisplay');
                const nameInput = $('twName');

                // 🔧 修正：從回傳資料取得名稱
                const stockName = data.name || data.data?.name;
                if (data.success && stockName) {
                    if (nameDisplay) nameDisplay.innerHTML = `<span class="text-gray-800">${stockName}</span>`;
                    if (nameInput) nameInput.value = stockName;
                    
                    // 🔧 查詢該股票最後一筆交易價格
                    fetchLastTransactionPrice(`${symbol}.TW`, 'tw');
                } else {
                    if (nameDisplay) nameDisplay.innerHTML = '<span class="text-gray-400">查無資料</span>';
                }
            } catch (e) {
                console.error('查詢台股失敗:', e);
                const nameDisplay = $('twNameDisplay');
                if (nameDisplay) nameDisplay.innerHTML = '<span class="text-gray-400">查無資料</span>';
            }
        }, 500);
    }

    // 🔧 新增：獲取最後一筆交易價格
    async function fetchLastTransactionPrice(symbol, market) {
        try {
            const res = await apiRequest(`/api/portfolio/transactions/last-price/${symbol}`);
            const data = await res.json();
            
            if (data.success && data.price) {
                const priceInput = $(market === 'tw' ? 'twPrice' : 'usPrice');
                if (priceInput && !priceInput.value) {
                    priceInput.value = data.price;
                    priceInput.classList.add('bg-yellow-50');
                    setTimeout(() => priceInput.classList.remove('bg-yellow-50'), 1000);
                }
            }
        } catch (e) {
            // 沒有歷史交易，不處理
        }
    }

    async function submitTwTransaction() {
        const editId = $('twEditId')?.value;
        const rawSymbol = $('twSymbol')?.value?.trim();
        const symbol = rawSymbol ? `${rawSymbol}.TW` : '';  // 🔧 加上 .TW 後綴
        const name = $('twName')?.value?.trim();
        const type = $('twType')?.value;
        const quantity = parseInt($('twQuantity')?.value) || 0;
        const price = parseFloat($('twPrice')?.value) || 0;
        const fee = 0;  // 🔧 忽略手續費
        const tax = 0;  // 🔧 忽略交易稅
        const date = $('twDate')?.value;
        const note = $('twNote')?.value?.trim();
        const brokerId = $('twBroker')?.value;  // 🔧 券商 ID

        if (!symbol || quantity <= 0 || price <= 0) {
            showToast('請填寫完整資料');
            return;
        }

        const body = {
            symbol,
            name,
            transaction_type: type,
            quantity,
            price,
            fee,
            tax,
            transaction_date: date,
            note,
            broker_id: brokerId && brokerId !== '__new__' ? parseInt(brokerId) : null  // 🔧 加入券商
        };

        try {
            let res;
            if (editId) {
                res = await apiRequest(`/api/portfolio/transactions/${editId}`, {
                    method: 'PUT',
                    body
                });
            } else {
                res = await apiRequest('/api/portfolio/transactions', {
                    method: 'POST',
                    body
                });
            }

            const data = await res.json();

            if (data.success) {
                showToast(editId ? '交易已更新' : '交易已新增');
                closeTwModal();

                // ✅ P4: 清除 AppState 快取
                if (window.AppState) {
                    AppState.set('portfolioLoaded', false);
                }

                if (typeof loadPortfolio === 'function') loadPortfolio();
                if (typeof loadTransactions === 'function') loadTransactions('tw');
            } else {
                showToast(data.detail || '操作失敗');
            }
        } catch (e) {
            console.error('提交交易失敗:', e);
            showToast('操作失敗');
        }
    }

    async function editTwTransaction(id) {
        try {
            const res = await apiRequest(`/api/portfolio/transactions/${id}`);
            const data = await res.json();

            if (data.success) {
                const t = data.data;
                $('twEditId').value = t.id;
                $('twModalTitle').textContent = '編輯台股交易';
                setTwType(t.transaction_type);

                $('twSymbol').value = t.symbol.replace('.TW', '').replace('.TWO', '');
                $('twName').value = t.name || '';

                const nameDisplay = $('twNameDisplay');
                if (nameDisplay) {
                    nameDisplay.innerHTML = t.name
                        ? `<span class="text-gray-800">${t.name}</span>`
                        : '<span class="text-gray-400">--</span>';
                }

                const lots = Math.floor(t.quantity / 1000);
                const oddLot = t.quantity % 1000;
                $('twLots').value = lots || '';
                $('twOddLot').value = oddLot || '';
                updateTwQuantity();

                $('twPrice').value = t.price;
                $('twFee').value = t.fee || '';
                $('twTax').value = t.tax || '';
                $('twDate').value = t.transaction_date;
                $('twNote').value = t.note || '';

                const modal = $('twTransactionModal');
                if (modal) {
                    modal.classList.remove('hidden');
                    modal.classList.add('flex');
                }
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
        $('usEditId').value = '';
        $('usModalTitle').textContent = '新增美股交易';
        setUsType('buy');
        $('usSymbol').value = '';
        $('usName').value = '';
        $('usNameDisplay').innerHTML = '<span class="text-gray-400">輸入代碼自動帶入</span>';
        $('usQuantity').value = '';
        $('usPrice').value = '';
        $('usFee').value = '0';
        $('usTax').value = '0';
        $('usDate').value = new Date().toISOString().split('T')[0];
        $('usNote').value = '';

        // 🔧 載入券商列表
        loadBrokers();

        const modal = $('usTransactionModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    function closeUsModal() {
        const modal = $('usTransactionModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    function setUsType(type) {
        const buyBtn = $('usTypeBuy');
        const sellBtn = $('usTypeSell');
        const typeInput = $('usType');

        if (type === 'buy') {
            if (buyBtn) {
                buyBtn.classList.add('bg-green-500', 'text-white');
                buyBtn.classList.remove('bg-gray-100', 'text-gray-700');
            }
            if (sellBtn) {
                sellBtn.classList.remove('bg-red-500', 'text-white');
                sellBtn.classList.add('bg-gray-100', 'text-gray-700');
            }
        } else {
            if (sellBtn) {
                sellBtn.classList.add('bg-red-500', 'text-white');
                sellBtn.classList.remove('bg-gray-100', 'text-gray-700');
            }
            if (buyBtn) {
                buyBtn.classList.remove('bg-green-500', 'text-white');
                buyBtn.classList.add('bg-gray-100', 'text-gray-700');
            }
        }
        if (typeInput) typeInput.value = type;
    }

    function lookupUsStock() {
        clearTimeout(usLookupTimer);
        usLookupTimer = setTimeout(async () => {
            const symbol = $('usSymbol')?.value?.trim().toUpperCase();
            if (!symbol || symbol.length < 1) return;

            try {
                // 🔧 修正：使用正確的 API 路徑
                const res = await apiRequest(`/api/stock/${symbol}`);
                const data = await res.json();

                const nameDisplay = $('usNameDisplay');
                const nameInput = $('usName');

                // 🔧 修正：從回傳資料取得名稱
                const stockName = data.name || data.data?.name;
                if (data.success && stockName) {
                    if (nameDisplay) nameDisplay.innerHTML = `<span class="text-gray-800">${stockName}</span>`;
                    if (nameInput) nameInput.value = stockName;
                    
                    // 🔧 查詢該股票最後一筆交易價格
                    fetchLastTransactionPrice(symbol, 'us');
                } else {
                    if (nameDisplay) nameDisplay.innerHTML = '<span class="text-gray-400">查無資料</span>';
                }
            } catch (e) {
                console.error('查詢美股失敗:', e);
                const nameDisplay = $('usNameDisplay');
                if (nameDisplay) nameDisplay.innerHTML = '<span class="text-gray-400">查無資料</span>';
            }
        }, 500);
    }

    async function submitUsTransaction() {
        const editId = $('usEditId')?.value;
        const symbol = $('usSymbol')?.value?.trim().toUpperCase();
        const name = $('usName')?.value?.trim();
        const type = $('usType')?.value;
        const quantity = parseFloat($('usQuantity')?.value) || 0;
        const price = parseFloat($('usPrice')?.value) || 0;
        const fee = 0;  // 🔧 忽略手續費
        const tax = 0;  // 🔧 忽略交易稅
        const date = $('usDate')?.value;
        const note = $('usNote')?.value?.trim();
        const brokerId = $('usBroker')?.value;  // 🔧 券商 ID

        if (!symbol || quantity <= 0 || price <= 0) {
            showToast('請填寫完整資料');
            return;
        }

        const body = {
            symbol,
            name,
            transaction_type: type,
            quantity,
            price,
            fee,
            tax,
            transaction_date: date,
            note,
            broker_id: brokerId && brokerId !== '__new__' ? parseInt(brokerId) : null  // 🔧 加入券商
        };

        try {
            let res;
            if (editId) {
                res = await apiRequest(`/api/portfolio/transactions/${editId}`, {
                    method: 'PUT',
                    body
                });
            } else {
                res = await apiRequest('/api/portfolio/transactions', {
                    method: 'POST',
                    body
                });
            }

            const data = await res.json();

            if (data.success) {
                showToast(editId ? '交易已更新' : '交易已新增');
                closeUsModal();

                // ✅ P4: 清除 AppState 快取
                if (window.AppState) {
                    AppState.set('portfolioLoaded', false);
                }

                if (typeof loadPortfolio === 'function') loadPortfolio();
                if (typeof loadTransactions === 'function') loadTransactions('us');
            } else {
                showToast(data.detail || '操作失敗');
            }
        } catch (e) {
            console.error('提交交易失敗:', e);
            showToast('操作失敗');
        }
    }

    async function editUsTransaction(id) {
        try {
            const res = await apiRequest(`/api/portfolio/transactions/${id}`);
            const data = await res.json();

            if (data.success) {
                const t = data.data;
                $('usEditId').value = t.id;
                $('usModalTitle').textContent = '編輯美股交易';
                setUsType(t.transaction_type);

                $('usSymbol').value = t.symbol;
                $('usName').value = t.name || '';

                const nameDisplay = $('usNameDisplay');
                if (nameDisplay) {
                    nameDisplay.innerHTML = t.name
                        ? `<span class="text-gray-800">${t.name}</span>`
                        : '<span class="text-gray-400">--</span>';
                }

                $('usQuantity').value = t.quantity;
                $('usPrice').value = t.price;
                $('usFee').value = t.fee || '';
                $('usTax').value = t.tax || '';
                $('usDate').value = t.transaction_date;
                $('usNote').value = t.note || '';

                const modal = $('usTransactionModal');
                if (modal) {
                    modal.classList.remove('hidden');
                    modal.classList.add('flex');
                }
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
            $('twSymbol').value = cleanSymbol;
            $('twName').value = name || '';

            const nameDisplay = $('twNameDisplay');
            if (nameDisplay) {
                nameDisplay.innerHTML = name
                    ? `<span class="text-gray-800">${name}</span>`
                    : '<span class="text-gray-400">--</span>';
            }
        } else {
            showAddUsModal();
            setUsType(type);
            $('usSymbol').value = symbol;
            $('usName').value = name || '';

            const nameDisplay = $('usNameDisplay');
            if (nameDisplay) {
                nameDisplay.innerHTML = name
                    ? `<span class="text-gray-800">${name}</span>`
                    : '<span class="text-gray-400">--</span>';
            }
        }
    }

    // ============================================================
    // 導出
    // ============================================================

    // 掛載到 SELA 命名空間
    if (window.SELA) {
        window.SELA.transaction = {
            showTwModal: showAddTwModal,
            closeTwModal,
            showUsModal: showAddUsModal,
            closeUsModal,
            quickTrade
        };
    }

    // 全域導出（向後兼容）
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

    // 🔧 券商相關函數
    window.loadBrokers = loadBrokers;
    window.handleBrokerChange = handleBrokerChange;

    console.log('💰 transaction.js 模組已載入 (P4 優化版)');
})();
