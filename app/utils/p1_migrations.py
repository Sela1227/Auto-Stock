"""
P1 功能資料庫遷移
==================
新增以下表格：
1. stock_info - 股票基本資訊種子表
2. user_tags - 用戶自訂標籤
3. watchlist_tags - 追蹤項目標籤關聯

在 app/database.py 的 run_migrations() 中呼叫
"""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ============================================================
# 預設種子資料
# ============================================================

DEFAULT_STOCK_INFO = [
    # 美股 - 科技巨頭
    {"symbol": "AAPL", "name": "Apple Inc.", "name_zh": "蘋果", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "name_zh": "微軟", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "name_zh": "Google", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "name_zh": "亞馬遜", "market": "us", "exchange": "NASDAQ", "sector": "Consumer Cyclical", "is_popular": True},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "name_zh": "輝達", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "META", "name": "Meta Platforms Inc.", "name_zh": "Meta", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "TSLA", "name": "Tesla Inc.", "name_zh": "特斯拉", "market": "us", "exchange": "NASDAQ", "sector": "Consumer Cyclical", "is_popular": True},
    
    # 美股 - 金融
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "name_zh": "摩根大通", "market": "us", "exchange": "NYSE", "sector": "Financial Services", "is_popular": True},
    {"symbol": "V", "name": "Visa Inc.", "name_zh": "Visa", "market": "us", "exchange": "NYSE", "sector": "Financial Services", "is_popular": True},
    {"symbol": "MA", "name": "Mastercard Inc.", "name_zh": "萬事達卡", "market": "us", "exchange": "NYSE", "sector": "Financial Services", "is_popular": True},
    
    # 美股 - 半導體
    {"symbol": "AMD", "name": "Advanced Micro Devices", "name_zh": "超微", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "INTC", "name": "Intel Corporation", "name_zh": "英特爾", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "name_zh": "博通", "market": "us", "exchange": "NASDAQ", "sector": "Technology", "is_popular": True},
    
    # 台股 - 半導體
    {"symbol": "2330.TW", "name": "Taiwan Semiconductor", "name_zh": "台積電", "market": "tw", "exchange": "TWSE", "sector": "半導體", "is_popular": True},
    {"symbol": "2454.TW", "name": "MediaTek Inc.", "name_zh": "聯發科", "market": "tw", "exchange": "TWSE", "sector": "半導體", "is_popular": True},
    {"symbol": "2303.TW", "name": "United Microelectronics", "name_zh": "聯電", "market": "tw", "exchange": "TWSE", "sector": "半導體", "is_popular": True},
    {"symbol": "3711.TW", "name": "ASE Technology", "name_zh": "日月光投控", "market": "tw", "exchange": "TWSE", "sector": "半導體", "is_popular": True},
    
    # 台股 - 電子代工
    {"symbol": "2317.TW", "name": "Hon Hai Precision", "name_zh": "鴻海", "market": "tw", "exchange": "TWSE", "sector": "電子", "is_popular": True},
    {"symbol": "2382.TW", "name": "Quanta Computer", "name_zh": "廣達", "market": "tw", "exchange": "TWSE", "sector": "電子", "is_popular": True},
    {"symbol": "2357.TW", "name": "Asustek Computer", "name_zh": "華碩", "market": "tw", "exchange": "TWSE", "sector": "電子", "is_popular": True},
    
    # 台股 - 金融
    {"symbol": "2881.TW", "name": "Fubon Financial", "name_zh": "富邦金", "market": "tw", "exchange": "TWSE", "sector": "金融", "is_popular": True},
    {"symbol": "2882.TW", "name": "Cathay Financial", "name_zh": "國泰金", "market": "tw", "exchange": "TWSE", "sector": "金融", "is_popular": True},
    {"symbol": "2884.TW", "name": "E.Sun Financial", "name_zh": "玉山金", "market": "tw", "exchange": "TWSE", "sector": "金融", "is_popular": True},
    
    # 台股 - ETF
    {"symbol": "0050.TW", "name": "Yuanta Taiwan 50 ETF", "name_zh": "元大台灣50", "market": "tw", "exchange": "TWSE", "sector": "ETF", "is_popular": True},
    {"symbol": "0056.TW", "name": "Yuanta High Dividend ETF", "name_zh": "元大高股息", "market": "tw", "exchange": "TWSE", "sector": "ETF", "is_popular": True},
    {"symbol": "00878.TW", "name": "Cathay ESG High Dividend ETF", "name_zh": "國泰永續高股息", "market": "tw", "exchange": "TWSE", "sector": "ETF", "is_popular": True},
    
    # 加密貨幣
    {"symbol": "BTC", "name": "Bitcoin", "name_zh": "比特幣", "market": "crypto", "exchange": "CoinGecko", "sector": "Cryptocurrency", "is_popular": True},
    {"symbol": "ETH", "name": "Ethereum", "name_zh": "以太坊", "market": "crypto", "exchange": "CoinGecko", "sector": "Cryptocurrency", "is_popular": True},
    {"symbol": "SOL", "name": "Solana", "name_zh": "索拉納", "market": "crypto", "exchange": "CoinGecko", "sector": "Cryptocurrency", "is_popular": True},
    
    # 指數
    {"symbol": "^GSPC", "name": "S&P 500", "name_zh": "標普500", "market": "us", "exchange": "INDEX", "sector": "Index", "is_popular": True},
    {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "name_zh": "道瓊工業", "market": "us", "exchange": "INDEX", "sector": "Index", "is_popular": True},
    {"symbol": "^IXIC", "name": "NASDAQ Composite", "name_zh": "納斯達克", "market": "us", "exchange": "INDEX", "sector": "Index", "is_popular": True},
    {"symbol": "^TWII", "name": "Taiwan Weighted Index", "name_zh": "台灣加權", "market": "tw", "exchange": "INDEX", "sector": "Index", "is_popular": True},
]


def run_p1_migrations(db: Session) -> dict:
    """
    執行 P1 功能的資料庫遷移
    
    Returns:
        遷移結果
    """
    results = {
        "success": True,
        "tables_created": [],
        "columns_added": [],
        "seed_data": 0,
        "errors": [],
    }
    
    try:
        # ============================================================
        # 1. stock_info 表
        # ============================================================
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS stock_info (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100),
                    name_zh VARCHAR(100),
                    market VARCHAR(10) DEFAULT 'us',
                    exchange VARCHAR(20),
                    sector VARCHAR(50),
                    industry VARCHAR(50),
                    market_cap FLOAT,
                    pe_ratio FLOAT,
                    dividend_yield FLOAT,
                    description TEXT,
                    website VARCHAR(200),
                    logo_url VARCHAR(300),
                    is_active BOOLEAN DEFAULT TRUE,
                    is_popular BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 建立索引
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_info_symbol ON stock_info(symbol)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_info_market ON stock_info(market)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_info_sector ON stock_info(sector)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_info_popular ON stock_info(is_popular)"))
            
            db.commit()
            results["tables_created"].append("stock_info")
            logger.info("✅ stock_info 表已建立")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("ℹ️ stock_info 表已存在")
            else:
                results["errors"].append(f"stock_info: {e}")
                logger.error(f"❌ stock_info 建立失敗: {e}")
        
        # ============================================================
        # 2. user_tags 表
        # ============================================================
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS user_tags (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(50) NOT NULL,
                    color VARCHAR(20) DEFAULT '#3B82F6',
                    icon VARCHAR(50) DEFAULT 'fa-tag',
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name)
                )
            """))
            
            # 建立索引
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_user_tags_user_id ON user_tags(user_id)"))
            
            db.commit()
            results["tables_created"].append("user_tags")
            logger.info("✅ user_tags 表已建立")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("ℹ️ user_tags 表已存在")
            else:
                results["errors"].append(f"user_tags: {e}")
                logger.error(f"❌ user_tags 建立失敗: {e}")
        
        # ============================================================
        # 3. watchlist_tags 關聯表
        # ============================================================
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS watchlist_tags (
                    watchlist_id INTEGER NOT NULL REFERENCES watchlist(id) ON DELETE CASCADE,
                    tag_id INTEGER NOT NULL REFERENCES user_tags(id) ON DELETE CASCADE,
                    PRIMARY KEY (watchlist_id, tag_id)
                )
            """))
            
            db.commit()
            results["tables_created"].append("watchlist_tags")
            logger.info("✅ watchlist_tags 表已建立")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("ℹ️ watchlist_tags 表已存在")
            else:
                results["errors"].append(f"watchlist_tags: {e}")
                logger.error(f"❌ watchlist_tags 建立失敗: {e}")
        
        # ============================================================
        # 4. 檢查 watchlist 表是否有 target_price 欄位
        # ============================================================
        try:
            # 檢查欄位是否存在
            result = db.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'watchlist' AND column_name = 'target_price'
            """))
            if not result.fetchone():
                db.execute(text("""
                    ALTER TABLE watchlist ADD COLUMN target_price DECIMAL(20, 8)
                """))
                db.commit()
                results["columns_added"].append("watchlist.target_price")
                logger.info("✅ watchlist.target_price 欄位已新增")
            else:
                logger.info("ℹ️ watchlist.target_price 欄位已存在")
        except Exception as e:
            if "already exists" in str(e).lower():
                pass
            else:
                results["errors"].append(f"target_price: {e}")
                logger.warning(f"⚠️ 新增 target_price 欄位失敗: {e}")
        
        # ============================================================
        # 5. 自動填入種子資料
        # ============================================================
        try:
            # 檢查是否為空表
            count_result = db.execute(text("SELECT COUNT(*) FROM stock_info"))
            count = count_result.scalar()
            
            if count == 0:
                logger.info("📊 stock_info 為空，開始填入種子資料...")
                for stock_data in DEFAULT_STOCK_INFO:
                    db.execute(text("""
                        INSERT INTO stock_info (symbol, name, name_zh, market, exchange, sector, is_popular)
                        VALUES (:symbol, :name, :name_zh, :market, :exchange, :sector, :is_popular)
                        ON CONFLICT (symbol) DO NOTHING
                    """), stock_data)
                db.commit()
                results["seed_data"] = len(DEFAULT_STOCK_INFO)
                logger.info(f"✅ 已填入 {len(DEFAULT_STOCK_INFO)} 筆種子資料")
            else:
                logger.info(f"ℹ️ stock_info 已有 {count} 筆資料，跳過種子填入")
        except Exception as e:
            logger.warning(f"⚠️ 種子資料填入失敗: {e}")
        
        # ============================================================
        # 總結
        # ============================================================
        if results["errors"]:
            results["success"] = False
            logger.warning(f"P1 遷移完成，但有錯誤: {results['errors']}")
        else:
            logger.info(f"✅ P1 遷移完成: 建立 {len(results['tables_created'])} 個表, 種子 {results['seed_data']} 筆")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ P1 遷移失敗: {e}")
        db.rollback()
        results["success"] = False
        results["errors"].append(str(e))
        return results
