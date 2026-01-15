/**
 * 儀表板模組
 * 包含：BTC 價格、三大指數、市場情緒
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
            
            console.log('[BTC] CoinGecko 回應:', data);

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
    }
    
    // ============================================================
    // 三大指數
    // ============================================================
    
    async function loadIndices() {
        try {
            console.log('開始載入指數...');
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
    }
    
    // ============================================================
    // 市場情緒
    // ============================================================
    
    async function loadSentiment() {
        try {
            const res = await fetch('/api/market/sentiment');
            const data = await res.json();
            
            if (data.success) {
                updateSentimentCard('stock', data.stock || { value: 50, classification: 'neutral' });
                updateSentimentCard('crypto', data.crypto || { value: 50, classification: 'neutral' });
            }
        } catch (e) {
            console.error('載入情緒失敗', e);
            updateSentimentCard('stock', { value: 50, classification: 'neutral' });
            updateSentimentCard('crypto', { value: 50, classification: 'neutral' });
        }
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
    // 主載入函數
    // ============================================================
    
    async function loadDashboard() {
        await loadIndices();
        await loadSentiment();
        await loadBtcPrice();
        if (typeof loadWatchlistOverview === 'function') {
            await loadWatchlistOverview();
        }
    }
    
    // 管理員更新
    async function triggerAdminUpdates() {
        console.log('🔄 管理員登入，觸發全部更新...');
        const token = localStorage.getItem('token');
        
        try {
            fetch('/api/admin/update-indices', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json()).then(d => {
                console.log('✅ 四大指數更新:', d.success ? '成功' : '失敗');
            });
            
            fetch('/api/admin/update-price-cache', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json()).then(d => {
                console.log('✅ 價格快取更新:', d.success ? '成功' : '失敗');
            });
            
            loadBtcPrice();
            
            fetch('/api/admin/update-exchange-rate', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json()).then(d => {
                console.log('✅ 匯率更新:', d.success ? '成功' : '失敗');
            });
        } catch (e) {
            console.error('管理員更新觸發失敗:', e);
        }
    }
    
    // ============================================================
    // 導出到全域
    // ============================================================
    
    window.loadDashboard = loadDashboard;
    window.loadBtcPrice = loadBtcPrice;
    window.loadIndices = loadIndices;
    window.loadSentiment = loadSentiment;
    window.openIndexModal = openIndexModal;
    window.closeIndexModal = closeIndexModal;
    window.loadIndexModalChart = loadIndexModalChart;
    window.openSentimentModal = openSentimentModal;
    window.closeSentimentModal = closeSentimentModal;
    window.loadSentimentModalChart = loadSentimentModalChart;
    window.triggerAdminUpdates = triggerAdminUpdates;
    
    console.log('📊 dashboard.js 模組已載入');
})();
