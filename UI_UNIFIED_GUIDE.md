# 🔧 SELA UI 統一修復指南

## 問題
點選「報酬率比較」、「後台管理」時會跳轉到獨立頁面，失去導航列。

## 目標
統一 UI 體驗，所有功能都在 dashboard.html 內以 section 方式切換。

---

## 修改 1：側邊欄導航連結

### 電腦版側邊欄 (約第 21875, 21884 行)

**修改前：**
```html
<a href="/static/compare.html" class="nav-link flex items-center px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg">
    <i class="fas fa-trophy mr-3"></i>
    <span>報酬率比較</span>
</a>
...
<a id="adminSidebarLink" href="/static/admin.html" class="hidden flex items-center px-4 py-2 text-orange-500 hover:bg-orange-50 rounded-lg mt-4 border-t pt-4">
    <i class="fas fa-user-shield mr-3"></i>
    <span>管理後台</span>
</a>
```

**修改後：**
```html
<a href="#" onclick="showSection('cagr', event)" class="nav-link flex items-center px-4 py-2 text-gray-600 hover:bg-gray-50 rounded-lg" data-section="cagr">
    <i class="fas fa-trophy mr-3"></i>
    <span>報酬率比較</span>
</a>
...
<a id="adminSidebarLink" href="#" onclick="showSection('admin', event)" class="hidden nav-link flex items-center px-4 py-2 text-orange-500 hover:bg-orange-50 rounded-lg mt-4 border-t pt-4" data-section="admin">
    <i class="fas fa-user-shield mr-3"></i>
    <span>管理後台</span>
</a>
```

### 手機版側邊欄 (約第 21787 行)

**修改前：**
```html
<a href="/static/compare.html" class="mobile-nav-link flex items-center px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg touch-target">
    <i class="fas fa-trophy mr-3 w-5"></i>
    <span>報酬率比較</span>
</a>
```

**修改後：**
```html
<a href="#" onclick="mobileNavTo('cagr')" class="mobile-nav-link flex items-center px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg touch-target" data-section="cagr">
    <i class="fas fa-trophy mr-3 w-5"></i>
    <span>報酬率比較</span>
</a>
```

### 頂部導航的管理員連結 (約第 21832 行)

**修改前：**
```html
<a id="adminLink" href="/static/admin.html" class="text-orange-500 hover:text-orange-600 hidden p-2" title="管理後台">
```

**修改後：**
```html
<a id="adminLink" href="#" onclick="showSection('admin', event)" class="text-orange-500 hover:text-orange-600 hidden p-2" title="管理後台">
```

---

## 修改 2：新增 Section

在 `</main>` 之前（約第 22804 行），在 `section-settings` 之後新增：

```html
            <!-- ===== 報酬率比較區塊 ===== -->
            <section id="section-cagr" class="section hidden">
                <h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">
                    <i class="fas fa-trophy text-yellow-500 mr-2"></i>
                    報酬率比較
                </h2>
                
                <!-- 說明卡片 -->
                <div class="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-lg p-4 md:p-6 mb-4 text-white">
                    <h3 class="text-lg font-bold mb-2">🏆 年化報酬率 (CAGR) 比較器</h3>
                    <p class="text-blue-100 text-sm">比較股票、加密貨幣、指數的長期投資報酬表現，找出最佳投資標的</p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
                    <!-- 左側：選擇標的 -->
                    <div class="lg:col-span-1 space-y-4">
                        <!-- 快速選擇預設組合 -->
                        <div class="bg-white rounded-xl shadow p-4">
                            <h3 class="font-bold text-gray-700 mb-3">🚀 快速比較</h3>
                            <div class="space-y-2" id="cagrPresetList">
                                <button onclick="loadCagrPreset(['AAPL','MSFT','GOOGL','AMZN','META'])" class="w-full text-left px-3 py-2 border rounded-lg hover:bg-gray-50 text-sm">
                                    📱 科技五巨頭
                                </button>
                                <button onclick="loadCagrPreset(['BTC','ETH','SOL'])" class="w-full text-left px-3 py-2 border rounded-lg hover:bg-gray-50 text-sm">
                                    🪙 加密貨幣
                                </button>
                                <button onclick="loadCagrPreset(['^GSPC','^IXIC','^DJI'])" class="w-full text-left px-3 py-2 border rounded-lg hover:bg-gray-50 text-sm">
                                    📊 美國三大指數
                                </button>
                                <button onclick="loadCagrPreset(['2330.TW','2317.TW','2454.TW'])" class="w-full text-left px-3 py-2 border rounded-lg hover:bg-gray-50 text-sm">
                                    🇹🇼 台灣權值股
                                </button>
                            </div>
                        </div>
                        
                        <!-- 自訂標的 -->
                        <div class="bg-white rounded-xl shadow p-4">
                            <h3 class="font-bold text-gray-700 mb-3">🎯 自訂標的</h3>
                            <div class="flex gap-2 mb-3">
                                <input type="text" id="cagrSymbolInput" placeholder="輸入代號 (如 AAPL)" 
                                    class="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-sm"
                                    onkeypress="if(event.key==='Enter')addCagrSymbol()">
                                <button onclick="addCagrSymbol()" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm">
                                    <i class="fas fa-plus"></i>
                                </button>
                            </div>
                            <div id="cagrSymbolTags" class="flex flex-wrap gap-2 mb-3">
                                <!-- 動態生成的標籤 -->
                            </div>
                            <button onclick="compareCagr()" class="w-full py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center justify-center">
                                <i class="fas fa-calculator mr-2"></i>
                                開始比較
                            </button>
                        </div>
                    </div>

                    <!-- 右側：比較結果 -->
                    <div class="lg:col-span-2">
                        <div class="bg-white rounded-xl shadow p-4">
                            <h3 class="font-bold text-gray-700 mb-3">📊 比較結果</h3>
                            <div id="cagrResults">
                                <p class="text-gray-400 text-center py-8">選擇標的後點擊「開始比較」</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ===== 管理後台區塊 ===== -->
            <section id="section-admin" class="section hidden">
                <h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">
                    <i class="fas fa-user-shield text-orange-500 mr-2"></i>
                    管理後台
                </h2>
                
                <!-- 統計卡片 -->
                <div class="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4 mb-4 md:mb-6">
                    <div class="bg-white rounded-lg shadow p-3 md:p-4">
                        <div class="text-gray-500 text-xs md:text-sm">總用戶數</div>
                        <div id="adminStatTotal" class="text-xl md:text-2xl font-bold text-slate-800">-</div>
                    </div>
                    <div class="bg-white rounded-lg shadow p-3 md:p-4">
                        <div class="text-gray-500 text-xs md:text-sm">總登入次數</div>
                        <div id="adminStatTotalLogins" class="text-xl md:text-2xl font-bold text-purple-600">-</div>
                    </div>
                    <div class="bg-white rounded-lg shadow p-3 md:p-4">
                        <div class="text-gray-500 text-xs md:text-sm">今日登入</div>
                        <div id="adminStatToday" class="text-xl md:text-2xl font-bold text-green-600">-</div>
                    </div>
                    <div class="bg-white rounded-lg shadow p-3 md:p-4">
                        <div class="text-gray-500 text-xs md:text-sm">封鎖用戶</div>
                        <div id="adminStatBlocked" class="text-xl md:text-2xl font-bold text-red-600">-</div>
                    </div>
                    <div class="bg-white rounded-lg shadow p-3 md:p-4">
                        <div class="text-gray-500 text-xs md:text-sm">管理員</div>
                        <div id="adminStatAdmin" class="text-xl md:text-2xl font-bold text-blue-600">-</div>
                    </div>
                </div>

                <!-- 系統管理 -->
                <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                    <h3 class="font-bold text-gray-700 mb-4">📊 市場資料管理</h3>
                    <div class="flex flex-wrap gap-2 md:gap-3">
                        <button onclick="adminInitializeData()" class="bg-blue-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center text-sm">
                            <i class="fas fa-sync mr-2"></i>初始化歷史資料
                        </button>
                        <button onclick="adminUpdateIndices()" class="bg-green-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-green-700 flex items-center text-sm">
                            <i class="fas fa-chart-line mr-2"></i>更新三大指數
                        </button>
                        <button onclick="adminUpdateSentiment()" class="bg-purple-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center text-sm">
                            <i class="fas fa-brain mr-2"></i>更新恐懼貪婪
                        </button>
                        <button onclick="adminTriggerDailyUpdate()" class="bg-orange-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-orange-700 flex items-center text-sm">
                            <i class="fas fa-bolt mr-2"></i>執行每日更新
                        </button>
                    </div>
                    <p id="adminSystemMessage" class="mt-3 text-sm text-gray-500"></p>
                </div>

                <!-- 訊號檢查與推播 -->
                <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                    <h3 class="font-bold text-gray-700 mb-4">🔔 訊號檢查與推播</h3>
                    <div class="flex flex-wrap gap-2 md:gap-3 mb-3">
                        <button onclick="adminRunSignalCheck()" class="bg-indigo-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center text-sm">
                            <i class="fas fa-search mr-2"></i>偵測訊號
                        </button>
                        <button onclick="adminSendSignalNotifications()" class="bg-orange-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-orange-700 flex items-center text-sm">
                            <i class="fas fa-paper-plane mr-2"></i>發送訊號通知
                        </button>
                        <button onclick="adminTestLineNotify()" class="bg-green-500 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-green-600 flex items-center text-sm">
                            <i class="fab fa-line mr-2"></i>測試 LINE 推播
                        </button>
                    </div>
                    <div class="flex gap-2 items-center">
                        <input type="text" id="adminTestSymbolInput" placeholder="輸入股票代號測試訊號偵測 (如 AAPL)"
                            class="flex-1 px-3 md:px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 text-sm">
                        <button onclick="adminTestSignalDetection()" class="bg-gray-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-gray-700 text-sm">
                            測試偵測
                        </button>
                    </div>
                    <p id="adminSignalMessage" class="mt-3 text-sm text-gray-500"></p>
                </div>

                <!-- 用戶管理 -->
                <div class="bg-white rounded-xl shadow p-4 md:p-6">
                    <h3 class="font-bold text-gray-700 mb-4">👥 用戶管理</h3>
                    <div class="flex flex-col md:flex-row gap-3 md:gap-4 mb-4">
                        <input type="text" id="adminSearchInput" placeholder="搜尋用戶名稱、Email 或 LINE ID..."
                            class="flex-1 px-3 md:px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm">
                        <div class="flex gap-2 items-center">
                            <label class="flex items-center text-sm">
                                <input type="checkbox" id="adminBlockedOnly" class="mr-2">
                                <span>只顯示封鎖</span>
                            </label>
                            <button onclick="adminLoadUsers()" class="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 text-sm">
                                搜尋
                            </button>
                        </div>
                    </div>
                    <div id="adminUserList" class="overflow-x-auto">
                        <p class="text-gray-400 text-center py-4">點擊搜尋查看用戶列表</p>
                    </div>
                </div>
            </section>
```

---

## 修改 3：新增 JavaScript 函數

在 `<script>` 區塊中新增以下函數：

```javascript
// ========== 報酬率比較功能 ==========
let cagrSymbols = [];

function addCagrSymbol() {
    const input = document.getElementById('cagrSymbolInput');
    const symbol = input.value.trim().toUpperCase();
    if (symbol && !cagrSymbols.includes(symbol) && cagrSymbols.length < 10) {
        cagrSymbols.push(symbol);
        renderCagrTags();
        input.value = '';
    }
}

function removeCagrSymbol(symbol) {
    cagrSymbols = cagrSymbols.filter(s => s !== symbol);
    renderCagrTags();
}

function renderCagrTags() {
    const container = document.getElementById('cagrSymbolTags');
    container.innerHTML = cagrSymbols.map(s => `
        <span class="inline-flex items-center px-3 py-1 bg-gray-100 rounded-full text-sm">
            ${s}
            <button onclick="removeCagrSymbol('${s}')" class="ml-2 text-gray-400 hover:text-red-500">
                <i class="fas fa-times"></i>
            </button>
        </span>
    `).join('');
}

function loadCagrPreset(symbols) {
    cagrSymbols = [...symbols];
    renderCagrTags();
    compareCagr();
}

async function compareCagr() {
    if (cagrSymbols.length === 0) {
        showToast('請先添加要比較的標的', 'warning');
        return;
    }
    
    const resultsDiv = document.getElementById('cagrResults');
    resultsDiv.innerHTML = '<div class="text-center py-8"><i class="fas fa-spinner fa-spin text-2xl text-blue-500"></i><p class="mt-2 text-gray-500">計算中...</p></div>';
    
    try {
        const response = await apiRequest(`/api/cagr/compare?symbols=${cagrSymbols.join(',')}`);
        if (response.success) {
            renderCagrResults(response.data);
        } else {
            resultsDiv.innerHTML = '<p class="text-red-500 text-center py-4">查詢失敗</p>';
        }
    } catch (error) {
        resultsDiv.innerHTML = `<p class="text-red-500 text-center py-4">錯誤: ${error.message}</p>`;
    }
}

function renderCagrResults(data) {
    const resultsDiv = document.getElementById('cagrResults');
    
    // 按 10 年 CAGR 排序
    const sorted = Object.entries(data).sort((a, b) => (b[1].cagr_10y || -999) - (a[1].cagr_10y || -999));
    
    let html = '<div class="space-y-3">';
    sorted.forEach(([symbol, info], index) => {
        const rankClass = index === 0 ? 'bg-yellow-50 border-yellow-300' : 
                         index === 1 ? 'bg-gray-50 border-gray-300' : 
                         index === 2 ? 'bg-orange-50 border-orange-300' : 'bg-white';
        const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`;
        
        html += `
            <div class="p-4 border rounded-lg ${rankClass}">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center">
                        <span class="text-xl mr-2">${medal}</span>
                        <span class="font-bold text-gray-800">${symbol}</span>
                        <span class="text-gray-500 text-sm ml-2">${info.name || ''}</span>
                    </div>
                </div>
                <div class="grid grid-cols-4 gap-2 text-sm">
                    <div>
                        <span class="text-gray-500">1年</span>
                        <div class="${info.cagr_1y >= 0 ? 'text-green-600' : 'text-red-600'} font-medium">
                            ${info.cagr_1y != null ? info.cagr_1y.toFixed(1) + '%' : '-'}
                        </div>
                    </div>
                    <div>
                        <span class="text-gray-500">3年</span>
                        <div class="${info.cagr_3y >= 0 ? 'text-green-600' : 'text-red-600'} font-medium">
                            ${info.cagr_3y != null ? info.cagr_3y.toFixed(1) + '%' : '-'}
                        </div>
                    </div>
                    <div>
                        <span class="text-gray-500">5年</span>
                        <div class="${info.cagr_5y >= 0 ? 'text-green-600' : 'text-red-600'} font-medium">
                            ${info.cagr_5y != null ? info.cagr_5y.toFixed(1) + '%' : '-'}
                        </div>
                    </div>
                    <div>
                        <span class="text-gray-500">10年</span>
                        <div class="${info.cagr_10y >= 0 ? 'text-green-600' : 'text-red-600'} font-bold">
                            ${info.cagr_10y != null ? info.cagr_10y.toFixed(1) + '%' : '-'}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    resultsDiv.innerHTML = html;
}

// ========== 管理後台功能 ==========
async function loadAdminStats() {
    try {
        const response = await apiRequest('/api/admin/users');
        if (response.success) {
            document.getElementById('adminStatTotal').textContent = response.data.length;
            document.getElementById('adminStatBlocked').textContent = response.data.filter(u => u.is_blocked).length;
            document.getElementById('adminStatAdmin').textContent = response.data.filter(u => u.is_admin).length;
            // 今日登入需要額外 API
        }
    } catch (error) {
        console.error('載入管理統計失敗:', error);
    }
}

async function adminInitializeData() {
    showAdminMessage('正在初始化歷史資料...');
    try {
        const response = await apiRequest('/api/admin/initialize', { method: 'POST' });
        showAdminMessage(response.message || '初始化完成', 'success');
    } catch (error) {
        showAdminMessage('初始化失敗: ' + error.message, 'error');
    }
}

async function adminUpdateIndices() {
    showAdminMessage('正在更新三大指數...');
    try {
        const response = await apiRequest('/api/admin/update-indices', { method: 'POST' });
        showAdminMessage(response.message || '更新完成', 'success');
    } catch (error) {
        showAdminMessage('更新失敗: ' + error.message, 'error');
    }
}

async function adminUpdateSentiment() {
    showAdminMessage('正在更新恐懼貪婪指數...');
    try {
        const response = await apiRequest('/api/admin/update-sentiment', { method: 'POST' });
        showAdminMessage(response.message || '更新完成', 'success');
    } catch (error) {
        showAdminMessage('更新失敗: ' + error.message, 'error');
    }
}

async function adminTriggerDailyUpdate() {
    showAdminMessage('正在執行每日更新...');
    try {
        const response = await apiRequest('/api/admin/daily-update', { method: 'POST' });
        showAdminMessage(response.message || '更新完成', 'success');
    } catch (error) {
        showAdminMessage('更新失敗: ' + error.message, 'error');
    }
}

async function adminRunSignalCheck() {
    showAdminSignalMessage('正在偵測訊號...');
    try {
        const response = await apiRequest('/api/admin/signal-check', { method: 'POST' });
        showAdminSignalMessage(response.message || '偵測完成', 'success');
    } catch (error) {
        showAdminSignalMessage('偵測失敗: ' + error.message, 'error');
    }
}

async function adminSendSignalNotifications() {
    showAdminSignalMessage('正在發送通知...');
    try {
        const response = await apiRequest('/api/admin/send-notifications', { method: 'POST' });
        showAdminSignalMessage(response.message || '發送完成', 'success');
    } catch (error) {
        showAdminSignalMessage('發送失敗: ' + error.message, 'error');
    }
}

async function adminTestLineNotify() {
    showAdminSignalMessage('正在測試 LINE 推播...');
    try {
        const response = await apiRequest('/api/admin/test-line', { method: 'POST' });
        showAdminSignalMessage(response.message || '測試完成', 'success');
    } catch (error) {
        showAdminSignalMessage('測試失敗: ' + error.message, 'error');
    }
}

async function adminTestSignalDetection() {
    const symbol = document.getElementById('adminTestSymbolInput').value.trim();
    if (!symbol) {
        showAdminSignalMessage('請輸入股票代號', 'warning');
        return;
    }
    showAdminSignalMessage(`正在測試 ${symbol} 訊號偵測...`);
    try {
        const response = await apiRequest(`/api/admin/test-signal/${symbol}`);
        showAdminSignalMessage(JSON.stringify(response, null, 2), 'success');
    } catch (error) {
        showAdminSignalMessage('測試失敗: ' + error.message, 'error');
    }
}

async function adminLoadUsers() {
    const search = document.getElementById('adminSearchInput').value.trim();
    const blockedOnly = document.getElementById('adminBlockedOnly').checked;
    
    try {
        let url = '/api/admin/users';
        if (search) url += `?search=${encodeURIComponent(search)}`;
        if (blockedOnly) url += (search ? '&' : '?') + 'blocked_only=true';
        
        const response = await apiRequest(url);
        if (response.success) {
            renderAdminUserList(response.data);
        }
    } catch (error) {
        document.getElementById('adminUserList').innerHTML = `<p class="text-red-500 text-center py-4">載入失敗: ${error.message}</p>`;
    }
}

function renderAdminUserList(users) {
    const container = document.getElementById('adminUserList');
    if (users.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-center py-4">沒有找到用戶</p>';
        return;
    }
    
    let html = `
        <table class="w-full text-sm">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-3 py-2 text-left">用戶</th>
                    <th class="px-3 py-2 text-left hidden md:table-cell">Email</th>
                    <th class="px-3 py-2 text-center">狀態</th>
                    <th class="px-3 py-2 text-center">操作</th>
                </tr>
            </thead>
            <tbody class="divide-y">
    `;
    
    users.forEach(user => {
        html += `
            <tr class="${user.is_blocked ? 'bg-red-50' : ''}">
                <td class="px-3 py-2">
                    <div class="flex items-center">
                        <img src="${user.avatar_url || '/static/default-avatar.png'}" class="w-8 h-8 rounded-full mr-2">
                        <span class="font-medium">${user.display_name || user.line_name || '-'}</span>
                    </div>
                </td>
                <td class="px-3 py-2 hidden md:table-cell text-gray-500">${user.email || '-'}</td>
                <td class="px-3 py-2 text-center">
                    ${user.is_admin ? '<span class="px-2 py-1 bg-blue-100 text-blue-600 rounded text-xs">管理員</span>' : ''}
                    ${user.is_blocked ? '<span class="px-2 py-1 bg-red-100 text-red-600 rounded text-xs">封鎖</span>' : '<span class="px-2 py-1 bg-green-100 text-green-600 rounded text-xs">正常</span>'}
                </td>
                <td class="px-3 py-2 text-center">
                    <button onclick="toggleUserBlock(${user.id}, ${!user.is_blocked})" class="px-2 py-1 ${user.is_blocked ? 'bg-green-500' : 'bg-red-500'} text-white rounded text-xs hover:opacity-80">
                        ${user.is_blocked ? '解封' : '封鎖'}
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function toggleUserBlock(userId, block) {
    try {
        await apiRequest(`/api/admin/users/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_blocked: block })
        });
        adminLoadUsers();
        showToast(block ? '用戶已封鎖' : '用戶已解封', 'success');
    } catch (error) {
        showToast('操作失敗: ' + error.message, 'error');
    }
}

function showAdminMessage(msg, type = 'info') {
    const el = document.getElementById('adminSystemMessage');
    el.textContent = msg;
    el.className = `mt-3 text-sm ${type === 'error' ? 'text-red-500' : type === 'success' ? 'text-green-500' : 'text-gray-500'}`;
}

function showAdminSignalMessage(msg, type = 'info') {
    const el = document.getElementById('adminSignalMessage');
    el.textContent = msg;
    el.className = `mt-3 text-sm ${type === 'error' ? 'text-red-500' : type === 'success' ? 'text-green-500' : 'text-gray-500'}`;
}

// 在 showSection 中添加管理後台的載入
// 找到 showSection 函數，在 switch 或 if 判斷中加入：
// case 'admin':
//     loadAdminStats();
//     break;
```

---

## 修改 4：更新 showSection 函數

找到 `showSection` 函數，確保它能處理新的 section：

```javascript
function showSection(name, evt) {
    if (evt) evt.preventDefault();
    
    // 隱藏所有 section
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    
    // 顯示目標 section
    const target = document.getElementById(`section-${name}`);
    if (target) {
        target.classList.remove('hidden');
    }
    
    // 更新導航狀態
    document.querySelectorAll('.nav-link, .mobile-nav-link, .bottom-nav-item').forEach(link => {
        link.classList.remove('bg-blue-50', 'text-gray-700', 'active');
        if (link.dataset.section === name) {
            link.classList.add('bg-blue-50', 'text-gray-700');
            if (link.classList.contains('bottom-nav-item')) {
                link.classList.add('active');
            }
        }
    });
    
    // 載入特定 section 的資料
    switch(name) {
        case 'watchlist':
            loadWatchlist();
            break;
        case 'sentiment':
            loadSentiment();
            break;
        case 'portfolio':
            loadPortfolioData();
            break;
        case 'admin':
            loadAdminStats();
            break;
        // ... 其他 case
    }
    
    // 關閉手機選單
    closeMobileSidebar();
}
```

---

## 驗證

修改完成後，測試以下功能：
1. ✅ 點擊「報酬率比較」→ 保持導航列，只切換內容
2. ✅ 點擊「後台管理」→ 保持導航列，只切換內容
3. ✅ 點擊「設定」→ 保持導航列，只切換內容
4. ✅ 手機版也能正常切換
