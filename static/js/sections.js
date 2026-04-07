/**
 * Section 內容動態生成模組
 * 將所有 section HTML 從 dashboard.html 移出
 */
(function() {
    'use strict';

    // 輔助函數
    function renderIndexCard(symbol, name, id, color, icon) {
        return `<div class="bg-white rounded-xl shadow p-4 cursor-pointer hover:shadow-lg transition-shadow" onclick="openIndexModal('${symbol}', '${name}')">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-${color}-100 rounded-lg flex items-center justify-center mr-3"><i class="fas ${icon} text-${color}-600"></i></div>
                    <div><h3 class="font-semibold text-gray-700 text-sm">${name}</h3><p class="text-xs text-gray-400">${symbol}</p></div>
                </div>
                <i class="fas fa-chart-area text-gray-300"></i>
            </div>
            <div class="flex items-baseline justify-between">
                <span id="index-${id}-price" class="text-xl font-bold text-gray-800">--</span>
                <span id="index-${id}-change" class="text-sm font-medium">--</span>
            </div>
            <p id="index-${id}-date" class="text-xs text-gray-400 mt-1"></p>
        </div>`;
    }

    function renderGauge(type, title, iconClass, color) {
        return `<div class="bg-white rounded-xl shadow p-4 md:p-6 cursor-pointer hover:shadow-lg transition-shadow" onclick="openSentimentModal('${type}', '${title}')">
            <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold text-gray-700 text-sm md:text-base"><i class="${iconClass} mr-2 text-${color}-500"></i>${title}</h3>
                <i class="fas fa-chart-area text-gray-300"></i>
            </div>
            <div class="fear-greed-gauge" id="${type}Gauge">
                <svg viewBox="0 0 200 115" class="gauge-svg">
                    <path class="gauge-arc gauge-arc-extreme-fear" d="M 20 100 A 80 80 0 0 1 38 62" />
                    <path class="gauge-arc gauge-arc-fear" d="M 38 62 A 80 80 0 0 1 75 32" />
                    <path class="gauge-arc gauge-arc-neutral" d="M 75 32 A 80 80 0 0 1 125 32" />
                    <path class="gauge-arc gauge-arc-greed" d="M 125 32 A 80 80 0 0 1 162 62" />
                    <path class="gauge-arc gauge-arc-extreme-greed" d="M 162 62 A 80 80 0 0 1 180 100" />
                    <text x="8" y="105" class="gauge-tick-text">0</text>
                    <text x="96" y="12" class="gauge-tick-text" text-anchor="middle">50</text>
                    <text x="188" y="105" class="gauge-tick-text">100</text>
                    <g id="${type}NeedleGroup" class="gauge-needle-group"><polygon class="gauge-needle" points="100,25 97,100 103,100" /></g>
                    <circle class="gauge-center-dot" cx="100" cy="100" r="6" />
                </svg>
            </div>
            <div class="text-center mt-2"><span id="${type}GaugeValue" class="text-4xl font-bold text-gray-800">--</span></div>
            <p id="${type}SentimentStatus" class="text-center font-semibold text-lg mt-1"></p>
            <p id="${type}SentimentTime" class="text-xs text-gray-400 text-center mt-1"></p>
            <p class="text-xs text-blue-500 text-center mt-2"><i class="fas fa-chart-line mr-1"></i>點擊查看走勢</p>
        </div>`;
    }

    const SECTION_TEMPLATES = {
        dashboard: `<h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">儀表板</h2>
            <div class="mb-4 md:mb-6">
                <div id="btc-price-card" class="bg-gradient-to-br from-orange-500 to-yellow-500 rounded-xl p-4 md:p-5 text-white shadow-lg cursor-pointer hover:shadow-xl transition-all duration-300" onclick="showSection('search', event); setTimeout(() => { document.getElementById('searchSymbol').value='BTC'; searchStock(); }, 100);">
                    <div class="flex items-center justify-between">
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center space-x-2 mb-1"><i class="fab fa-bitcoin text-xl"></i><span class="text-sm font-medium opacity-90">Bitcoin</span></div>
                            <div class="text-2xl md:text-3xl font-bold truncate" id="btc-price">$--,---</div>
                        </div>
                        <div class="text-right flex-shrink-0 ml-3">
                            <div class="text-lg md:text-xl font-semibold" id="btc-change">--%</div>
                            <div class="text-xs opacity-75">24h</div>
                        </div>
                        <div class="ml-3 opacity-20"><i class="fab fa-bitcoin text-5xl md:text-6xl"></i></div>
                    </div>
                </div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4 md:mb-6">
                ${renderIndexCard('^GSPC', 'S&P 500', 'GSPC', 'blue', 'fa-chart-line')}
                ${renderIndexCard('^DJI', '道瓊工業', 'DJI', 'green', 'fa-industry')}
                ${renderIndexCard('^IXIC', '納斯達克', 'IXIC', 'purple', 'fa-microchip')}
                ${renderIndexCard('^TWII', '台股加權', 'TWII', 'red', 'fa-landmark')}
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-4 md:mb-6">
                ${renderGauge('stock', '美股恐懼貪婪指數', 'fas fa-flag-usa', 'blue')}
                ${renderGauge('crypto', '幣圈恐懼貪婪指數', 'fab fa-bitcoin', 'orange')}
            </div>
            <div class="bg-white rounded-xl shadow p-4 md:p-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-semibold text-gray-700">追蹤清單</h3>
                    <a href="#" onclick="showSection('watchlist')" class="text-blue-600 text-sm hover:underline">查看全部</a>
                </div>
                <div id="dashboardWatchlist"><p class="text-gray-500 text-center py-4">載入中...</p></div>
            </div>`,

        search: `<h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">股票查詢</h2>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4 md:mb-6">
                <div class="flex flex-col sm:flex-row gap-3">
                    <input type="text" id="searchSymbol" placeholder="輸入股票代號（如 AAPL、2330）" class="flex-1 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 text-base" onkeypress="if(event.key==='Enter')searchStock()">
                    <button onclick="searchStock()" class="brand-orange text-white px-6 py-3 rounded-lg font-medium flex items-center justify-center touch-target"><i class="fas fa-search mr-2"></i><span>查詢</span></button>
                </div>
                <p class="text-gray-500 text-xs md:text-sm mt-2">支援美股、台股 (輸入純數字如 2330) 及加密貨幣 (BTC, ETH)</p>
            </div>
            <div id="searchResult" class="hidden"></div>`,

        watchlist: `<div class="flex items-center justify-between mb-4 md:mb-6">
                <h2 class="text-xl md:text-2xl font-bold text-gray-800">追蹤清單</h2>
                <div class="flex items-center gap-2">
                    <div class="relative">
                        <button onclick="toggleWatchlistMenu()" class="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg border hover:bg-gray-50" title="匯出匯入"><i class="fas fa-exchange-alt"></i></button>
                        <div id="watchlistMenu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-50">
                            <button onclick="exportWatchlist('json')" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700 flex items-center"><i class="fas fa-download mr-2 text-blue-500"></i>匯出 JSON</button>
                            <button onclick="exportWatchlist('csv')" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700 flex items-center"><i class="fas fa-file-csv mr-2 text-green-500"></i>匯出 CSV</button>
                            <hr class="my-1">
                            <button onclick="showImportWatchlistModal()" class="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm text-gray-700 flex items-center"><i class="fas fa-upload mr-2 text-orange-500"></i>匯入清單</button>
                        </div>
                    </div>
                    <button onclick="showAddWatchlistModal()" class="brand-orange text-white px-4 py-2 rounded-lg font-medium flex items-center touch-target"><i class="fas fa-plus mr-2"></i><span class="hidden sm:inline">新增</span></button>
                </div>
            </div>
            <div id="watchlistContent"><p class="text-gray-500 text-center py-4">載入中...</p></div>`,

        sentiment: `<h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">恐懼貪婪指數</h2>
            <div id="sentimentContent"><p class="text-gray-500 text-center py-4">載入中...</p></div>`,

        compare: `<h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">走勢比較</h2>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-plus-circle mr-2 text-blue-500"></i>選擇比較標的</h3>
                <p class="text-gray-500 text-sm mb-4">輸入股票代號或指數（最多 5 個），以逗號分隔</p>
                <div class="mb-4"><span class="text-sm text-gray-600 mr-2">快速選擇：</span>
                    <button onclick="addCompareSymbol('^GSPC')" class="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded mr-1 mb-1">S&P 500</button>
                    <button onclick="addCompareSymbol('^DJI')" class="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded mr-1 mb-1">道瓊</button>
                    <button onclick="addCompareSymbol('AAPL')" class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded mr-1 mb-1">AAPL</button>
                    <button onclick="addCompareSymbol('MSFT')" class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded mr-1 mb-1">MSFT</button>
                    <button onclick="addCompareSymbol('2330.TW')" class="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 rounded mr-1 mb-1">台積電</button>
                    <button onclick="addCompareSymbol('BTC-USD')" class="px-2 py-1 text-xs bg-yellow-100 hover:bg-yellow-200 rounded mr-1 mb-1">BTC</button>
                </div>
                <div class="flex flex-col md:flex-row gap-3">
                    <input type="text" id="compareSymbols" placeholder="例: AAPL, MSFT, ^GSPC" class="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500">
                    <select id="compareDays" class="px-4 py-2 border rounded-lg bg-white">
                        <option value="30">1 個月</option><option value="90" selected>3 個月</option><option value="180">6 個月</option><option value="365">1 年</option>
                    </select>
                    <button onclick="loadCompareChart()" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"><i class="fas fa-chart-line mr-2"></i>比較</button>
                </div>
                <div id="selectedSymbols" class="flex flex-wrap gap-2 mt-3"></div>
            </div>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <div id="compareChartContainer" class="hidden">
                    <div class="flex items-center justify-between mb-4"><h3 class="font-semibold text-gray-700"><i class="fas fa-chart-line mr-2 text-green-500"></i>走勢比較圖</h3><span class="text-sm text-gray-500">起始日 = 100%</span></div>
                    <div class="relative" style="height: 400px;"><canvas id="compareChart"></canvas></div>
                </div>
                <div id="compareChartPlaceholder" class="text-center py-12"><i class="fas fa-chart-line text-gray-300 text-5xl mb-4"></i><p class="text-gray-500">選擇標的後顯示比較圖表</p></div>
                <div id="compareChartLoading" class="hidden text-center py-12"><i class="fas fa-spinner fa-spin text-blue-500 text-3xl mb-4"></i><p class="text-gray-500">載入中...</p></div>
            </div>
            <div id="compareResultTable" class="bg-white rounded-xl shadow p-4 md:p-6 hidden">
                <h3 class="font-semibold text-gray-700 mb-4"><i class="fas fa-table mr-2 text-purple-500"></i>比較結果</h3>
                <div class="overflow-x-auto"><table class="w-full text-sm"><thead><tr class="border-b"><th class="text-left py-2 px-3">標的</th><th class="text-right py-2 px-3">起始價</th><th class="text-right py-2 px-3">最新價</th><th class="text-right py-2 px-3">漲跌幅</th></tr></thead><tbody id="compareTableBody"></tbody></table></div>
            </div>`,

        portfolio: `<div class="flex items-center justify-between mb-4 md:mb-6">
                <h2 class="text-xl md:text-2xl font-bold text-gray-800">個人投資記錄</h2>
                <div class="flex gap-2">
                    <button onclick="showExportMenu()" class="px-3 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 text-sm"><i class="fas fa-download mr-1"></i>匯出</button>
                    <button onclick="showImportPortfolioModal()" class="px-3 py-2 bg-orange-100 text-orange-600 rounded-lg hover:bg-orange-200 text-sm"><i class="fas fa-upload mr-1"></i>匯入</button>
                </div>
            </div>
            <div class="flex gap-2 mb-4 border-b">
                <button onclick="switchPortfolioMarket('tw')" id="portfolioTabTw" class="px-4 py-2 border-b-2 border-red-500 text-red-600 font-medium"><i class="fas fa-landmark mr-1"></i>台股</button>
                <button onclick="switchPortfolioMarket('us')" id="portfolioTabUs" class="px-4 py-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700"><i class="fas fa-flag-usa mr-1"></i>美股</button>
            </div>
            <div id="portfolioTwSection">
                <button onclick="showTwModal()" class="w-full mb-4 py-3 border-2 border-dashed border-red-300 text-red-500 rounded-xl hover:bg-red-50"><i class="fas fa-plus mr-2"></i>新增台股交易</button>
                <div class="bg-white rounded-xl shadow p-4 mb-4"><h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-chart-pie mr-2 text-red-500"></i>台股持股總覽</h3><div id="twHoldingsSummary" class="text-center py-4 text-gray-400">載入中...</div></div>
                <div class="bg-white rounded-xl shadow p-4 mb-4"><h3 class="font-semibold text-gray-700 mb-3 flex items-center justify-between"><span><i class="fas fa-list mr-2 text-red-500"></i>持股明細</span><span class="text-sm text-gray-400" id="twHoldingsCount">0 檔</span></h3><div id="twHoldingsList" class="space-y-3"><p class="text-center py-4 text-gray-400">載入中...</p></div></div>
                <div class="bg-white rounded-xl shadow p-4"><h3 class="font-semibold text-gray-700 mb-3 flex items-center justify-between"><span><i class="fas fa-history mr-2 text-red-500"></i>交易紀錄</span><span class="text-sm text-gray-400" id="twTxCount">0 筆</span></h3><div id="twTransactionList" class="space-y-2 max-h-96 overflow-y-auto"><p class="text-center py-4 text-gray-400">載入中...</p></div></div>
            </div>
            <div id="portfolioUsSection" class="hidden">
                <button onclick="showUsModal()" class="w-full mb-4 py-3 border-2 border-dashed border-blue-300 text-blue-500 rounded-xl hover:bg-blue-50"><i class="fas fa-plus mr-2"></i>新增美股交易</button>
                <div class="bg-white rounded-xl shadow p-4 mb-4"><h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-chart-pie mr-2 text-blue-500"></i>美股持股總覽</h3><div id="usHoldingsSummary" class="text-center py-4 text-gray-400">載入中...</div></div>
                <div class="bg-white rounded-xl shadow p-4 mb-4"><h3 class="font-semibold text-gray-700 mb-3 flex items-center justify-between"><span><i class="fas fa-list mr-2 text-blue-500"></i>持股明細</span><span class="text-sm text-gray-400" id="usHoldingsCount">0 檔</span></h3><div id="usHoldingsList" class="space-y-3"><p class="text-center py-4 text-gray-400">載入中...</p></div></div>
                <div class="bg-white rounded-xl shadow p-4"><h3 class="font-semibold text-gray-700 mb-3 flex items-center justify-between"><span><i class="fas fa-history mr-2 text-blue-500"></i>交易紀錄</span><span class="text-sm text-gray-400" id="usTxCount">0 筆</span></h3><div id="usTransactionList" class="space-y-2 max-h-96 overflow-y-auto"><p class="text-center py-4 text-gray-400">載入中...</p></div></div>
            </div>`,

        subscription: `<div class="flex items-center justify-between mb-4 md:mb-6">
                <h2 class="text-xl md:text-2xl font-bold text-gray-800">📡 訂閱精選</h2>
                <button onclick="refreshSubscriptionPicks()" class="text-gray-500 hover:text-gray-700 p-2" title="重新整理"><i class="fas fa-sync-alt"></i></button>
            </div>
            <div id="subscriptionSourcesCard" class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-rss mr-2 text-orange-500"></i>訂閱來源</h3>
                <div id="subscriptionSourcesList"><p class="text-gray-500 text-center py-4">載入中...</p></div>
            </div>
            <div class="bg-white rounded-xl shadow p-4 md:p-6">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center justify-between"><span><i class="fas fa-fire mr-2 text-red-500"></i>精選股票</span><span id="subscriptionPicksCount" class="text-sm text-gray-400"></span></h3>
                <div id="subscriptionPicksList"><p class="text-gray-500 text-center py-4">載入中...</p></div>
            </div>`,

        settings: `<h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">設定</h2>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-magic mr-2 text-purple-500"></i>快速套用模板</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-2" id="templateButtons">
                    <button onclick="applyTemplate('minimal')" data-template="minimal" class="template-btn px-3 py-2 border rounded-lg text-sm hover:bg-gray-50"><i class="fas fa-minus-circle text-gray-400 mr-1"></i>極簡</button>
                    <button onclick="applyTemplate('standard')" data-template="standard" class="template-btn px-3 py-2 border rounded-lg text-sm border-blue-500 bg-blue-50 text-blue-600"><i class="fas fa-check-circle text-blue-500 mr-1"></i>標準</button>
                    <button onclick="applyTemplate('full')" data-template="full" class="template-btn px-3 py-2 border rounded-lg text-sm hover:bg-gray-50"><i class="fas fa-layer-group text-green-500 mr-1"></i>完整</button>
                    <button onclick="applyTemplate('short_term')" data-template="short_term" class="template-btn px-3 py-2 border rounded-lg text-sm hover:bg-gray-50"><i class="fas fa-bolt text-yellow-500 mr-1"></i>短線</button>
                </div>
            </div>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-chart-line mr-2 text-blue-500"></i>指標顯示設定</h3>
                <p class="text-gray-500 text-sm mb-4">選擇在股票分析中要顯示的技術指標</p>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-3" id="indicatorToggles"></div>
                <button onclick="saveIndicatorSettings()" class="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"><i class="fas fa-save mr-2"></i>儲存指標設定</button>
            </div>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-semibold text-gray-700 flex items-center"><i class="fas fa-tags mr-2 text-indigo-500"></i>標籤管理</h3>
                    <button onclick="showTagEditModal()" class="px-3 py-1 bg-indigo-500 text-white text-sm rounded-lg hover:bg-indigo-600"><i class="fas fa-plus mr-1"></i>新增</button>
                </div>
                <div id="tagManageList" class="space-y-2"><p class="text-gray-400 text-center py-4">載入中...</p></div>
            </div>
            <div class="bg-white rounded-xl shadow p-4 md:p-6">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-user-circle mr-2 text-gray-500"></i>帳戶資訊</h3>
                <div class="flex items-center p-4 bg-gray-50 rounded-lg">
                    <img id="settingsAvatar" class="w-16 h-16 rounded-full mr-4" src="" alt="">
                    <div><p class="font-medium text-gray-800" id="settingsUserName">-</p><p class="text-sm text-gray-500">LINE 帳號登入</p><p class="text-xs text-gray-400 mt-1">ID: <span id="settingsUserId">-</span></p></div>
                </div>
                <button onclick="logout()" class="mt-4 w-full py-3 border border-red-300 text-red-500 rounded-lg hover:bg-red-50"><i class="fas fa-sign-out-alt mr-2"></i>登出</button>
            </div>`,

        cagr: `<h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6">報酬率比較</h2>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div><label class="block text-gray-700 mb-2 text-sm">股票代碼 (最多5個)</label><input type="text" id="cagrSymbols" placeholder="如: AAPL,MSFT,GOOGL" class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"><p class="text-xs text-gray-400 mt-1">用逗號分隔多個代碼</p></div>
                    <div><label class="block text-gray-700 mb-2 text-sm">起始日期</label><input type="date" id="cagrStartDate" class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"></div>
                    <div><label class="block text-gray-700 mb-2 text-sm">結束日期</label><input type="date" id="cagrEndDate" class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"></div>
                </div>
                <div class="flex gap-2">
                    <button onclick="calculateCAGR()" class="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"><i class="fas fa-calculator mr-2"></i>計算報酬率</button>
                    <button onclick="clearCAGR()" class="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50"><i class="fas fa-eraser mr-2"></i>清除</button>
                </div>
            </div>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-bolt mr-2 text-yellow-500"></i>快速範例</h3>
                <div class="flex flex-wrap gap-2">
                    <button onclick="setCAGRExample('AAPL,MSFT,GOOGL', 5)" class="px-3 py-1.5 bg-blue-100 text-blue-600 rounded-lg text-sm hover:bg-blue-200">科技三巨頭 (5年)</button>
                    <button onclick="setCAGRExample('SPY,QQQ,VTI', 10)" class="px-3 py-1.5 bg-green-100 text-green-600 rounded-lg text-sm hover:bg-green-200">大盤ETF (10年)</button>
                    <button onclick="setCAGRExample('2330.TW,2317.TW,2454.TW', 5)" class="px-3 py-1.5 bg-red-100 text-red-600 rounded-lg text-sm hover:bg-red-200">台灣權值股 (5年)</button>
                </div>
            </div>
            <div id="cagrResults" class="hidden">
                <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4"><h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-trophy mr-2 text-green-500"></i>報酬率排名</h3><div id="cagrRankingList" class="space-y-3"></div></div>
                <div class="bg-white rounded-xl shadow p-4 md:p-6"><h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-chart-line mr-2 text-blue-500"></i>累積報酬走勢</h3><div class="h-80"><canvas id="cagrChart"></canvas></div></div>
            </div>`,

        admin: `<h2 class="text-xl md:text-2xl font-bold text-gray-800 mb-4 md:mb-6"><i class="fas fa-user-shield mr-2 text-orange-500"></i>管理後台</h2>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-server mr-2 text-green-500"></i>系統狀態</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-2xl font-bold text-blue-600" id="adminUserCount">-</p><p class="text-xs text-gray-500">註冊用戶</p></div>
                    <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-2xl font-bold text-green-600" id="adminWatchlistCount">-</p><p class="text-xs text-gray-500">追蹤項目</p></div>
                    <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-2xl font-bold text-purple-600" id="adminCacheCount">-</p><p class="text-xs text-gray-500">快取項目</p></div>
                    <div class="text-center p-3 bg-gray-50 rounded-lg"><p class="text-2xl font-bold text-orange-600" id="adminTxCount">-</p><p class="text-xs text-gray-500">交易紀錄</p></div>
                </div>
            </div>
            <div class="bg-white rounded-xl shadow p-4 md:p-6 mb-4">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-database mr-2 text-blue-500"></i>快取管理</h3>
                <div class="flex flex-wrap gap-2">
                    <button onclick="adminUpdateAllPrices()" class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"><i class="fas fa-sync mr-2"></i>更新所有價格</button>
                    <button onclick="adminClearOldCache()" class="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600"><i class="fas fa-broom mr-2"></i>清理過期快取</button>
                </div>
                <div id="adminCacheStatus" class="mt-3 text-sm text-gray-500"></div>
            </div>
            <div class="bg-white rounded-xl shadow p-4 md:p-6">
                <h3 class="font-semibold text-gray-700 mb-3 flex items-center"><i class="fas fa-users mr-2 text-indigo-500"></i>用戶列表</h3>
                <div id="adminUserList" class="space-y-2 max-h-96 overflow-y-auto"><p class="text-center py-4 text-gray-400">載入中...</p></div>
            </div>`
    };

    // Section 載入邏輯
    const loadedSections = new Set();

    function loadSectionContent(sectionId) {
        const el = document.getElementById('section-' + sectionId);
        if (!el || loadedSections.has(sectionId)) return;
        if (SECTION_TEMPLATES[sectionId]) {
            el.innerHTML = SECTION_TEMPLATES[sectionId];
            loadedSections.add(sectionId);
            console.log('✅ Section loaded:', sectionId);
        }
    }

    // 攔截 showSection
    const origShow = window.showSection;
    window.showSection = function(id, e) {
        loadSectionContent(id);
        if (typeof origShow === 'function') origShow(id, e);
    };

    window.loadSectionContent = loadSectionContent;
    window.preloadAllSections = function() { Object.keys(SECTION_TEMPLATES).forEach(loadSectionContent); };

    // 自動載入 dashboard
    document.addEventListener('DOMContentLoaded', function() { loadSectionContent('dashboard'); });
})();
