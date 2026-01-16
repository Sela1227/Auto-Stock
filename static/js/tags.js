/**
 * 標籤管理模組
 * P1 功能：追蹤清單分組 Tag
 * 
 * 🔧 修復版本 - 2026-01-16
 * - 新增 selectTagColor 函數
 * - 新增 selectTagIcon 函數
 */

(function() {
    'use strict';
    
    // ============================================================
    // 私有變數
    // ============================================================
    
    let userTags = [];
    let currentEditTagId = null;
    let currentAssignWatchlistId = null;
    let currentFilterTagId = null;
    
    // ============================================================
    // 標籤 CRUD
    // ============================================================
    
    /**
     * 載入用戶標籤
     */
    async function loadTags() {
        try {
            const res = await apiRequest('/api/tags');
            const data = await res.json();
            
            if (data.success) {
                userTags = data.data || [];
            }
            
            return userTags;
        } catch (e) {
            console.error('載入標籤失敗:', e);
            return [];
        }
    }
    
    /**
     * 建立標籤
     */
    async function createTag(name, color = '#3B82F6', icon = 'fa-tag') {
        try {
            const res = await apiRequest('/api/tags', {
                method: 'POST',
                body: { name, color, icon }
            });
            const data = await res.json();
            
            if (data.success) {
                showToast('標籤已建立');
                await loadTags();
                renderTagManager();
                return data.data;
            } else {
                showToast(data.detail || '建立失敗');
                return null;
            }
        } catch (e) {
            console.error('建立標籤失敗:', e);
            showToast('建立失敗');
            return null;
        }
    }
    
    /**
     * 更新標籤
     */
    async function updateTag(tagId, updates) {
        try {
            const res = await apiRequest(`/api/tags/${tagId}`, {
                method: 'PUT',
                body: updates
            });
            const data = await res.json();
            
            if (data.success) {
                showToast('標籤已更新');
                await loadTags();
                renderTagManager();
            } else {
                showToast(data.detail || '更新失敗');
            }
        } catch (e) {
            console.error('更新標籤失敗:', e);
            showToast('更新失敗');
        }
    }
    
    /**
     * 刪除標籤
     */
    async function deleteTag(tagId) {
        if (!confirm('確定要刪除此標籤嗎？')) return;
        
        try {
            const res = await apiRequest(`/api/tags/${tagId}`, {
                method: 'DELETE'
            });
            const data = await res.json();
            
            if (data.success) {
                showToast('標籤已刪除');
                await loadTags();
                renderTagManager();
            } else {
                showToast(data.detail || '刪除失敗');
            }
        } catch (e) {
            console.error('刪除標籤失敗:', e);
            showToast('刪除失敗');
        }
    }
    
    /**
     * 初始化預設標籤
     */
    async function initDefaultTags() {
        try {
            const res = await apiRequest('/api/tags/init-defaults', {
                method: 'POST'
            });
            const data = await res.json();
            
            showToast(data.message);
            
            if (data.success) {
                await loadTags();
                renderTagManager();
            }
        } catch (e) {
            console.error('初始化標籤失敗:', e);
            showToast('初始化失敗');
        }
    }
    
    // ============================================================
    // 追蹤項目標籤管理
    // ============================================================
    
    /**
     * 取得追蹤項目的標籤
     */
    async function getWatchlistTags(watchlistId) {
        try {
            const res = await apiRequest(`/api/tags/watchlist/${watchlistId}`);
            const data = await res.json();
            return data.success ? data.tags : [];
        } catch (e) {
            console.error('取得標籤失敗:', e);
            return [];
        }
    }
    
    /**
     * 設定追蹤項目的標籤
     */
    async function setWatchlistTags(watchlistId, tagIds) {
        try {
            const res = await apiRequest(`/api/tags/watchlist/${watchlistId}`, {
                method: 'PUT',
                body: { tag_ids: tagIds }
            });
            const data = await res.json();
            
            if (data.success) {
                showToast('標籤已更新');
                // 重新載入追蹤清單
                if (typeof loadWatchlist === 'function') {
                    loadWatchlist();
                }
            } else {
                showToast(data.detail || '更新失敗');
            }
        } catch (e) {
            console.error('設定標籤失敗:', e);
            showToast('更新失敗');
        }
    }
    
    // ============================================================
    // UI 渲染
    // ============================================================
    
    /**
     * 渲染標籤管理區塊
     */
    function renderTagManager() {
        const container = document.getElementById('tagManagerContent');
        if (!container) return;
        
        if (userTags.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-tags text-4xl text-gray-300 mb-3"></i>
                    <p class="text-gray-500 mb-4">尚無自訂標籤</p>
                    <button onclick="initDefaultTags()" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                        <i class="fas fa-magic mr-2"></i>建立預設標籤
                    </button>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="flex flex-wrap gap-2 mb-4">
                ${userTags.map(tag => `
                    <div class="flex items-center px-3 py-2 rounded-lg border" style="border-color: ${tag.color}">
                        <i class="fas ${tag.icon} mr-2" style="color: ${tag.color}"></i>
                        <span class="font-medium">${tag.name}</span>
                        <button onclick="showEditTagModal(${tag.id})" class="ml-2 text-gray-400 hover:text-blue-500">
                            <i class="fas fa-edit text-xs"></i>
                        </button>
                        <button onclick="deleteTag(${tag.id})" class="ml-1 text-gray-400 hover:text-red-500">
                            <i class="fas fa-times text-xs"></i>
                        </button>
                    </div>
                `).join('')}
            </div>
            <button onclick="showCreateTagModal()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                <i class="fas fa-plus mr-2"></i>新增標籤
            </button>
        `;
        
        container.innerHTML = html;
    }
    
    /**
     * 渲染標籤 badges
     */
    function renderTagBadges(tags) {
        if (!tags || tags.length === 0) return '';
        
        return tags.map(tag => `
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs" 
                  style="background-color: ${tag.color}20; color: ${tag.color}">
                <i class="fas ${tag.icon} mr-1 text-xs"></i>${tag.name}
            </span>
        `).join('');
    }
    
    /**
     * 渲染標籤篩選器
     */
    function renderTagFilter(selectedTagId = null) {
        if (userTags.length === 0) return '';
        
        return `
            <div class="flex items-center gap-2 mb-4 flex-wrap">
                <span class="text-sm text-gray-500"><i class="fas fa-filter mr-1"></i>篩選:</span>
                <button onclick="filterByTag(null)" class="px-3 py-1.5 text-xs rounded-full transition-all ${!selectedTagId ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}">
                    全部
                </button>
                ${userTags.map(tag => `
                    <button onclick="filterByTag(${tag.id})" 
                            class="px-3 py-1.5 text-xs rounded-full transition-all ${selectedTagId === tag.id ? 'text-white' : 'hover:opacity-80'}"
                            style="background-color: ${selectedTagId === tag.id ? tag.color : tag.color + '30'}; color: ${selectedTagId === tag.id ? 'white' : tag.color}">
                        <i class="fas ${tag.icon} mr-1"></i>${tag.name}
                    </button>
                `).join('')}
            </div>
        `;
    }
    
    // ============================================================
    // 🆕 顏色/圖示選擇函數（修復新增）
    // ============================================================
    
    /**
     * 選擇標籤顏色
     * 點擊顏色圓圈時呼叫，更新 hidden input 並高亮選中的顏色
     */
    function selectTagColor(color) {
        // 1. 更新 hidden input 的值
        const input = document.getElementById('tagColorInput');
        if (input) input.value = color;
        
        // 2. 清除所有按鈕的選中樣式
        const buttons = document.querySelectorAll('#tagColorOptions button');
        buttons.forEach(btn => {
            btn.classList.remove('ring-2', 'ring-offset-2');
        });
        
        // 3. 找到對應顏色的按鈕並加上選中樣式
        const hexToRgb = (hex) => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result 
                ? `rgb(${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)})` 
                : null;
        };
        
        buttons.forEach(btn => {
            const computedColor = window.getComputedStyle(btn).backgroundColor;
            if (computedColor === hexToRgb(color)) {
                btn.classList.add('ring-2', 'ring-offset-2');
            }
        });
    }

    /**
     * 選擇標籤圖示
     * 點擊圖示按鈕時呼叫，更新 hidden input 並高亮選中的圖示
     */
    function selectTagIcon(icon) {
        // 1. 更新 hidden input 的值
        const input = document.getElementById('tagIconInput');
        if (input) input.value = icon;
        
        // 2. 清除所有按鈕的選中樣式
        document.querySelectorAll('#tagIconOptions button').forEach(btn => {
            btn.classList.remove('border-2', 'border-blue-500', 'bg-blue-50', 'text-blue-500');
            btn.classList.add('border', 'border-gray-200', 'text-gray-400');
        });
        
        // 3. 找到對應圖示的按鈕並加上選中樣式
        document.querySelectorAll('#tagIconOptions button').forEach(btn => {
            const iconEl = btn.querySelector('i');
            if (iconEl && iconEl.classList.contains(icon)) {
                btn.classList.remove('border', 'border-gray-200', 'text-gray-400');
                btn.classList.add('border-2', 'border-blue-500', 'bg-blue-50', 'text-blue-500');
            }
        });
    }
    
    // ============================================================
    // Modal 控制
    // ============================================================
    
    function showCreateTagModal() {
        currentEditTagId = null;
        const modal = document.getElementById('tagEditModal');
        const title = document.getElementById('tagModalTitle');
        const nameInput = document.getElementById('tagNameInput');
        const colorInput = document.getElementById('tagColorInput');
        const iconInput = document.getElementById('tagIconInput');
        
        if (title) title.textContent = '新增標籤';
        if (nameInput) nameInput.value = '';
        if (colorInput) colorInput.value = '#3B82F6';
        if (iconInput) iconInput.value = 'fa-tag';
        
        // 重置顏色選擇器的視覺狀態
        selectTagColor('#3B82F6');
        selectTagIcon('fa-tag');
        
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }
    
    function showEditTagModal(tagId) {
        currentEditTagId = tagId;
        const tag = userTags.find(t => t.id === tagId);
        if (!tag) return;
        
        const modal = document.getElementById('tagEditModal');
        const title = document.getElementById('tagModalTitle');
        const nameInput = document.getElementById('tagNameInput');
        const colorInput = document.getElementById('tagColorInput');
        const iconInput = document.getElementById('tagIconInput');
        
        if (title) title.textContent = '編輯標籤';
        if (nameInput) nameInput.value = tag.name;
        if (colorInput) colorInput.value = tag.color;
        if (iconInput) iconInput.value = tag.icon;
        
        // 設定顏色選擇器的視覺狀態
        selectTagColor(tag.color);
        selectTagIcon(tag.icon);
        
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }
    
    function hideTagEditModal() {
        const modal = document.getElementById('tagEditModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        currentEditTagId = null;
    }
    
    async function saveTagFromModal() {
        const nameInput = document.getElementById('tagNameInput');
        const colorInput = document.getElementById('tagColorInput');
        const iconInput = document.getElementById('tagIconInput');
        
        const name = nameInput?.value?.trim();
        const color = colorInput?.value || '#3B82F6';
        const icon = iconInput?.value || 'fa-tag';
        
        if (!name) {
            showToast('請輸入標籤名稱');
            return;
        }
        
        if (currentEditTagId) {
            await updateTag(currentEditTagId, { name, color, icon });
        } else {
            await createTag(name, color, icon);
        }
        
        hideTagEditModal();
    }
    
    /**
     * 顯示標籤指派 Modal
     */
    function showAssignTagModal(watchlistId, symbol) {
        currentAssignWatchlistId = watchlistId;
        
        const modal = document.getElementById('assignTagModal');
        const symbolEl = document.getElementById('assignTagSymbol');
        const container = document.getElementById('assignTagList');
        
        if (symbolEl) symbolEl.textContent = symbol;
        
        if (container) {
            container.innerHTML = '<p class="text-gray-400 text-center">載入中...</p>';
        }
        
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
        
        // 載入當前標籤
        loadAssignTagList(watchlistId);
    }
    
    async function loadAssignTagList(watchlistId) {
        const container = document.getElementById('assignTagList');
        if (!container) return;
        
        // 取得當前標籤
        const currentTags = await getWatchlistTags(watchlistId);
        const currentTagIds = new Set(currentTags.map(t => t.id));
        
        if (userTags.length === 0) {
            container.innerHTML = `
                <p class="text-gray-500 text-center py-4">尚無標籤</p>
                <button onclick="hideAssignTagModal(); showCreateTagModal();" class="w-full py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200">
                    <i class="fas fa-plus mr-2"></i>建立標籤
                </button>
            `;
            return;
        }
        
        container.innerHTML = userTags.map(tag => `
            <label class="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input type="checkbox" class="assign-tag-checkbox w-5 h-5 rounded" 
                       value="${tag.id}" ${currentTagIds.has(tag.id) ? 'checked' : ''}>
                <i class="fas ${tag.icon} ml-3 mr-2" style="color: ${tag.color}"></i>
                <span>${tag.name}</span>
            </label>
        `).join('');
    }
    
    function hideAssignTagModal() {
        const modal = document.getElementById('assignTagModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        currentAssignWatchlistId = null;
    }
    
    async function saveAssignedTags() {
        if (!currentAssignWatchlistId) return;
        
        const checkboxes = document.querySelectorAll('.assign-tag-checkbox:checked');
        const tagIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
        
        await setWatchlistTags(currentAssignWatchlistId, tagIds);
        hideAssignTagModal();
    }
    
    // ============================================================
    // 篩選功能
    // ============================================================
    
    function filterByTag(tagId) {
        currentFilterTagId = tagId;
        
        // 重新載入追蹤清單（帶篩選）
        if (typeof loadWatchlist === 'function') {
            loadWatchlist();
        }
    }
    
    function getFilterTagId() {
        return currentFilterTagId;
    }
    
    // ============================================================
    // 導出到全域
    // ============================================================
    
    window.loadTags = loadTags;
    window.createTag = createTag;
    window.updateTag = updateTag;
    window.deleteTag = deleteTag;
    window.initDefaultTags = initDefaultTags;
    window.getWatchlistTags = getWatchlistTags;
    window.setWatchlistTags = setWatchlistTags;
    window.renderTagBadges = renderTagBadges;
    window.renderTagFilter = renderTagFilter;
    window.renderTagManager = renderTagManager;
    window.showCreateTagModal = showCreateTagModal;
    window.showEditTagModal = showEditTagModal;
    window.hideTagEditModal = hideTagEditModal;
    window.saveTagFromModal = saveTagFromModal;
    window.showAssignTagModal = showAssignTagModal;
    window.hideAssignTagModal = hideAssignTagModal;
    window.saveAssignedTags = saveAssignedTags;
    window.filterByTag = filterByTag;
    window.getFilterTagId = getFilterTagId;
    window.userTags = userTags;
    
    // 🆕 新增：暴露顏色/圖示選擇函數
    window.selectTagColor = selectTagColor;
    window.selectTagIcon = selectTagIcon;
    
    console.log('🏷️ tags.js 模組已載入（含選色/選圖示功能）');
})();
