/**
 * 目標價功能修復 (獨立模組)
 * 解決 API 路徑錯誤 + 新增高於/低於方向
 * 
 * 將此檔案放到 static/js/target-price-fix.js
 * 並在 dashboard.html 的 </body> 前引入
 */
(function() {
    'use strict';
    
    let currentTargetItemId = null;
    
    // 覆寫 showTargetPriceModal
    window.showTargetPriceModal = function(itemId, symbol, currentTarget, direction) {
        currentTargetItemId = itemId;
        
        const modal = document.getElementById('targetPriceModal');
        const symbolEl = document.getElementById('targetPriceSymbol');
        const input = document.getElementById('targetPriceInput');
        const dirAbove = document.getElementById('directionAbove');
        const dirBelow = document.getElementById('directionBelow');
        
        if (symbolEl) symbolEl.textContent = symbol;
        if (input) input.value = currentTarget || '';
        
        // 設定方向 radio
        const dir = direction || 'above';
        if (dirAbove) dirAbove.checked = (dir === 'above');
        if (dirBelow) dirBelow.checked = (dir === 'below');
        
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            if (input) setTimeout(() => input.focus(), 100);
        }
    };
    
    // 覆寫 hideTargetPriceModal
    window.hideTargetPriceModal = function() {
        const modal = document.getElementById('targetPriceModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        currentTargetItemId = null;
    };
    
    // 覆寫 saveTargetPrice - 修正 API 路徑
    window.saveTargetPrice = async function() {
        if (!currentTargetItemId) return;
        
        const input = document.getElementById('targetPriceInput');
        const directionEl = document.querySelector('input[name="targetDirection"]:checked');
        const targetPrice = parseFloat(input?.value);
        const direction = directionEl?.value || 'above';
        
        if (isNaN(targetPrice) || targetPrice <= 0) {
            if (typeof showToast === 'function') showToast('請輸入有效的目標價');
            return;
        }
        
        try {
            // 🔧 關鍵修正: 使用 target-price 而非 target
            const res = await apiRequest(`/api/watchlist/${currentTargetItemId}/target-price`, {
                method: 'PUT',
                body: { 
                    target_price: targetPrice,
                    target_direction: direction
                }
            });
            
            const data = await res.json();
            
            if (data.success) {
                if (typeof showToast === 'function') showToast('目標價已設定');
                hideTargetPriceModal();
                if (typeof loadWatchlist === 'function') loadWatchlist();
            } else {
                if (typeof showToast === 'function') showToast(data.detail || '設定失敗');
            }
        } catch (e) {
            console.error('設定目標價失敗:', e);
            if (typeof showToast === 'function') showToast('設定失敗: ' + e.message);
        }
    };
    
    // 覆寫 clearTargetPrice
    window.clearTargetPrice = async function() {
        if (!currentTargetItemId) return;
        
        try {
            const res = await apiRequest(`/api/watchlist/${currentTargetItemId}/target-price`, {
                method: 'PUT',
                body: { target_price: null, target_direction: null }
            });
            
            const data = await res.json();
            
            if (data.success) {
                if (typeof showToast === 'function') showToast('已清除目標價');
                hideTargetPriceModal();
                if (typeof loadWatchlist === 'function') loadWatchlist();
            } else {
                if (typeof showToast === 'function') showToast(data.detail || '清除失敗');
            }
        } catch (e) {
            console.error('清除目標價失敗:', e);
            if (typeof showToast === 'function') showToast('清除失敗');
        }
    };
    
    console.log('🎯 target-price-fix.js 已載入 (修正 API 路徑 + 高於/低於方向)');
})();
