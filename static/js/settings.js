/**
 * SELA 設定頁面 JavaScript
 * 版本: 1.0.0
 * 
 * 依賴: 需要 dashboard.html 中的 apiRequest() 函數
 */

// ========== 常數定義 ==========

// 指標名稱對照表
const INDICATOR_LABELS = {
    show_ma: { name: '均線', icon: 'fas fa-wave-square', color: 'text-blue-500' },
    show_rsi: { name: 'RSI', icon: 'fas fa-tachometer-alt', color: 'text-green-500' },
    show_macd: { name: 'MACD', icon: 'fas fa-signal', color: 'text-purple-500' },
    show_kd: { name: 'KD', icon: 'fas fa-chart-pie', color: 'text-pink-500' },
    show_bollinger: { name: '布林通道', icon: 'fas fa-road', color: 'text-indigo-500' },
    show_obv: { name: 'OBV', icon: 'fas fa-database', color: 'text-teal-500' },
    show_volume: { name: '成交量', icon: 'fas fa-chart-bar', color: 'text-orange-500' },
};

// 通知名稱對照表
const ALERT_LABELS = {
    alert_ma_cross: { name: '均線交叉', icon: 'fas fa-times', color: 'text-blue-500' },
    alert_ma_breakout: { name: '均線突破', icon: 'fas fa-arrow-up', color: 'text-green-500' },
    alert_rsi: { name: 'RSI 超買/超賣', icon: 'fas fa-exclamation-triangle', color: 'text-yellow-500' },
    alert_macd: { name: 'MACD 交叉', icon: 'fas fa-exchange-alt', color: 'text-purple-500' },
    alert_kd: { name: 'KD 交叉', icon: 'fas fa-random', color: 'text-pink-500' },
    alert_bollinger: { name: '布林突破', icon: 'fas fa-expand-arrows-alt', color: 'text-indigo-500' },
    alert_volume: { name: '量能異常', icon: 'fas fa-volume-up', color: 'text-red-500' },
    alert_sentiment: { name: '情緒極端', icon: 'fas fa-smile', color: 'text-orange-500' },
};

// 模板名稱對照
const TEMPLATE_NAMES = {
    minimal: '極簡',
    standard: '標準',
    full: '完整',
    short_term: '短線'
};

// 參數設定範圍
const PARAM_RANGES = {
    ma_short: { min: 5, max: 50, step: 1 },
    ma_mid: { min: 20, max: 100, step: 1 },
    ma_long: { min: 100, max: 300, step: 1 },
    rsi_period: { min: 5, max: 30, step: 1 },
    rsi_overbought: { min: 60, max: 90, step: 1 },
    rsi_oversold: { min: 10, max: 40, step: 1 },
    macd_fast: { min: 5, max: 20, step: 1 },
    macd_slow: { min: 15, max: 40, step: 1 },
    macd_signal: { min: 5, max: 15, step: 1 },
    kd_period: { min: 5, max: 20, step: 1 },
    bollinger_period: { min: 10, max: 30, step: 1 },
    bollinger_std: { min: 1, max: 3, step: 0.1 },
    breakout_threshold: { min: 0.5, max: 5, step: 0.1 },
    volume_alert_ratio: { min: 1, max: 5, step: 0.1 },
};

// ========== 狀態管理 ==========

let settingsState = {
    indicators: {},
    alerts: {},
    params: {},
    hasUnsavedChanges: false,
    isLoading: false,
    currentTemplate: null
};

// ========== 初始化 ==========

/**
 * 初始化設定頁面
 */
async function initSettingsPage() {
    console.log('[Settings] 初始化設定頁面');
    await loadAllSettings();
}

// ========== API 調用 ==========

/**
 * 載入所有設定
 */
async function loadAllSettings() {
    settingsState.isLoading = true;
    showSettingsLoading(true);
    
    try {
        // 並行載入三種設定
        const [indRes, alertRes, paramRes] = await Promise.all([
            apiRequest('/api/settings/indicators'),
            apiRequest('/api/settings/alerts'),
            apiRequest('/api/settings/params'),
        ]);
        
        settingsState.indicators = indRes.data || {};
        settingsState.alerts = alertRes.data || {};
        settingsState.params = paramRes.data || {};
        settingsState.hasUnsavedChanges = false;
        
        // 渲染 UI
        renderIndicatorToggles();
        renderAlertToggles();
        renderParamInputs();
        detectCurrentTemplate();
        updateSaveButton();
        
        console.log('[Settings] 設定載入完成', settingsState);
        
    } catch (error) {
        console.error('[Settings] 載入設定失敗:', error);
        showSettingsMessage('載入設定失敗，請重新整理頁面', 'error');
    } finally {
        settingsState.isLoading = false;
        showSettingsLoading(false);
    }
}

/**
 * 儲存所有設定
 */
async function saveAllSettings() {
    const btn = document.getElementById('settings-save-btn');
    if (!btn || settingsState.isLoading) return;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 儲存中...';
    
    try {
        // 收集參數值
        const params = collectParamValues();
        
        // 並行儲存三種設定
        await Promise.all([
            apiRequest('/api/settings/indicators', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settingsState.indicators)
            }),
            apiRequest('/api/settings/alerts', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settingsState.alerts)
            }),
            apiRequest('/api/settings/params', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            }),
        ]);
        
        settingsState.params = params;
        settingsState.hasUnsavedChanges = false;
        
        showSettingsMessage('設定已成功儲存！', 'success');
        btn.innerHTML = '<i class="fas fa-check"></i> 已儲存';
        
        setTimeout(() => {
            updateSaveButton();
        }, 2000);
        
    } catch (error) {
        console.error('[Settings] 儲存失敗:', error);
        showSettingsMessage('儲存失敗，請重試', 'error');
        btn.innerHTML = '<i class="fas fa-save"></i> 儲存設定';
        btn.disabled = false;
    }
}

/**
 * 套用模板
 */
async function applyTemplate(templateName) {
    if (settingsState.isLoading) return;
    
    try {
        const res = await apiRequest(`/api/settings/template/${templateName}`, {
            method: 'POST'
        });
        
        if (res.success) {
            showSettingsMessage(`已套用「${TEMPLATE_NAMES[templateName]}」模板`, 'success');
            settingsState.currentTemplate = templateName;
            updateTemplateButtons();
            
            // 重新載入設定
            await loadAllSettings();
        }
    } catch (error) {
        console.error('[Settings] 套用模板失敗:', error);
        showSettingsMessage('套用模板失敗', 'error');
    }
}

// ========== 渲染函數 ==========

/**
 * 渲染指標開關
 */
function renderIndicatorToggles() {
    const grid = document.getElementById('indicators-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    for (const [key, config] of Object.entries(INDICATOR_LABELS)) {
        const isActive = settingsState.indicators[key] === true;
        const div = document.createElement('div');
        div.className = `toggle-switch ${isActive ? 'active' : ''}`;
        div.setAttribute('data-key', key);
        div.onclick = () => toggleIndicator(key);
        div.innerHTML = `
            <div class="toggle-label">
                <i class="${config.icon} ${isActive ? config.color : ''}"></i>
                <span>${config.name}</span>
            </div>
            <div class="toggle-dot"></div>
        `;
        grid.appendChild(div);
    }
}

/**
 * 渲染通知開關
 */
function renderAlertToggles() {
    const grid = document.getElementById('alerts-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    for (const [key, config] of Object.entries(ALERT_LABELS)) {
        const isActive = settingsState.alerts[key] === true;
        const div = document.createElement('div');
        div.className = `toggle-switch ${isActive ? 'active' : ''}`;
        div.setAttribute('data-key', key);
        div.onclick = () => toggleAlert(key);
        div.innerHTML = `
            <div class="toggle-label">
                <i class="${config.icon} ${isActive ? config.color : ''}"></i>
                <span>${config.name}</span>
            </div>
            <div class="toggle-dot"></div>
        `;
        grid.appendChild(div);
    }
}

/**
 * 渲染參數輸入
 */
function renderParamInputs() {
    const params = settingsState.params;
    
    for (const [key, value] of Object.entries(params)) {
        const input = document.getElementById(`param-${key}`);
        if (input) {
            input.value = value;
            
            // 設定範圍限制
            const range = PARAM_RANGES[key];
            if (range) {
                input.min = range.min;
                input.max = range.max;
                input.step = range.step;
            }
        }
    }
}

// ========== 互動處理 ==========

/**
 * 切換指標
 */
function toggleIndicator(key) {
    settingsState.indicators[key] = !settingsState.indicators[key];
    markUnsaved();
    renderIndicatorToggles();
    detectCurrentTemplate();
}

/**
 * 切換通知
 */
function toggleAlert(key) {
    settingsState.alerts[key] = !settingsState.alerts[key];
    markUnsaved();
    renderAlertToggles();
    detectCurrentTemplate();
}

/**
 * 切換參數面板
 */
function toggleParamsPanel() {
    const content = document.getElementById('params-collapse-content');
    const arrow = document.getElementById('params-collapse-arrow');
    
    if (content && arrow) {
        content.classList.toggle('expanded');
        arrow.classList.toggle('rotated');
    }
}

/**
 * 收集參數值
 */
function collectParamValues() {
    const params = {};
    
    for (const key of Object.keys(PARAM_RANGES)) {
        const input = document.getElementById(`param-${key}`);
        if (input) {
            const value = parseFloat(input.value);
            if (!isNaN(value)) {
                params[key] = value;
            }
        }
    }
    
    return params;
}

/**
 * 參數變更處理
 */
function onParamChange() {
    markUnsaved();
}

// ========== 狀態更新 ==========

/**
 * 標記有未儲存的變更
 */
function markUnsaved() {
    settingsState.hasUnsavedChanges = true;
    updateSaveButton();
}

/**
 * 更新儲存按鈕狀態
 */
function updateSaveButton() {
    const btn = document.getElementById('settings-save-btn');
    if (!btn) return;
    
    btn.disabled = false;
    
    if (settingsState.hasUnsavedChanges) {
        btn.innerHTML = `
            <i class="fas fa-save"></i> 
            儲存設定 
            <span class="unsaved-badge">未儲存</span>
        `;
    } else {
        btn.innerHTML = '<i class="fas fa-save"></i> 儲存設定';
    }
}

/**
 * 更新模板按鈕狀態
 */
function updateTemplateButtons() {
    document.querySelectorAll('.template-btn').forEach(btn => {
        const template = btn.getAttribute('data-template');
        btn.classList.toggle('active', template === settingsState.currentTemplate);
    });
}

/**
 * 偵測當前模板
 */
function detectCurrentTemplate() {
    // 簡單的模板偵測邏輯
    const ind = settingsState.indicators;
    const alerts = settingsState.alerts;
    
    // 極簡模式
    if (ind.show_ma && ind.show_volume && 
        !ind.show_rsi && !ind.show_macd && !ind.show_kd && !ind.show_bollinger && !ind.show_obv) {
        settingsState.currentTemplate = 'minimal';
    }
    // 完整模式
    else if (ind.show_ma && ind.show_rsi && ind.show_macd && ind.show_kd && 
             ind.show_bollinger && ind.show_obv && ind.show_volume) {
        settingsState.currentTemplate = 'full';
    }
    // 其他情況清除模板選擇
    else {
        settingsState.currentTemplate = null;
    }
    
    updateTemplateButtons();
}

// ========== UI 輔助 ==========

/**
 * 顯示/隱藏載入狀態
 */
function showSettingsLoading(show) {
    const loading = document.getElementById('settings-loading');
    const content = document.getElementById('settings-content');
    
    if (loading) loading.classList.toggle('hidden', !show);
    if (content) content.classList.toggle('hidden', show);
}

/**
 * 顯示訊息
 */
function showSettingsMessage(text, type) {
    const msg = document.getElementById('settings-message');
    if (!msg) return;
    
    msg.className = `settings-message ${type}`;
    msg.textContent = text;
    msg.classList.remove('hidden');
    
    setTimeout(() => {
        msg.classList.add('hidden');
    }, 3000);
}

// ========== 頁面離開警告 ==========

/**
 * 離開前檢查未儲存變更
 */
function checkUnsavedChanges() {
    if (settingsState.hasUnsavedChanges) {
        return confirm('您有未儲存的變更，確定要離開嗎？');
    }
    return true;
}

// ========== 導出函數（供外部調用）==========

// 確保這些函數可以在全域範圍使用
window.initSettingsPage = initSettingsPage;
window.loadAllSettings = loadAllSettings;
window.saveAllSettings = saveAllSettings;
window.applyTemplate = applyTemplate;
window.toggleIndicator = toggleIndicator;
window.toggleAlert = toggleAlert;
window.toggleParamsPanel = toggleParamsPanel;
window.onParamChange = onParamChange;
window.checkUnsavedChanges = checkUnsavedChanges;
