/**
 * SELA 共用工具（非模組，<script> 直接引用）
 */

// localStorage 封裝：JSON 存取，壞資料回預設值
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
    }
};

/**
 * XSS 防護：統一的 HTML 跳脫函數
 * 
 * 所有來自 server/外部的資料插入 innerHTML 前，必須經過此函數。
 * 內部事件屬性（onclick 等）應改用 addEventListener，不用字串插值。
 * 
 * 使用方式：
 *   element.innerHTML = `<p>${escapeHTML(source.name)}</p>`;
 * 
 * 安全的替代方式（純文字不需要 escape）：
 *   element.textContent = source.name;
 */
function escapeHTML(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
}
