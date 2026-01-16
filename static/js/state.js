/**
 * SELA 狀態管理模組 (P1)
 * 
 * 功能：
 * 1. 集中管理應用狀態
 * 2. 狀態變化事件通知
 * 3. 跨模組資料同步
 * 
 * 載入順序：utils.js → core.js → state.js → 其他模組
 */

(function() {
    'use strict';

    // ============================================================
    // 狀態管理核心
    // ============================================================

    const AppState = {
        // ----- 用戶狀態 -----
        user: null,
        isAdmin: false,
        
        // ----- 導航狀態 -----
        currentSection: 'dashboard',
        previousSection: null,
        
        // ----- 股票相關 -----
        currentStock: null,        // 目前查看的股票
        searchHistory: [],         // 搜尋歷史 (最多 10 筆)
        
        // ----- 追蹤清單 -----
        watchlist: [],             // 追蹤清單
        watchlistLoaded: false,    // 是否已載入
        
        // ----- 持股 -----
        portfolio: {
            tw: [],                // 台股持股
            us: [],                // 美股持股
            summary: null          // 總覽
        },
        portfolioLoaded: false,
        
        // ----- 標籤 -----
        tags: [],
        tagsLoaded: false,
        
        // ----- 市場資料 -----
        indices: {},               // 指數資料
        sentiment: null,           // 市場情緒
        btcPrice: null,            // BTC 價格
        
        // ----- UI 狀態 -----
        isMobileSidebarOpen: false,
        activeModal: null,
        isLoading: false,
        
        // ----- 事件系統 -----
        _listeners: new Map(),
        
        /**
         * 設置狀態並觸發事件
         * @param {string} key - 狀態鍵
         * @param {any} value - 新值
         */
        set(key, value) {
            const oldValue = this[key];
            this[key] = value;
            this._emit(key, value, oldValue);
            
            // Debug 模式
            if (window.SELA_DEBUG) {
                console.log(`📊 State: ${key}`, oldValue, '→', value);
            }
        },
        
        /**
         * 批量設置狀態
         * @param {Object} updates - {key: value, ...}
         */
        setMultiple(updates) {
            Object.entries(updates).forEach(([key, value]) => {
                this.set(key, value);
            });
        },
        
        /**
         * 監聽狀態變化
         * @param {string} key - 狀態鍵
         * @param {Function} callback - (newValue, oldValue) => void
         * @returns {Function} 取消監聽的函數
         */
        on(key, callback) {
            if (!this._listeners.has(key)) {
                this._listeners.set(key, new Set());
            }
            this._listeners.get(key).add(callback);
            
            // 返回取消監聽函數
            return () => {
                this._listeners.get(key)?.delete(callback);
            };
        },
        
        /**
         * 一次性監聽
         */
        once(key, callback) {
            const unsubscribe = this.on(key, (newVal, oldVal) => {
                callback(newVal, oldVal);
                unsubscribe();
            });
            return unsubscribe;
        },
        
        /**
         * 觸發事件
         */
        _emit(key, newValue, oldValue) {
            const listeners = this._listeners.get(key);
            if (listeners) {
                listeners.forEach(cb => {
                    try {
                        cb(newValue, oldValue);
                    } catch (e) {
                        console.error(`State listener error for ${key}:`, e);
                    }
                });
            }
            
            // 也觸發通用的 '*' 監聽器
            const globalListeners = this._listeners.get('*');
            if (globalListeners) {
                globalListeners.forEach(cb => {
                    try {
                        cb(key, newValue, oldValue);
                    } catch (e) {
                        console.error('Global state listener error:', e);
                    }
                });
            }
        },
        
        /**
         * 取消所有監聽
         */
        offAll(key) {
            if (key) {
                this._listeners.delete(key);
            } else {
                this._listeners.clear();
            }
        },
        
        // ============================================================
        // 便捷方法
        // ============================================================
        
        /**
         * 設置當前用戶
         */
        setUser(user) {
            this.set('user', user);
            this.set('isAdmin', user?.is_admin || false);
        },
        
        /**
         * 切換 Section
         */
        switchSection(name) {
            this.set('previousSection', this.currentSection);
            this.set('currentSection', name);
        },
        
        /**
         * 設置當前股票
         */
        setCurrentStock(stock) {
            this.set('currentStock', stock);
            
            // 加入搜尋歷史
            if (stock?.symbol) {
                const history = this.searchHistory.filter(s => s !== stock.symbol);
                history.unshift(stock.symbol);
                this.set('searchHistory', history.slice(0, 10));
                
                // 持久化搜尋歷史
                try {
                    localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
                } catch (e) {}
            }
        },
        
        /**
         * 更新追蹤清單
         */
        setWatchlist(list) {
            this.set('watchlist', list);
            this.set('watchlistLoaded', true);
        },
        
        /**
         * 新增到追蹤清單 (樂觀更新)
         */
        addToWatchlist(item) {
            const newList = [...this.watchlist, item];
            this.set('watchlist', newList);
        },
        
        /**
         * 從追蹤清單移除
         */
        removeFromWatchlist(symbol) {
            const newList = this.watchlist.filter(w => w.symbol !== symbol);
            this.set('watchlist', newList);
        },
        
        /**
         * 更新持股資料
         */
        setPortfolio(data) {
            this.set('portfolio', { ...this.portfolio, ...data });
            this.set('portfolioLoaded', true);
        },
        
        /**
         * 更新標籤
         */
        setTags(tags) {
            this.set('tags', tags);
            this.set('tagsLoaded', true);
        },
        
        /**
         * 更新市場資料
         */
        setMarketData(data) {
            if (data.indices) this.set('indices', data.indices);
            if (data.sentiment) this.set('sentiment', data.sentiment);
            if (data.btcPrice) this.set('btcPrice', data.btcPrice);
        },
        
        /**
         * 設置載入狀態
         */
        setLoading(isLoading) {
            this.set('isLoading', isLoading);
        },
        
        /**
         * 設置 Modal 狀態
         */
        setModal(modalId) {
            this.set('activeModal', modalId);
        },
        
        /**
         * 重置狀態 (登出時)
         */
        reset() {
            this.user = null;
            this.isAdmin = false;
            this.currentStock = null;
            this.watchlist = [];
            this.watchlistLoaded = false;
            this.portfolio = { tw: [], us: [], summary: null };
            this.portfolioLoaded = false;
            this.tags = [];
            this.tagsLoaded = false;
            this._emit('reset', null, null);
        },
        
        /**
         * 初始化 (從 localStorage 恢復)
         */
        init() {
            // 恢復搜尋歷史
            try {
                const history = localStorage.getItem('searchHistory');
                if (history) {
                    this.searchHistory = JSON.parse(history);
                }
            } catch (e) {}
            
            console.log('📊 AppState 初始化完成');
        }
    };

    // ============================================================
    // 自動同步 UI (範例)
    // ============================================================

    // 監聽 section 變化，自動更新導航高亮
    AppState.on('currentSection', (newSection) => {
        // 更新 URL hash (可選)
        // history.replaceState(null, '', `#${newSection}`);
    });

    // 監聽用戶變化，自動更新 UI
    AppState.on('user', (user) => {
        if (user && typeof updateUserUI === 'function') {
            // updateUserUI 已在 core.js 中定義
        }
    });

    // 監聽載入狀態
    AppState.on('isLoading', (isLoading) => {
        // 可以在這裡顯示/隱藏全域載入指示器
    });

    // ============================================================
    // 初始化
    // ============================================================

    AppState.init();

    // ============================================================
    // 導出
    // ============================================================

    // 掛載到 SELA 命名空間
    if (window.SELA) {
        window.SELA.state = AppState;
    }

    // 全域導出
    window.AppState = AppState;

    console.log('📊 state.js 狀態管理模組已載入');
})();
