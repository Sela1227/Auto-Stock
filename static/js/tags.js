/**
 * 標籤管理模組 (P4 優化版)
 * 
 * 優化內容：
 * 1. AppState 整合 - 統一狀態管理
 * 2. 事件委託 - 減少監聽器數量
 * 3. DOM 快取 - 使用 $() 函數
 * 
 * 包含：標籤 CRUD、追蹤項目標籤關聯、篩選功能
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

    async function loadTags() {
        // ✅ P4: 檢查 AppState 快取
        if (window.AppState && AppState.tagsLoaded && AppState.tags.length > 0) {
            userTags = AppState.tags;
            return userTags;
        }

        try {
            const res = await apiRequest('/api/tags');
            const data = await res.json();
            if (data.success) {
                userTags = data.data || [];

                // ✅ P4: 同步到 AppState
                if (window.AppState) {
                    AppState.setTags(userTags);
                }
            }
            return userTags;
        } catch (e) {
            console.error('載入標籤失敗:', e);
            return [];
        }
    }

    async function createTag(name, color = '#3B82F6', icon = 'fa-tag') {
        try {
            const res = await apiRequest('/api/tags', {
                method: 'POST',
                body: { name, color, icon }
            });
            const data = await res.json();
            if (data.success) {
                showToast('標籤已建立');

                // ✅ P4: 樂觀更新
                if (data.data) {
                    userTags.push(data.data);
                    if (window.AppState) {
                        AppState.setTags([...userTags]);
                    }
                } else {
                    await loadTags();
                }

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

    async function updateTag(tagId, updates) {
        try {
            const res = await apiRequest(`/api/tags/${tagId}`, {
                method: 'PUT',
                body: updates
            });
            const data = await res.json();
            if (data.success) {
                showToast('標籤已更新');

                // ✅ P4: 樂觀更新
                const idx = userTags.findIndex(t => t.id === tagId);
                if (idx !== -1) {
                    userTags[idx] = { ...userTags[idx], ...updates };
                    if (window.AppState) {
                        AppState.setTags([...userTags]);
                    }
                } else {
                    await loadTags();
                }

                renderTagManager();
            } else {
                showToast(data.detail || '更新失敗');
            }
        } catch (e) {
            console.error('更新標籤失敗:', e);
            showToast('更新失敗');
        }
    }

    async function deleteTag(tagId) {
        if (!confirm('確定要刪除此標籤嗎？')) return;
        try {
            const res = await apiRequest(`/api/tags/${tagId}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                showToast('標籤已刪除');

                // ✅ P4: 樂觀更新
                userTags = userTags.filter(t => t.id !== tagId);
                if (window.AppState) {
                    AppState.setTags([...userTags]);
                }

                renderTagManager();
            } else {
                showToast(data.detail || '刪除失敗');
            }
        } catch (e) {
            console.error('刪除標籤失敗:', e);
            showToast('刪除失敗');
        }
    }

    async function initDefaultTags() {
        try {
            const res = await apiRequest('/api/tags/init-defaults', { method: 'POST' });
            const data = await res.json();
            showToast(data.message);
            if (data.success) {
                // 清除快取，強制重新載入
                if (window.AppState) {
                    AppState.set('tagsLoaded', false);
                }
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

    async function setWatchlistTags(watchlistId, tagIds) {
        try {
            const res = await apiRequest(`/api/tags/watchlist/${watchlistId}`, {
                method: 'PUT',
                body: { tag_ids: tagIds }
            });
            const data = await res.json();
            if (data.success) {
                showToast('標籤已更新');
                if (typeof loadWatchlist === 'function') loadWatchlist();
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

    function renderTagManager() {
        const container = $('tagManagerContent');
        if (!container) return;

        if (userTags.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-tags text-4xl text-gray-300 mb-3"></i>
                    <p class="text-gray-500 mb-4">尚無自訂標籤</p>
                    <button data-action="init-defaults" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                        <i class="fas fa-magic mr-2"></i>建立預設標籤
                    </button>
                </div>
            `;
            initTagEventDelegation();
            return;
        }

        // ✅ P4: 使用 data-action 替代 onclick
        container.innerHTML = `
            <div class="flex flex-wrap gap-2 mb-4" id="tagList">
                ${userTags.map(tag => `
                    <div class="flex items-center px-3 py-2 rounded-lg border" style="border-color: ${tag.color}" data-tag-id="${tag.id}">
                        <i class="fas ${tag.icon} mr-2" style="color: ${tag.color}"></i>
                        <span class="font-medium">${tag.name}</span>
                        <button data-action="edit-tag" data-id="${tag.id}" class="ml-2 text-gray-400 hover:text-blue-500">
                            <i class="fas fa-edit text-xs"></i>
                        </button>
                        <button data-action="delete-tag" data-id="${tag.id}" class="ml-1 text-gray-400 hover:text-red-500">
                            <i class="fas fa-times text-xs"></i>
                        </button>
                    </div>
                `).join('')}
            </div>
            <button data-action="create-tag" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                <i class="fas fa-plus mr-2"></i>新增標籤
            </button>
        `;

        initTagEventDelegation();
    }

    function renderTagBadges(tags) {
        if (!tags || tags.length === 0) return '';
        return tags.map(tag => `
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs"
                  style="background-color: ${tag.color}20; color: ${tag.color}">
                <i class="fas ${tag.icon} mr-1 text-xs"></i>${tag.name}
            </span>
        `).join('');
    }

    function renderTagFilter(selectedTagId = null) {
        if (userTags.length === 0) return '';
        // ✅ P4: 使用 data-action 替代 onclick
        return `
            <div class="flex items-center gap-2 mb-4 flex-wrap">
                <span class="text-sm text-gray-500"><i class="fas fa-filter mr-1"></i>篩選:</span>
                <button data-action="filter-tag" data-tag-id="" class="px-3 py-1.5 text-xs rounded-full transition-all ${!selectedTagId ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}">全部</button>
                ${userTags.map(tag => `
                    <button data-action="filter-tag" data-tag-id="${tag.id}"
                            class="px-3 py-1.5 text-xs rounded-full transition-all ${selectedTagId === tag.id ? 'text-white' : 'hover:opacity-80'}"
                            style="background-color: ${selectedTagId === tag.id ? tag.color : tag.color + '30'}; color: ${selectedTagId === tag.id ? 'white' : tag.color}">
                        <i class="fas ${tag.icon} mr-1"></i>${tag.name}
                    </button>
                `).join('')}
            </div>
        `;
    }

    // ============================================================
    // 事件委託 (P4 核心優化)
    // ============================================================

    let delegationInitialized = false;

    function initTagEventDelegation() {
        const container = $('tagManagerContent');
        if (!container || delegationInitialized) return;

        container.addEventListener('click', handleTagClick);
        delegationInitialized = true;
        console.log('📌 標籤管理事件委託已初始化');
    }

    function handleTagClick(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;

        e.preventDefault();
        const action = target.dataset.action;

        switch (action) {
            case 'create-tag':
                showCreateTagModal();
                break;

            case 'edit-tag':
                showEditTagModal(parseInt(target.dataset.id));
                break;

            case 'delete-tag':
                deleteTag(parseInt(target.dataset.id));
                break;

            case 'init-defaults':
                initDefaultTags();
                break;

            case 'filter-tag':
                const tagId = target.dataset.tagId ? parseInt(target.dataset.tagId) : null;
                filterByTag(tagId);
                break;
        }
    }

    // ============================================================
    // 顏色/圖示選擇函數
    // ============================================================

    function selectTagColor(color) {
        const input = $('tagColorInput');
        if (input) input.value = color;

        const buttons = document.querySelectorAll('#tagColorOptions button');
        buttons.forEach(btn => btn.classList.remove('ring-2', 'ring-offset-2'));

        const selectedBtn = Array.from(buttons).find(btn => {
            const onclick = btn.getAttribute('onclick') || btn.getAttribute('data-color');
            return onclick && onclick.includes(color);
        });

        if (!selectedBtn) {
            buttons.forEach(btn => {
                const style = btn.style.backgroundColor;
                if (style) {
                    const rgb = style.match(/\d+/g);
                    if (rgb) {
                        const hex = '#' + rgb.map(x => parseInt(x).toString(16).padStart(2, '0')).join('').toUpperCase();
                        if (hex === color.toUpperCase()) {
                            btn.classList.add('ring-2', 'ring-offset-2');
                            btn.style.setProperty('--tw-ring-color', color);
                        }
                    }
                }
            });
        } else {
            selectedBtn.classList.add('ring-2', 'ring-offset-2');
        }
    }

    function selectTagIcon(icon) {
        const input = $('tagIconInput');
        if (input) input.value = icon;

        const buttons = document.querySelectorAll('#tagIconOptions button');
        buttons.forEach(btn => {
            btn.classList.remove('border-blue-500', 'bg-blue-50', 'text-blue-500', 'border-2');
            btn.classList.add('border', 'border-gray-200', 'text-gray-400');
        });

        const selectedBtn = Array.from(buttons).find(btn => {
            const i = btn.querySelector('i');
            return i && i.classList.contains(icon);
        });

        if (selectedBtn) {
            selectedBtn.classList.remove('border', 'border-gray-200', 'text-gray-400');
            selectedBtn.classList.add('border-2', 'border-blue-500', 'bg-blue-50', 'text-blue-500');
        }
    }

    // ============================================================
    // Modal 控制
    // ============================================================

    function showCreateTagModal() {
        currentEditTagId = null;

        const title = $('tagModalTitle');
        if (title) title.innerHTML = '<i class="fas fa-tag mr-2 text-blue-500"></i>新增標籤';

        const nameInput = $('tagNameInput');
        if (nameInput) nameInput.value = '';

        const colorInput = $('tagColorInput');
        if (colorInput) colorInput.value = '#3B82F6';
        selectTagColor('#3B82F6');

        const iconInput = $('tagIconInput');
        if (iconInput) iconInput.value = 'fa-tag';
        selectTagIcon('fa-tag');

        const modal = $('tagEditModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            if (nameInput) nameInput.focus();
        }
    }

    function showEditTagModal(tagId) {
        const tag = userTags.find(t => t.id === tagId);
        if (!tag) return;

        currentEditTagId = tagId;

        const title = $('tagModalTitle');
        if (title) title.innerHTML = '<i class="fas fa-tag mr-2 text-blue-500"></i>編輯標籤';

        const nameInput = $('tagNameInput');
        if (nameInput) nameInput.value = tag.name;

        const colorInput = $('tagColorInput');
        if (colorInput) colorInput.value = tag.color;
        selectTagColor(tag.color);

        const iconInput = $('tagIconInput');
        if (iconInput) iconInput.value = tag.icon;
        selectTagIcon(tag.icon);

        const modal = $('tagEditModal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    function hideTagEditModal() {
        const modal = $('tagEditModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        currentEditTagId = null;
    }

    async function saveTagFromModal() {
        const name = $('tagNameInput')?.value?.trim();
        const color = $('tagColorInput')?.value || '#3B82F6';
        const icon = $('tagIconInput')?.value || 'fa-tag';

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

    // ============================================================
    // 指派標籤 Modal
    // ============================================================

    function showAssignTagModal(watchlistId, symbol) {
        currentAssignWatchlistId = watchlistId;
        const modal = $('assignTagModal');
        const symbolEl = $('assignTagSymbol');
        const container = $('assignTagList');

        if (symbolEl) symbolEl.textContent = symbol;
        if (container) container.innerHTML = '<p class="text-gray-400 text-center">載入中...</p>';

        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
        loadAssignTagList(watchlistId);
    }

    async function loadAssignTagList(watchlistId) {
        const container = $('assignTagList');
        if (!container) return;

        const currentTags = await getWatchlistTags(watchlistId);
        const currentTagIds = new Set(currentTags.map(t => t.id));

        if (userTags.length === 0) {
            container.innerHTML = `
                <p class="text-gray-500 text-center py-4">尚無標籤</p>
                <button data-action="goto-create-tag" class="w-full py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200">
                    <i class="fas fa-plus mr-2"></i>建立標籤
                </button>
            `;
            return;
        }

        container.innerHTML = userTags.map(tag => `
            <label class="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input type="checkbox" class="assign-tag-checkbox w-5 h-5 rounded" value="${tag.id}" ${currentTagIds.has(tag.id) ? 'checked' : ''}>
                <i class="fas ${tag.icon} ml-3 mr-2" style="color: ${tag.color}"></i>
                <span>${tag.name}</span>
            </label>
        `).join('');
    }

    function hideAssignTagModal() {
        const modal = $('assignTagModal');
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
        if (typeof loadWatchlist === 'function') loadWatchlist();
    }

    function getFilterTagId() {
        return currentFilterTagId;
    }

    function setFilterTagId(tagId) {
        currentFilterTagId = tagId;
    }

    // ============================================================
    // 導出
    // ============================================================

    // 掛載到 SELA 命名空間
    if (window.SELA) {
        window.SELA.tags = {
            load: loadTags,
            create: createTag,
            update: updateTag,
            delete: deleteTag,
            initDefaults: initDefaultTags,
            getWatchlistTags,
            setWatchlistTags,
            renderBadges: renderTagBadges,
            renderFilter: renderTagFilter,
            renderManager: renderTagManager,
            getFilterId: getFilterTagId,
            setFilterId: setFilterTagId
        };
    }

    // 全域導出（向後兼容）
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
    window.setFilterTagId = setFilterTagId;
    window.userTags = userTags;
    window.selectTagColor = selectTagColor;
    window.selectTagIcon = selectTagIcon;

    console.log('🏷️ tags.js 模組已載入 (P4 優化版)');
})();
