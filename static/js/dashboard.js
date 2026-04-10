/**
 * 儀表板模組
 * 包含：BTC 價格、三大指數、市場情緒、熱門追蹤統計
 */

(function() {
    'use strict';
    
    // ============================================================
    // 私有變數
    // ============================================================
    
    let btcRefreshInterval = null;
    let indexCharts = {};
    let indexModalChart = null;
    let currentIndexSymbol = '';
    let currentIndexName = '';
    let sentimentModalChart = null;
    let currentSentimentMarket = '';
    let currentSentimentName = '';
    
    // ============================================================
    // BTC 價格
    // ============================================================
    
    async function loadBtcPrice() {
        const priceEl = document.getElementById('btc-price');
        const changeEl = document.getElementById('btc-change');
        const cardEl = document.getElementById('btc-price-card');
        const indicatorEl = document.getElementById('btc-update-indicator');

        if (!priceEl || !changeEl) return;

        try {
            if (indicatorEl) indicatorEl.classList.remove('hidden');

            // 直接用 CoinGecko Simple API 取即時價格
            const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true');
            const data = await res.json();
            

            if (data.bitcoin) {
                const price = data.bitcoin.usd || 0;
                const dayChange = data.bitcoin.usd_24h_change || 0;
                
                if (price > 0) {
                    priceEl.textContent = '$' + price.toLocaleString('en-US', { 
                        minimumFractionDigits: 0, 
                        maximumFractionDigits: 0 
                    });

                    const prefix = dayChange >= 0 ? '+' : '';
                    changeEl.textContent = `${prefix}${dayChange.toFixed(2)}%`;
                    
                    changeEl.classList.remove('text-green-200', 'text-red-200');
                    changeEl.classList.add(dayChange >= 0 ? 'text-green-200' : 'text-red-200');

                    // 根據漲跌幅改變卡片顏色
                    if (cardEl) {
                        cardEl.classList.remove(
                            'from-orange-500', 'to-yellow-500', 
                            'from-green-500', 'to-emerald-500', 
                            'from-red-500', 'to-rose-500'
                        );
                        if (dayChange >= 3) {
                            cardEl.classList.add('from-green-500', 'to-emerald-500');
                        } else if (dayChange <= -3) {
                            cardEl.classList.add('from-red-500', 'to-rose-500');
                        } else {
                            cardEl.classList.add('from-orange-500', 'to-yellow-500');
                        }
                    }
                } else {
                    priceEl.textContent = '載入中...';
                }
            }
        } catch (e) {
            console.error('[BTC] 載入失敗:', e);
            // 備援：使用後端 API
            try {
                const backupRes = await fetch('/api/crypto/BTC');
                const backupData = await backupRes.json();
                if (backupData.success && backupData.price?.current) {
                    priceEl.textContent = '$' + backupData.price.current.toLocaleString('en-US', { 
                        minimumFractionDigits: 0, 
                        maximumFractionDigits: 0 
                    });
                    const change = backupData.change?.day || 0;
                    changeEl.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
                }
            } catch (backupErr) {
                console.error('[BTC] 備援 API 也失敗:', backupErr);
            }
        } finally {
            if (indicatorEl) setTimeout(() => indicatorEl.classList.add('hidden'), 500);
        }
        
        // 設定自動更新（每分鐘）
        if (!btcRefreshInterval) {
            btcRefreshInterval = setInterval(loadBtcPrice, 60000);
        }
    
    // ============================================================
    // 三大指數
    // ============================================================
    
    async function loadIndices() {
        try {
            const res = await fetch('/api/market/indices');
            const data = await res.json();
            
            if (data.success && data.data && data.data.indices) {
                const indices = data.data.indices;
                
                if (indices['^GSPC']) updateIndexCard('GSPC', indices['^GSPC']);
                if (indices['^DJI']) updateIndexCard('DJI', indices['^DJI']);
                if (indices['^IXIC']) updateIndexCard('IXIC', indices['^IXIC']);
                if (indices['^TWII']) updateIndexCard('TWII', indices['^TWII']);
            }
        } catch (e) {
            console.error('載入指數失敗', e);
        }
    
    function updateIndexCard(symbol, data) {
        const priceEl = document.getElementById(`index-${symbol}-price`);
        const changeEl = document.getElementById(`index-${symbol}-change`);
        const dateEl = document.getElementById(`index-${symbol}-date`);
        
        if (priceEl) {
            priceEl.textContent = data.close 
                ? data.close.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) 
                : '--';
        }
        
        if (changeEl && data.change_pct !== undefined) {
            const isPositive = data.change_pct >= 0;
            changeEl.textContent = `${isPositive ? '▲' : '▼'} ${Math.abs(data.change_pct).toFixed(2)}%`;
            changeEl.className = `text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`;
        }
        
        if (dateEl && data.date) {
            dateEl.textContent = `更新: ${data.date}`;
        }
    
    // ============================================================
    // 指數圖表 Modal
    // ============================================================
    
    function openIndexModal(symbol, name) {
        currentIndexSymbol = symbol;
        currentIndexName = name;
        document.getElementById('indexModalTitle').textContent = name;
        document.getElementById('indexChartModal').classList.add('open');
        document.body.style.overflow = 'hidden';
        loadIndexModalChart(365);
    }
    
    function closeIndexModal() {
        document.getElementById('indexChartModal').classList.remove('open');
        document.body.style.overflow = '';
    }
    
    async function loadIndexModalChart(days) {
        const canvas = document.getElementById('indexModalChart');
        if (!canvas) return;
        
        // 更新按鈕狀態
        document.querySelectorAll('.index-modal-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent === '1M' && days === 30) btn.classList.add('active');
            if (btn.textContent === '3M' && days === 90) btn.classList.add('active');
            if (btn.textContent === '1Y' && days === 365) btn.classList.add('active');
            if (btn.textContent === '5Y' && days === 1825) btn.classList.add('active');
        });
        
        try {
            const res = await fetch(`/api/market/indices/${currentIndexSymbol}/history?days=${days}`);
            const data = await res.json();
            
            if (data.success && data.data && data.data.history) {
                const history = data.data.history;
                const labels = history.map(h => h.date);
                const prices = history.map(h => h.close);
                
                if (indexModalChart) indexModalChart.destroy();
                
                const cleanSymbol = currentIndexSymbol.replace('^', '');
                const colorMap = { 'GSPC': '#3B82F6', 'DJI': '#10B981', 'IXIC': '#8B5CF6', 'TWII': '#EF4444' };
                const color = colorMap[cleanSymbol] || '#3B82F6';
                
                const ctx = canvas.getContext('2d');
                indexModalChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: currentIndexName,
                            data: prices,
                            borderColor: color,
                            backgroundColor: 'transparent',
                            borderWidth: 2,
                            pointRadius: 0,
                            tension: 0.1,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: ctx => ctx.parsed.y.toLocaleString(undefined, {minimumFractionDigits: 2})
                                }
                            }
                        },
                        scales: {
                            x: { ticks: { maxTicksLimit: 8, font: { size: 11 } }, grid: { display: false } },
                            y: { ticks: { font: { size: 11 }, callback: v => v.toLocaleString() }, grid: { color: '#F3F4F6' } }
                        }
                    }
                });
            }
        } catch (e) {
            console.error('載入指數走勢失敗', e);
        }
    
    // ============================================================
    // 市場情緒
    // ============================================================
    
    async function loadSentiment() {
        try {
            const res = await fetch('/api/market/sentiment');
            const data = await res.json();
            
            if (data.success) {
                updateSentimentCard('stock', data.data?.stock || { value: 50, classification: 'neutral' });
                updateSentimentCard('crypto', data.data?.crypto || { value: 50, classification: 'neutral' });
            }
        } catch (e) {
            console.error('載入情緒失敗', e);
            updateSentimentCard('stock', { value: 50, classification: 'neutral' });
            updateSentimentCard('crypto', { value: 50, classification: 'neutral' });
        }

    function updateSentimentCard(type, sentiment) {
        if (!sentiment) return;
        
        const value = sentiment.value;
        
        // 更新數值
        const gaugeValue = document.getElementById(`${type}GaugeValue`);
        if (gaugeValue) gaugeValue.textContent = value;
        
        // 更新指針角度
        const angle = -90 + (value / 100) * 180;
        const needleGroup = document.getElementById(`${type}NeedleGroup`);
        if (needleGroup) needleGroup.style.transform = `rotate(${angle}deg)`;
        
        // 決定狀態
        let label, colorClass;
        if (value <= 25) { label = 'Extreme Fear'; colorClass = 'text-red-600'; }
        else if (value <= 45) { label = 'Fear'; colorClass = 'text-orange-500'; }
        else if (value <= 55) { label = 'Neutral'; colorClass = 'text-gray-500'; }
        else if (value <= 75) { label = 'Greed'; colorClass = 'text-green-500'; }
        else { label = 'Extreme Greed'; colorClass = 'text-emerald-600'; }
        
        const statusEl = document.getElementById(`${type}SentimentStatus`);
        if (statusEl) {
            statusEl.textContent = label;
            statusEl.className = `text-center font-semibold mt-1 ${colorClass}`;
        }
        
        const timeEl = document.getElementById(`${type}SentimentTime`);
        if (timeEl && sentiment.updated_at) {
            const date = new Date(sentiment.updated_at);
            timeEl.textContent = `Last updated ${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
        }
    }
    
    // ============================================================
    // 情緒圖表 Modal
    // ============================================================
    
    function openSentimentModal(market, name) {
        currentSentimentMarket = market;
        currentSentimentName = name;
        document.getElementById('sentimentModalTitle').textContent = name;
        document.getElementById('sentimentChartModal').classList.add('open');
        document.body.style.overflow = 'hidden';
        loadSentimentModalChart(180);
    }
    
    function closeSentimentModal() {
        document.getElementById('sentimentChartModal').classList.remove('open');
        document.body.style.overflow = '';
    }
    
    async function loadSentimentModalChart(days) {
        const canvas = document.getElementById('sentimentModalChart');
        if (!canvas) return;
        
        // 更新按鈕狀態
        document.querySelectorAll('.sentiment-modal-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent === '1M' && days === 30) btn.classList.add('active');
            if (btn.textContent === '3M' && days === 90) btn.classList.add('active');
            if (btn.textContent === '6M' && days === 180) btn.classList.add('active');
            if (btn.textContent === '1Y' && days === 365) btn.classList.add('active');
        });
        
        try {
            const res = await fetch(`/api/market/sentiment/${currentSentimentMarket}/history?days=${days}`);
            const data = await res.json();
            
            if (data.success && data.data && data.data.history) {
                const history = data.data.history;
                const labels = history.map(h => h.date);
                const values = history.map(h => h.value);
                
                if (sentimentModalChart) sentimentModalChart.destroy();
                
                const ctx = canvas.getContext('2d');
                const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
                gradient.addColorStop(0, 'rgba(34, 197, 94, 0.3)');
                gradient.addColorStop(0.5, 'rgba(234, 179, 8, 0.2)');
                gradient.addColorStop(1, 'rgba(239, 68, 68, 0.3)');
                
                const color = currentSentimentMarket === 'stock' ? '#3B82F6' : '#F97316';
                
                sentimentModalChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: currentSentimentName,
                            data: values,
                            borderColor: color,
                            backgroundColor: gradient,
                            fill: true,
                            borderWidth: 2,
                            pointRadius: 0,
                            tension: 0.3,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: ctx => {
                                        const v = ctx.parsed.y;
                                        let status = '';
                                        if (v <= 25) status = '(Extreme Fear)';
                                        else if (v <= 45) status = '(Fear)';
                                        else if (v <= 55) status = '(Neutral)';
                                        else if (v <= 75) status = '(Greed)';
                                        else status = '(Extreme Greed)';
                                        return `${v} ${status}`;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { ticks: { maxTicksLimit: 8, font: { size: 11 } }, grid: { display: false } },
                            y: {
                                min: 0, max: 100,
                                ticks: {
                                    font: { size: 11 }, stepSize: 25,
                                    callback: v => {
                                        if (v === 0) return '0 Fear';
                                        if (v === 100) return '100 Greed';
                                        return v;
                                    }
                                },
                                grid: { color: '#F3F4F6' }
                            }
                        }
                    }
                });
            }
        } catch (e) {
            console.error('載入情緒走勢失敗', e);
        }
    }
    
    // ============================================================
    // 🆕 熱門追蹤統計
    // ============================================================
    
    async function loadPopularStocks() {
        const container = document.getElementById('popularStocksContainer');
        if (!container) return;
        
        try {
            const res = await fetch('/api/watchlist/popular?limit=10');
            const data = await res.json();
            
            if (data.success && data.data && data.data.length > 0) {
                renderPopularStocks(data.data);
            } else {
                container.innerHTML = `
                    <div class="text-center py-4 text-gray-400 text-sm">
                        <i class="fas fa-chart-line mb-2"></i>
                        <p>尚無追蹤統計</p>
                    </div>
                `;
            }
        } catch (e) {
            console.error('載入熱門追蹤失敗:', e);
            container.innerHTML = `
                <div class="text-center py-4 text-gray-400 text-sm">
                    <p>載入失敗</p>
                </div>
            `;
        }
    }
    
    function renderPopularStocks(stocks) {
        const container = document.getElementById('popularStocksContainer');
        if (!container) return;
        
        const maxCount = stocks[0]?.count || 1;
        
        let html = `
            <div class="space-y-2">
                ${stocks.map((stock, index) => {
                    const barWidth = Math.max(20, (stock.count / maxCount) * 100);
                    const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '';
                    const bgClass = index < 3 ? 'bg-gradient-to-r from-yellow-50 to-orange-50' : 'bg-gray-50';
                    
                    return `
                        <div class="flex items-center p-2 rounded-lg ${bgClass} hover:shadow-sm transition cursor-pointer" 
                             onclick="searchSymbol('${stock.symbol}')">
                            <span class="w-6 text-center text-sm">${medal || (index + 1)}</span>
                            <div class="flex-1 ml-2">
                                <div class="flex items-center justify-between">
                                    <span class="font-medium text-gray-800 text-sm">${stock.symbol}</span>
                                    <span class="text-xs text-gray-500">${stock.count} 人追蹤</span>
                                </div>
                                <div class="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                    <div class="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all" 
                                         style="width: ${barWidth}%"></div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    // ============================================================
    // 主載入函數
    // ============================================================
    
    async function loadDashboard() {
        // 🆕 V1.07 並行載入（不互相等待）
        const tasks = [
            loadSentiment(),
            loadIndices(),
            typeof loadWatchlistOverview === 'function' ? loadWatchlistOverview() : Promise.resolve(),
            loadPopularStocks(),
        ];
        
        loadBtcPrice();  // 外部 API，背景執行
        
        await Promise.all(tasks);
    }
    
    // 管理員更新
    async function triggerAdminUpdates() {
        const token = localStorage.getItem('token');
        
        try {
            fetch('/api/admin/update-indices', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json()).then(d => {
            });
            
            fetch('/api/admin/update-price-cache', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json()).then(d => {
            });
            
            loadBtcPrice();
            
            fetch('/api/admin/update-exchange-rate', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json()).then(d => {
            });
        } catch (e) {
            console.error('管理員更新觸發失敗:', e);
        }
    
    /**
     * 載入恐懼貪婪詳細頁面
     */
    async function loadSentimentDetail() {
        const container = document.getElementById('sentimentContent');
        if (!container) return;
        
        // 先嘗試取得情緒資料
        let stockData = { value: 50, classification: 'neutral' };
        let cryptoData = { value: 50, classification: 'neutral' };
        
        try {
            const res = await fetch('/api/market/sentiment');
            if (res.ok) {
                const data = await res.json();
                if (data.data?.stock) stockData = data.data.stock;
                if (data.data?.crypto) cryptoData = data.data.crypto;
            }
        } catch (e) {
            console.error('載入情緒資料失敗', e);
        }
        
        // 生成簡潔儀表盤 SVG HTML
        function createGaugeSVG(id, value) {
            const angle = -90 + (value / 100) * 180;
            
            let label, colorClass;
            if (value <= 25) {
                label = 'Extreme Fear';
                colorClass = 'text-red-600';
            } else if (value <= 45) {
                label = 'Fear';
                colorClass = 'text-orange-500';
            } else if (value <= 55) {
                label = 'Neutral';
                colorClass = 'text-gray-500';
            } else if (value <= 75) {
                label = 'Greed';
                colorClass = 'text-green-500';
            } else {
                label = 'Extreme Greed';
                colorClass = 'text-emerald-600';
            }
            
            return `
                <div class="fear-greed-gauge">
                    <svg viewBox="0 0 200 115" class="gauge-svg">
                        <!-- 弧形背景區段 -->
                        <path class="gauge-arc gauge-arc-extreme-fear" d="M 20 100 A 80 80 0 0 1 38 62" />
                        <path class="gauge-arc gauge-arc-fear" d="M 38 62 A 80 80 0 0 1 75 32" />
                        <path class="gauge-arc gauge-arc-neutral" d="M 75 32 A 80 80 0 0 1 125 32" />
                        <path class="gauge-arc gauge-arc-greed" d="M 125 32 A 80 80 0 0 1 162 62" />
                        <path class="gauge-arc gauge-arc-extreme-greed" d="M 162 62 A 80 80 0 0 1 180 100" />
                        
                        <!-- 刻度數字 -->
                        <text x="8" y="105" class="gauge-tick-text">0</text>
                        <text x="96" y="12" class="gauge-tick-text" text-anchor="middle">50</text>
                        <text x="188" y="105" class="gauge-tick-text">100</text>
                        
                        <!-- 指針 -->
                        <g class="gauge-needle-group" style="transform: rotate(${angle}deg); transform-origin: 100px 100px;">
                            <polygon class="gauge-needle" points="100,25 97,100 103,100" />
                        </g>
                        <circle class="gauge-center-dot" cx="100" cy="100" r="6" />
                    </svg>
                </div>
                <div class="text-center mt-2">
                    <span class="text-4xl font-bold text-gray-800">${value}</span>
                </div>
                <p class="text-center font-semibold text-lg mt-1 ${colorClass}">${label}</p>
            `;
        }
        
        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <!-- 美股情緒 -->
                <div class="bg-white rounded-xl shadow p-6 cursor-pointer hover:shadow-lg" onclick="openSentimentModal('stock', '美股恐懼貪婪指數')">
                    <h3 class="font-semibold text-gray-700 mb-4 text-center">美股情緒指數 (Fear & Greed)</h3>
                    ${createGaugeSVG('stock-detail', stockData.value)}
                    <p class="text-center text-xs text-gray-400 mt-2">點擊查看歷史趨勢</p>
                </div>
                
                <!-- 幣圈情緒 -->
                <div class="bg-white rounded-xl shadow p-6 cursor-pointer hover:shadow-lg" onclick="openSentimentModal('crypto', '幣圈恐懼貪婪指數')">
                    <h3 class="font-semibold text-gray-700 mb-4 text-center">幣圈情緒指數</h3>
                    ${createGaugeSVG('crypto-detail', cryptoData.value)}
                    <p class="text-center text-xs text-gray-400 mt-2">點擊查看歷史趨勢</p>
                </div>
            </div>
            
            <div class="bg-white rounded-xl shadow p-6">
                <h3 class="font-semibold text-gray-700 mb-4">市場情緒解讀</h3>
                <div class="space-y-4 text-sm text-gray-600">
                    <div class="flex items-start">
                        <span class="w-24 flex-shrink-0 font-medium">0-25</span>
                        <span class="px-2 py-1 bg-red-100 text-red-700 rounded mr-2">極度恐懼</span>
                        <span>市場恐慌，可能是買入機會</span>
                    </div>
                    <div class="flex items-start">
                        <span class="w-24 flex-shrink-0 font-medium">26-45</span>
                        <span class="px-2 py-1 bg-orange-100 text-orange-700 rounded mr-2">恐懼</span>
                        <span>市場偏謹慎</span>
                    </div>
                    <div class="flex items-start">
                        <span class="w-24 flex-shrink-0 font-medium">46-55</span>
                        <span class="px-2 py-1 bg-gray-100 text-gray-700 rounded mr-2">中性</span>
                        <span>觀望為主</span>
                    </div>
                    <div class="flex items-start">
                        <span class="w-24 flex-shrink-0 font-medium">56-75</span>
                        <span class="px-2 py-1 bg-green-100 text-green-700 rounded mr-2">貪婪</span>
                        <span>市場偏樂觀</span>
                    </div>
                    <div class="flex items-start">
                        <span class="w-24 flex-shrink-0 font-medium">76-100</span>
                        <span class="px-2 py-1 bg-emerald-100 text-emerald-700 rounded mr-2">極度貪婪</span>
                        <span>市場過熱，留意風險</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // ============================================================
    // 導出到全域
    // ============================================================
    
    window.loadDashboard = loadDashboard;
    window.loadBtcPrice = loadBtcPrice;
    window.loadIndices = loadIndices;
    window.loadSentiment = loadSentiment;
    window.loadSentimentDetail = loadSentimentDetail;
    window.loadPopularStocks = loadPopularStocks;  // 🆕
    window.openIndexModal = openIndexModal;
    window.closeIndexModal = closeIndexModal;
    window.loadIndexModalChart = loadIndexModalChart;
    window.openSentimentModal = openSentimentModal;
    window.closeSentimentModal = closeSentimentModal;
    window.loadSentimentModalChart = loadSentimentModalChart;
    window.triggerAdminUpdates = triggerAdminUpdates;
    
})();
