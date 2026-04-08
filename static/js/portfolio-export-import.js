/**
 * 持股交易匯出匯入功能
 * P1 功能增強
 * 
 * 在現有 portfolio.js 基礎上新增匯出匯入功能
 */

(function() {
    'use strict';
    
    // ============================================================
    // 匯出功能
    // ============================================================
    
    /**
     * 匯出交易記錄
     * @param {string} format - 'json' 或 'csv'
     * @param {string} market - 'tw', 'us', 或 null (全部)
     */
    async function exportTransactions(format = 'json', market = null) {
        try {
            let url = `/api/portfolio/export?format=${format}`;
            if (market) {
                url += `&market=${market}`;
            }
            
            const res = await apiRequest(url);
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || '匯出失敗');
            }
            
            const blob = await res.blob();
            const filename = res.headers.get('Content-Disposition')?.split('filename=')[1] || `portfolio.${format}`;
            
            // 下載檔案
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
            
            showToast('匯出成功！');
        } catch (e) {
            console.error('匯出交易記錄失敗:', e);
            showToast(e.message || '匯出失敗');
        }
    }
    
    // ============================================================
    // 匯入功能
    // ============================================================
    
    /**
     * 顯示匯入 Modal
     */
    function showImportTransactionsModal() {
        const modal = document.getElementById('importTransactionsModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
        
        // 清空預覽
        const preview = document.getElementById('importTransactionsPreview');
        if (preview) preview.innerHTML = '';
        
        const fileInput = document.getElementById('importTransactionsFile');
        if (fileInput) fileInput.value = '';
    }
    
    /**
     * 隱藏匯入 Modal
     */
    function hideImportTransactionsModal() {
        const modal = document.getElementById('importTransactionsModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }
    
    /**
     * 預覽匯入檔案
     */
    function previewTransactionsFile(input) {
        const file = input.files[0];
        if (!file) return;
        
        const preview = document.getElementById('importTransactionsPreview');
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
                        const values = parseCSVLine(lines[i]);
                        const obj = {};
                        headers.forEach((h, idx) => obj[h] = values[idx]?.trim());
                        if (obj.symbol) items.push(obj);
                    }
                }
                
                // 驗證必要欄位
                const requiredFields = ['symbol', 'market', 'transaction_type', 'quantity', 'price', 'transaction_date'];
                const validItems = items.filter(item => {
                    return requiredFields.every(field => item[field] !== undefined && item[field] !== '');
                });
                
                const invalidCount = items.length - validItems.length;
                
                preview.innerHTML = `
                    <div class="p-3 ${validItems.length > 0 ? 'bg-green-50' : 'bg-red-50'} rounded-lg">
                        <p class="${validItems.length > 0 ? 'text-green-700' : 'text-red-700'} font-medium">
                            <i class="fas fa-${validItems.length > 0 ? 'check' : 'times'}-circle mr-2"></i>
                            找到 ${validItems.length} 筆有效記錄
                            ${invalidCount > 0 ? `<span class="text-orange-600">(${invalidCount} 筆無效)</span>` : ''}
                        </p>
                        ${validItems.length > 0 ? `
                            <div class="mt-2 max-h-40 overflow-y-auto">
                                <table class="text-sm w-full">
                                    <thead>
                                        <tr class="text-gray-500">
                                            <th class="text-left">代號</th>
                                            <th class="text-left">類型</th>
                                            <th class="text-right">數量</th>
                                            <th class="text-right">價格</th>
                                            <th class="text-left">日期</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${validItems.slice(0, 10).map(item => `
                                            <tr class="border-t border-gray-200">
                                                <td>${item.symbol}</td>
                                                <td><span class="px-1.5 py-0.5 rounded text-xs ${item.transaction_type === 'buy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">${item.transaction_type === 'buy' ? '買' : '賣'}</span></td>
                                                <td class="text-right">${item.quantity}</td>
                                                <td class="text-right">${item.price}</td>
                                                <td>${item.transaction_date}</td>
                                            </tr>
                                        `).join('')}
                                        ${validItems.length > 10 ? `
                                            <tr class="border-t border-gray-200">
                                                <td colspan="5" class="text-center text-gray-500">... 還有 ${validItems.length - 10} 筆</td>
                                            </tr>
                                        ` : ''}
                                    </tbody>
                                </table>
                            </div>
                        ` : ''}
                    </div>
                `;
                preview.dataset.items = JSON.stringify(validItems);
            } catch (err) {
                preview.innerHTML = `<p class="text-red-500 p-3"><i class="fas fa-times-circle mr-2"></i>檔案解析失敗: ${err.message}</p>`;
            }
        };
        
        reader.readAsText(file);
    }
    
    /**
     * 解析 CSV 行（處理引號內的逗號）
     */
    function parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(current);
                current = '';
            } else {
                current += char;
            }
        }
        result.push(current);
        
        return result;
    }
    
    /**
     * 執行匯入
     */
    async function importTransactions() {
        const preview = document.getElementById('importTransactionsPreview');
        const itemsStr = preview?.dataset?.items;
        
        if (!itemsStr) {
            showToast('請先選擇檔案');
            return;
        }
        
        try {
            const items = JSON.parse(itemsStr);
            
            if (items.length === 0) {
                showToast('沒有有效的記錄');
                return;
            }
            
            const res = await apiRequest('/api/portfolio/import', {
                method: 'POST',
                body: { items }
            });
            
            const data = await res.json();
            
            if (data.success) {
                showToast(data.message);
                hideImportTransactionsModal();
                
                // 重新載入持股資料
                if (typeof loadPortfolioData === 'function') {
                    loadPortfolioData();
                }
            } else {
                showToast(data.detail || '匯入失敗');
            }
        } catch (e) {
            console.error('匯入交易記錄失敗:', e);
            showToast('匯入失敗');
        }
    }
    
    // ============================================================
    // 切換匯出匯入選單
    // ============================================================
    
    function togglePortfolioMenu() {
        const menu = document.getElementById('portfolioMenu');
        if (menu) menu.classList.toggle('hidden');
    }
    
    // ============================================================
    // 渲染匯出匯入按鈕
    // ============================================================
    
    /**
     * 取得匯出匯入按鈕 HTML
     */
    function getPortfolioExportImportButtons() {
        return `
            <div class="relative">
                <button onclick="togglePortfolioMenu()" class="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg border hover:bg-gray-50" title="匯出匯入">
                    <i class="fas fa-exchange-alt"></i>
                </button>
                <div id="portfolioMenu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-50">
                    <button onclick="exportTransactions('json')" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700 flex items-center">
                        <i class="fas fa-download mr-2 text-blue-500"></i>匯出 JSON
                    </button>
                    <button onclick="exportTransactions('csv')" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700 flex items-center">
                        <i class="fas fa-file-csv mr-2 text-green-500"></i>匯出 CSV
                    </button>
                    <hr class="my-1">
                    <button onclick="exportTransactions('json', 'tw')" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700 flex items-center">
                        <i class="fas fa-download mr-2 text-red-500"></i>僅台股 JSON
                    </button>
                    <button onclick="exportTransactions('json', 'us')" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700 flex items-center">
                        <i class="fas fa-download mr-2 text-blue-500"></i>僅美股 JSON
                    </button>
                    <hr class="my-1">
                    <button onclick="togglePortfolioMenu(); showImportTransactionsModal();" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700 flex items-center">
                        <i class="fas fa-upload mr-2 text-orange-500"></i>匯入記錄
                    </button>
                </div>
            </div>
        `;
    }
    
    // ============================================================
    // 匯入 Modal HTML
    // ============================================================
    
    /**
     * 取得匯入 Modal HTML
     */
    function getImportTransactionsModalHTML() {
        return `
            <div id="importTransactionsModal" class="hidden fixed inset-0 bg-black bg-opacity-50 items-center justify-center z-50">
                <div class="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-bold text-gray-800">
                            <i class="fas fa-upload mr-2 text-orange-500"></i>匯入交易記錄
                        </h3>
                        <button onclick="hideImportTransactionsModal()" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    
                    <div class="mb-4">
                        <p class="text-sm text-gray-600 mb-2">支援 JSON 或 CSV 格式</p>
                        <p class="text-xs text-gray-500 mb-3">
                            必要欄位：symbol, market (tw/us), transaction_type (buy/sell), quantity, price, transaction_date
                        </p>
                        <input type="file" id="importTransactionsFile" accept=".json,.csv" 
                               onchange="previewTransactionsFile(this)"
                               class="w-full px-3 py-2 border rounded-lg">
                    </div>
                    
                    <div id="importTransactionsPreview" class="mb-4"></div>
                    
                    <div class="flex justify-end gap-2">
                        <button onclick="hideImportTransactionsModal()" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                            取消
                        </button>
                        <button onclick="importTransactions()" class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600">
                            <i class="fas fa-upload mr-2"></i>匯入
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    // ============================================================
    // 範例 JSON 格式
    // ============================================================
    
    const EXAMPLE_IMPORT_FORMAT = {
        "items": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "market": "us",
                "transaction_type": "buy",
                "quantity": 10,
                "price": 185.50,
                "fee": 1.99,
                "tax": 0,
                "transaction_date": "2024-01-15",
                "note": "長期投資"
            },
            {
                "symbol": "2330",
                "name": "台積電",
                "market": "tw",
                "transaction_type": "buy",
                "quantity": 1000,
                "price": 580,
                "fee": 20,
                "tax": 0,
                "transaction_date": "2024-01-20",
                "note": ""
            }
        ]
    };
    
    // ============================================================
    // 導出到全域
    // ============================================================
    
    window.exportTransactions = exportTransactions;
    window.showImportTransactionsModal = showImportTransactionsModal;
    window.hideImportTransactionsModal = hideImportTransactionsModal;
    window.previewTransactionsFile = previewTransactionsFile;
    window.importTransactions = importTransactions;
    window.togglePortfolioMenu = togglePortfolioMenu;
    window.getPortfolioExportImportButtons = getPortfolioExportImportButtons;
    window.getImportTransactionsModalHTML = getImportTransactionsModalHTML;
    
})();
