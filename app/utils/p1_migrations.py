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
        # 總結
        # ============================================================
        if results["errors"]:
            results["success"] = False
            logger.warning(f"P1 遷移完成，但有錯誤: {results['errors']}")
        else:
            logger.info(f"✅ P1 遷移完成: 建立 {len(results['tables_created'])} 個表")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ P1 遷移失敗: {e}")
        db.rollback()
        results["success"] = False
        results["errors"].append(str(e))
        return results


# ============================================================
# 整合到現有的 run_migrations
# ============================================================

MIGRATION_CODE = '''
# 在 app/database.py 的 run_migrations() 函數中加入：

def run_migrations(db: Session):
    """執行所有資料庫遷移"""
    logger.info("開始執行資料庫遷移...")
    
    # ... 現有的遷移 ...
    
    # P1 遷移
    try:
        from app.utils.p1_migrations import run_p1_migrations
        p1_result = run_p1_migrations(db)
        if p1_result["success"]:
            logger.info(f"P1 遷移成功: {p1_result}")
        else:
            logger.warning(f"P1 遷移有錯誤: {p1_result}")
    except ImportError:
        logger.info("P1 遷移模組未安裝")
    except Exception as e:
        logger.error(f"P1 遷移失敗: {e}")
'''
