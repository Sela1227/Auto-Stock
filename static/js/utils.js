/**
 * SELA å·¥å…·å‡½æ•¸åº«
 * é€™æ˜¯ä¸€å€‹éžæ¨¡çµ„ç‰ˆæœ¬ï¼Œå¯ä»¥ç›´æŽ¥é€šéŽ <script> æ¨™ç±¤å¼•ç”¨
 */

// ============================================================
// æ ¼å¼åŒ–å·¥å…·
// ============================================================

/**
 * æ•¸å­—æ ¼å¼åŒ–ï¼ˆå¸¶åƒåˆ†ä½ï¼‰
 */
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) return '--';
    return Number(num).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * åƒ¹æ ¼æ ¼å¼åŒ–
 */
function formatPrice(price, currency = 'USD') {
    if (price === null || price === undefined) return '--';
    const prefix = currency === 'TWD' ? 'NT$' : '$';
    return prefix + formatNumber(price);
}

/**
 * ç™¾åˆ†æ¯”æ ¼å¼åŒ–
 */
function formatPercent(value, showSign = true) {
    if (value === null || value === undefined || isNaN(value)) return '--';
    const sign = showSign && value > 0 ? '+' : '';
    return sign + value.toFixed(2) + '%';
}

/**
 * æ—¥æœŸæ ¼å¼åŒ–
 */
function formatDate(dateStr, format = 'short') {
    if (!dateStr) return '--';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '--';
    
    if (format === 'short') {
        return date.toLocaleDateString('zh-TW');
    } else if (format === 'full') {
        return date.toLocaleDateString('zh-TW', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } else if (format === 'iso') {
        return date.toISOString().split('T')[0];
    }
    return date.toLocaleDateString('zh-TW');
}

/**
 * å¤§æ•¸å­—ç¸®å¯«
 */
function formatLargeNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '--';
    const abs = Math.abs(num);
    if (abs >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (abs >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (abs >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (abs >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toFixed(2);
}

/**
 * è‚¡æ•¸æ ¼å¼åŒ–ï¼ˆå°è‚¡ç”¨å¼µï¼‰
 */
function formatShares(shares, market = 'us') {
    if (shares === null || shares === undefined) return '--';
    if (market === 'tw') {
        const lots = Math.floor(shares / 1000);
        const odd = shares % 1000;
        if (lots > 0 && odd > 0) {
            return `${lots} å¼µ ${odd} è‚¡`;
        } else if (lots > 0) {
            return `${lots} å¼µ`;
        } else {
            return `${odd} è‚¡`;
        }
    }
    return shares.toLocaleString() + ' è‚¡';
}

/**
 * æ¼²è·Œæ¨£å¼ class
 */
function getChangeClass(value) {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-500';
}

/**
 * æ¼²è·Œåœ–ç¤º
 */
function getChangeIcon(value) {
    if (value > 0) return 'â–²';
    if (value < 0) return 'â–¼';
    return 'â€”';
}

// ============================================================
// é˜²æŠ–èˆ‡ç¯€æµ
// ============================================================

/**
 * é˜²æŠ–å‡½æ•¸
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * ç¯€æµå‡½æ•¸
 */
function throttle(func, limit = 300) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ============================================================
// LocalStorage å°è£
// ============================================================

const storage = {
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('Storage get error:', e);
            return defaultValue;
        }
    },
    
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Storage set error:', e);
            return false;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Storage remove error:', e);
            return false;
        }
    }
};

// ============================================================
// æª”æ¡ˆè™•ç†
// ============================================================

/**
 * è§£æž CSV æª”æ¡ˆ
 */
function parseCSV(content) {
    const lines = content.split('\n').filter(l => l.trim());
    if (lines.length < 2) return [];
    
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const items = [];
    
    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',');
        const obj = {};
        headers.forEach((h, idx) => {
            obj[h] = values[idx]?.trim();
        });
        items.push(obj);
    }
    
    return items;
}

/**
 * è§£æž JSON æª”æ¡ˆ
 */
function parseJSON(content) {
    try {
        const data = JSON.parse(content);
        return data.items || data;
    } catch (e) {
        console.error('JSON parse error:', e);
        return [];
    }
}

/**
 * é è¦½æª”æ¡ˆå…§å®¹
 */
function previewFile(file, callback) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        let items = [];
        
        if (file.name.endsWith('.json')) {
            items = parseJSON(content);
        } else if (file.name.endsWith('.csv')) {
            items = parseCSV(content);
        }
        
        callback(items, null);
    };
    reader.onerror = function() {
        callback(null, new Error('æª”æ¡ˆè®€å–å¤±æ•—'));
    };
    reader.readAsText(file);
}

console.log('SELA å·¥å…·å‡½æ•¸åº«å·²è¼‰å…¥');