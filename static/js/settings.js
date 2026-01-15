/**
 * 設定模組
 * 包含：指標設定、通知設定、參數調整
 */

(function() {
    'use strict';
    
    // ============================================================
    // 模板定義
    // ============================================================
    
    const TEMPLATES = {
        minimal: {
            indicators: { ma: true, rsi: false, macd: false, kd: false, bollinger: false, obv: false, volume: false },
            alerts: { ma_cross: true, ma_breakout: false, rsi: false, macd: false, kd: false, bollinger: false, volume: false, sentiment: false }
        },
        standard: {
            indicators: { ma: true, rsi: true, macd: true, kd: false, bollinger: true, obv: false, volume: true },
            alerts: { ma_cross: true, ma_breakout: true, rsi: true, macd: true, kd: false, bollinger: false, volume: false, sentiment: true }
        },
        full: {
            indicators: { ma: true, rsi: true, macd: true, kd: true, bollinger: true, obv: true, volume: true },
            alerts: { ma_cross: true, ma_breakout: true, rsi: true, macd: true, kd: true, bollinger: true, volume: true, sentiment: true }
        },
        short_term: {
            indicators: { ma: true, rsi: true, macd: true, kd: true, bollinger: true, obv: false, volume: true },
            alerts: { ma_cross: true, ma_breakout: true, rsi: true, macd: true, kd: true, bollinger: true, volume: true, sentiment: false }
        }
    };
    
    // ============================================================
    // 指標設定
    // ============================================================
    
    function loadSettings() {
        // 載入指標設定
        const indicators = storage.get('indicatorSettings', {
            ma: true, rsi: true, macd: true, kd: false, 
            bollinger: true, obv: false, volume: true
        });
        
        Object.entries(indicators).forEach(([key, val]) => {
            const el = document.getElementById(`show_${key}`);
            if (el) el.checked = val;
        });
        
        // 載入通知設定
        const alerts = storage.get('alertSettings', {
            ma_cross: true, ma_breakout: true, rsi: true, macd: true,
            kd: false, bollinger: false, volume: false, sentiment: true
        });
        
        Object.entries(alerts).forEach(([key, val]) => {
            const el = document.getElementById(`alert_${key}`);
            if (el) el.checked = val;
        });
        
        // 載入參數設定
        const params = storage.get('paramSettings', {
            ma_short: 20, ma_mid: 50, ma_long: 200,
            rsi_period: 14, rsi_overbought: 70, rsi_oversold: 30,
            macd_fast: 12, macd_slow: 26, macd_signal: 9,
            kd_period: 9, bollinger_period: 20, breakout_threshold: 2.0
        });
        
        Object.entries(params).forEach(([key, val]) => {
            const el = document.getElementById(key);
            if (el) el.value = val;
        });
        
        // 更新模板按鈕狀態
        updateTemplateButtons();
    }
    
    function saveIndicatorSettings() {
        const indicators = {};
        ['ma', 'rsi', 'macd', 'kd', 'bollinger', 'obv', 'volume'].forEach(key => {
            const el = document.getElementById(`show_${key}`);
            if (el) indicators[key] = el.checked;
        });
        
        storage.set('indicatorSettings', indicators);
        showToast('指標設定已儲存');
        updateTemplateButtons();
    }
    
    function saveAlertSettings() {
        const alerts = {};
        ['ma_cross', 'ma_breakout', 'rsi', 'macd', 'kd', 'bollinger', 'volume', 'sentiment'].forEach(key => {
            const el = document.getElementById(`alert_${key}`);
            if (el) alerts[key] = el.checked;
        });
        
        storage.set('alertSettings', alerts);
        showToast('通知設定已儲存');
        updateTemplateButtons();
    }
    
    function saveParamSettings() {
        const params = {};
        const keys = [
            'ma_short', 'ma_mid', 'ma_long',
            'rsi_period', 'rsi_overbought', 'rsi_oversold',
            'macd_fast', 'macd_slow', 'macd_signal',
            'kd_period', 'bollinger_period', 'breakout_threshold'
        ];
        
        keys.forEach(key => {
            const el = document.getElementById(key);
            if (el) params[key] = parseFloat(el.value) || 0;
        });
        
        storage.set('paramSettings', params);
        showToast('參數設定已儲存');
    }
    
    // ============================================================
    // 模板功能
    // ============================================================
    
    function applyTemplate(name) {
        const template = TEMPLATES[name];
        if (!template) return;
        
        // 套用指標設定
        Object.entries(template.indicators).forEach(([key, val]) => {
            const el = document.getElementById(`show_${key}`);
            if (el) el.checked = val;
        });
        
        // 套用通知設定
        Object.entries(template.alerts).forEach(([key, val]) => {
            const el = document.getElementById(`alert_${key}`);
            if (el) el.checked = val;
        });
        
        // 儲存設定
        storage.set('indicatorSettings', template.indicators);
        storage.set('alertSettings', template.alerts);
        
        showToast(`已套用「${getTemplateName(name)}」模板`);
        updateTemplateButtons();
    }
    
    function getTemplateName(name) {
        const names = {
            minimal: '極簡',
            standard: '標準',
            full: '完整',
            short_term: '短線'
        };
        return names[name] || name;
    }
    
    function updateTemplateButtons() {
        const currentIndicators = {};
        ['ma', 'rsi', 'macd', 'kd', 'bollinger', 'obv', 'volume'].forEach(key => {
            const el = document.getElementById(`show_${key}`);
            if (el) currentIndicators[key] = el.checked;
        });
        
        const currentAlerts = {};
        ['ma_cross', 'ma_breakout', 'rsi', 'macd', 'kd', 'bollinger', 'volume', 'sentiment'].forEach(key => {
            const el = document.getElementById(`alert_${key}`);
            if (el) currentAlerts[key] = el.checked;
        });
        
        // 檢查匹配的模板
        document.querySelectorAll('.template-btn').forEach(btn => {
            const templateName = btn.dataset.template;
            const template = TEMPLATES[templateName];
            
            if (!template) return;
            
            const indicatorsMatch = Object.entries(template.indicators).every(
                ([k, v]) => currentIndicators[k] === v
            );
            const alertsMatch = Object.entries(template.alerts).every(
                ([k, v]) => currentAlerts[k] === v
            );
            
            if (indicatorsMatch && alertsMatch) {
                btn.classList.add('border-blue-500', 'bg-blue-50', 'text-blue-600');
                btn.classList.remove('border-gray-300');
            } else {
                btn.classList.remove('border-blue-500', 'bg-blue-50', 'text-blue-600');
                btn.classList.add('border-gray-300');
            }
        });
    }
    
    // ============================================================
    // 匯率設定
    // ============================================================
    
    async function updateExchangeRate() {
        const input = document.getElementById('manualExchangeRate');
        const rate = parseFloat(input?.value);
        
        if (!rate || rate <= 0) {
            showToast('請輸入有效的匯率');
            return;
        }
        
        try {
            const res = await apiRequest('/api/portfolio/exchange-rate', {
                method: 'PUT',
                body: { rate }
            });
            
            const data = await res.json();
            
            if (data.success) {
                showToast('匯率已更新');
                if (typeof loadPortfolioSummary === 'function') {
                    loadPortfolioSummary();
                }
            } else {
                showToast(data.detail || '更新失敗');
            }
        } catch (e) {
            console.error('更新匯率失敗:', e);
            showToast('更新失敗');
        }
    }
    
    // ============================================================
    // 導出到全域
    // ============================================================
    
    window.loadSettings = loadSettings;
    window.saveIndicatorSettings = saveIndicatorSettings;
    window.saveAlertSettings = saveAlertSettings;
    window.saveParamSettings = saveParamSettings;
    window.applyTemplate = applyTemplate;
    window.updateExchangeRate = updateExchangeRate;
    
    console.log('⚙️ settings.js 模組已載入');
})();
