/**
 * 目標價功能修復 v2
 * - 修正 API 路徑: /target -> /target-price
 * - 新增高於/低於方向選擇
 * - 使用全域變數確保正常運作
 */

// 全域變數
window._targetItemId = null;
window._targetDirection = 'above';

// 覆寫 showTargetPriceModal
window.showTargetPriceModal = function(itemId, symbol, currentTarget, direction) {
    console.log('🎯 showTargetPriceModal:', { itemId, symbol, currentTarget, direction });
    
    window._targetItemId = itemId;
    window._targetDirection = direction || 'above';
    
    const modal = document.getElementById('targetPriceModal');
    const symbolEl = document.getElementById('targetPriceSymbol');
    const input = document.getElementById('targetPriceInput');
    const dirAbove = document.getElementById('directionAbove');
    const dirBelow = document.getElementById('directionBelow');
    
    if (symbolEl) symbolEl.textContent = symbol;
    if (input) input.value = currentTarget || '';
    
    // 設定方向 radio（如果存在）
    if (dirAbove) dirAbove.checked = (window._targetDirection === 'above');
    if (dirBelow) dirBelow.checked = (window._targetDirection === 'below');
    
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
    window._targetItemId = null;
};

// 覆寫 saveTargetPrice
window.saveTargetPrice = async function() {
    console.log('🎯 saveTargetPrice called, itemId:', window._targetItemId);
    
    if (!window._targetItemId) {
        console.error('❌ No target item ID');
        if (typeof showToast === 'function') showToast('錯誤：未選擇項目');
        return;
    }
    
    const input = document.getElementById('targetPriceInput');
    const directionEl = document.querySelector('input[name="targetDirection"]:checked');
    const targetPrice = parseFloat(input?.value);
    const direction = directionEl?.value || window._targetDirection || 'above';
    
    console.log('🎯 Saving:', { targetPrice, direction });
    
    if (isNaN(targetPrice) || targetPrice <= 0) {
        if (typeof showToast === 'function') showToast('請輸入有效的目標價');
        return;
    }
    
    try {
        // 🔧 正確的 API 路徑
        const url = `/api/watchlist/${window._targetItemId}/target-price`;
        console.log('🎯 API URL:', url);
        
        const res = await apiRequest(url, {
            method: 'PUT',
            body: { 
                target_price: targetPrice,
                target_direction: direction
            }
        });
        
        const data = await res.json();
        console.log('🎯 API Response:', data);
        
        if (data.success) {
            if (typeof showToast === 'function') showToast('目標價已設定');
            hideTargetPriceModal();
            if (typeof loadWatchlist === 'function') loadWatchlist();
        } else {
            if (typeof showToast === 'function') showToast(data.detail || '設定失敗');
        }
    } catch (e) {
        console.error('🎯 設定目標價失敗:', e);
        if (typeof showToast === 'function') showToast('設定失敗: ' + e.message);
    }
};

// 覆寫 clearTargetPrice
window.clearTargetPrice = async function() {
    console.log('🎯 clearTargetPrice called, itemId:', window._targetItemId);
    
    if (!window._targetItemId) {
        if (typeof showToast === 'function') showToast('錯誤：未選擇項目');
        return;
    }
    
    try {
        const res = await apiRequest(`/api/watchlist/${window._targetItemId}/target-price`, {
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
        console.error('🎯 清除目標價失敗:', e);
        if (typeof showToast === 'function') showToast('清除失敗');
    }
};

console.log('✅ target-price-fix.js v2 已載入');
