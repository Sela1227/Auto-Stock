/**
 * SELA ç‹€æ…‹ç®¡ç†æ¨¡çµ„ (P1)
 * 
 * åŠŸèƒ½ï¼š
 * 1. é›†ä¸­ç®¡ç†æ‡‰ç”¨ç‹€æ…‹
 * 2. ç‹€æ…‹è®ŠåŒ–äº‹ä»¶é€šçŸ¥
 * 3. è·¨æ¨¡çµ„è³‡æ–™åŒæ­¥
 * 
 * è¼‰å…¥é †åºï¼šutils.js â†’ core.js â†’ state.js â†’ å…¶ä»–æ¨¡çµ„
 */

(function() {
    'use strict';

    // ============================================================
    // ç‹€æ…‹ç®¡ç†æ ¸å¿ƒ
    // ============================================================

    const AppState = {
        // ----- ç”¨æˆ¶ç‹€æ…‹ -----
        user: null,
        isAdmin: false,
        
        // ----- å°Žèˆªç‹€æ…‹ -----
        currentSection: 'dashboard',
        previousSection: null,
        
        // ----- è‚¡ç¥¨ç›¸é—œ -----
        currentStock: null,        // ç›®å‰æŸ¥çœ‹çš„è‚¡ç¥¨
        searchHistory: [],         // æœå°‹æ­·å² (æœ€å¤š 10 ç­†)
        
        // ----- è¿½è¹¤æ¸…å–® -----
        watchlist: [],             // è¿½è¹¤æ¸…å–®
        watchlistLoaded: false,    // æ˜¯å¦å·²è¼‰å…¥
        
        // ----- æŒè‚¡ -----
        portfolio: {
            tw: [],                // å°è‚¡æŒè‚¡
            us: [],                // ç¾Žè‚¡æŒè‚¡
            summary: null          // ç¸½è¦½
        },
        portfolioLoaded: false,
        
        // ----- æ¨™ç±¤ -----
        tags: [],
        tagsLoaded: false,
        
        // ----- å¸‚å ´è³‡æ–™ -----
        indices: {},               // æŒ‡æ•¸è³‡æ–™
        sentiment: null,           // å¸‚å ´æƒ…ç·’
        btcPrice: null,            // BTC åƒ¹æ ¼
        
        // ----- UI ç‹€æ…‹ -----
        isMobileSidebarOpen: false,
        activeModal: null,
        isLoading: false,
        
        // ----- äº‹ä»¶ç³»çµ± -----
        _listeners: new Map(),
        
        /**
         * è¨­ç½®ç‹€æ…‹ä¸¦è§¸ç™¼äº‹ä»¶
         * @param {string} key - ç‹€æ…‹éµ
         * @param {any} value - æ–°å€¼
         */
        set(key, value) {
            const oldValue = this[key];
            this[key] = value;
            this._emit(key, value, oldValue);
            
            // Debug æ¨¡å¼
            if (window.SELA_DEBUG) {
                console.log(`ðŸ“Š State: ${key}`, oldValue, 'â†’', value);
            }
        },
        
        /**
         * æ‰¹é‡è¨­ç½®ç‹€æ…‹
         * @param {Object} updates - {key: value, ...}
         */
        setMultiple(updates) {
            Object.entries(updates).forEach(([key, value]) => {
                this.set(key, value);
            });
        },
        
        /**
         * ç›£è½ç‹€æ…‹è®ŠåŒ–
         * @param {string} key - ç‹€æ…‹éµ
         * @param {Function} callback - (newValue, oldValue) => void
         * @returns {Function} å–æ¶ˆç›£è½çš„å‡½æ•¸
         */
        on(key, callback) {
            if (!this._listeners.has(key)) {
                this._listeners.set(key, new Set());
            }
            this._listeners.get(key).add(callback);
            
            // è¿”å›žå–æ¶ˆç›£è½å‡½æ•¸
            return () => {
                this._listeners.get(key)?.delete(callback);
            };
        },
        
        /**
         * ä¸€æ¬¡æ€§ç›£è½
         */
        once(key, callback) {
            const unsubscribe = this.on(key, (newVal, oldVal) => {
                callback(newVal, oldVal);
                unsubscribe();
            });
            return unsubscribe;
        },
        
        /**
         * è§¸ç™¼äº‹ä»¶
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
            
            // ä¹Ÿè§¸ç™¼é€šç”¨çš„ '*' ç›£è½å™¨
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
         * å–æ¶ˆæ‰€æœ‰ç›£è½
         */
        offAll(key) {
            if (key) {
                this._listeners.delete(key);
            } else {
                this._listeners.clear();
            }
        },
        
        // ============================================================
        // ä¾¿æ·æ–¹æ³•
        // ============================================================
        
        /**
         * è¨­ç½®ç•¶å‰ç”¨æˆ¶
         */
        setUser(user) {
            this.set('user', user);
            this.set('isAdmin', user?.is_admin || false);
        },
        
        /**
         * åˆ‡æ› Section
         */
        switchSection(name) {
            this.set('previousSection', this.currentSection);
            this.set('currentSection', name);
        },
        
        /**
         * è¨­ç½®ç•¶å‰è‚¡ç¥¨
         */
        setCurrentStock(stock) {
            this.set('currentStock', stock);
            
            // åŠ å…¥æœå°‹æ­·å²
            if (stock?.symbol) {
                const history = this.searchHistory.filter(s => s !== stock.symbol);
                history.unshift(stock.symbol);
                this.set('searchHistory', history.slice(0, 10));
                
                // æŒä¹…åŒ–æœå°‹æ­·å²
                try {
                    localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
                } catch (e) {}
            }
        },
        
        /**
         * æ›´æ–°è¿½è¹¤æ¸…å–®
         */
        setWatchlist(list) {
            this.set('watchlist', list);
            this.set('watchlistLoaded', true);
        },
        
        /**
         * æ–°å¢žåˆ°è¿½è¹¤æ¸…å–® (æ¨‚è§€æ›´æ–°)
         */
        addToWatchlist(item) {
            const newList = [...this.watchlist, item];
            this.set('watchlist', newList);
        },
        
        /**
         * å¾žè¿½è¹¤æ¸…å–®ç§»é™¤
         */
        removeFromWatchlist(symbol) {
            const newList = this.watchlist.filter(w => w.symbol !== symbol);
            this.set('watchlist', newList);
        },
        
        /**
         * æ›´æ–°æŒè‚¡è³‡æ–™
         */
        setPortfolio(data) {
            this.set('portfolio', { ...this.portfolio, ...data });
            this.set('portfolioLoaded', true);
        },
        
        /**
         * æ›´æ–°æ¨™ç±¤
         */
        setTags(tags) {
            this.set('tags', tags);
            this.set('tagsLoaded', true);
        },
        
        /**
         * æ›´æ–°å¸‚å ´è³‡æ–™
         */
        setMarketData(data) {
            if (data.indices) this.set('indices', data.indices);
            if (data.sentiment) this.set('sentiment', data.sentiment);
            if (data.btcPrice) this.set('btcPrice', data.btcPrice);
        },
        
        /**
         * è¨­ç½®è¼‰å…¥ç‹€æ…‹
         */
        setLoading(isLoading) {
            this.set('isLoading', isLoading);
        },
        
        /**
         * è¨­ç½® Modal ç‹€æ…‹
         */
        setModal(modalId) {
            this.set('activeModal', modalId);
        },
        
        /**
         * é‡ç½®ç‹€æ…‹ (ç™»å‡ºæ™‚)
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
         * åˆå§‹åŒ– (å¾ž localStorage æ¢å¾©)
         */
        init() {
            // æ¢å¾©æœå°‹æ­·å²
            try {
                const history = localStorage.getItem('searchHistory');
                if (history) {
                    this.searchHistory = JSON.parse(history);
                }
            } catch (e) {}
            
            console.log('ðŸ“Š AppState åˆå§‹åŒ–å®Œæˆ');
        }
    };

    // ============================================================
    // è‡ªå‹•åŒæ­¥ UI (ç¯„ä¾‹)
    // ============================================================

    // ç›£è½ section è®ŠåŒ–ï¼Œè‡ªå‹•æ›´æ–°å°Žèˆªé«˜äº®
    AppState.on('currentSection', (newSection) => {
        // æ›´æ–° URL hash (å¯é¸)
        // history.replaceState(null, '', `#${newSection}`);
    });

    // ç›£è½ç”¨æˆ¶è®ŠåŒ–ï¼Œè‡ªå‹•æ›´æ–° UI
    AppState.on('user', (user) => {
        if (user && typeof updateUserUI === 'function') {
            // updateUserUI å·²åœ¨ core.js ä¸­å®šç¾©
        }
    });

    // ç›£è½è¼‰å…¥ç‹€æ…‹
    AppState.on('isLoading', (isLoading) => {
        // å¯ä»¥åœ¨é€™è£¡é¡¯ç¤º/éš±è—å…¨åŸŸè¼‰å…¥æŒ‡ç¤ºå™¨
    });

    // ============================================================
    // åˆå§‹åŒ–
    // ============================================================

    AppState.init();

    // ============================================================
    // å°Žå‡º
    // ============================================================

    // æŽ›è¼‰åˆ° SELA å‘½åç©ºé–“
    if (window.SELA) {
        window.SELA.state = AppState;
    }

    // å…¨åŸŸå°Žå‡º
    window.AppState = AppState;

    console.log('ðŸ“Š state.js ç‹€æ…‹ç®¡ç†æ¨¡çµ„å·²è¼‰å…¥');
})();