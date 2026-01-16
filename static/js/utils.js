/**
 * SELA 工具函數庫
 * 這是一個非模組版本，可以直接通過 <script> 標籤引用
 */

// ============================================================
// 格式化工具
// ============================================================

/**
 * 數字格式化（帶千分位）
 */
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) return '--';
    return Number(num).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * 價格格式化
 */
function formatPrice(price, currency = 'USD') {
    if (price === null || price === undefined) return '--';
    const prefix = currency === 'TWD' ? 'NT$' : '$';
    return prefix + formatNumber(price);
}

/**
 * 百分比格式化
 */
function formatPercent(value, showSign = true) {
    if (value === null || value === undefined || isNaN(value)) return '--';
    const sign = showSign && value > 0 ? '+' : '';
    return sign + value.toFixed(2) + '%';
}

/**
 * 日期格式化
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
 * 大數字縮寫
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
 * 股數格式化（台股用張）
 */
function formatShares(shares, market = 'us') {
    if (shares === null || shares === undefined) return '--';
    if (market === 'tw') {
        const lots = Math.floor(shares / 1000);
        const odd = shares % 1000;
        if (lots > 0 && odd > 0) {
            return `${lots} 張 ${odd} 股`;
        } else if (lots > 0) {
            return `${lots} 張`;
        } else {
            return `${odd} 股`;
        }
    }
    return shares.toLocaleString() + ' 股';
}

/**
 * 漲跌樣式 class
 */
function getChangeClass(value) {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-500';
}

/**
 * 漲跌圖示
 */
function getChangeIcon(value) {
    if (value > 0) return '▲';
    if (value < 0) return '▼';
    return '—';
}

// ============================================================
// 防抖與節流
// ============================================================

/**
 * 防抖函數
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
 * 節流函數
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
// LocalStorage 封裝
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
// 檔案處理
// ============================================================

/**
 * 解析 CSV 檔案
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
 * 解析 JSON 檔案
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
 * 預覽檔案內容
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
        callback(null, new Error('檔案讀取失敗'));
    };
    reader.readAsText(file);
}

console.log('SELA 工具函數庫已載入');
