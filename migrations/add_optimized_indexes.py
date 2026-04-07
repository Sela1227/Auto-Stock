"""
資料庫優化索引遷移腳本
執行方式: python -m migrations.add_optimized_indexes

🔧 優化版本 - 2026-04-06
"""
import os
import sys

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SyncSessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 優化索引列表
OPTIMIZED_INDEXES = [
    # ============================================================
    # 價格快取優化
    # ============================================================
    {
        "name": "idx_price_cache_symbol_updated",
        "table": "stock_price_cache",
        "sql": "CREATE INDEX IF NOT EXISTS idx_price_cache_symbol_updated ON stock_price_cache(symbol, updated_at DESC)",
        "description": "加速按股票代碼查詢最新價格",
    },
    {
        "name": "idx_price_cache_updated",
        "table": "stock_price_cache",
        "sql": "CREATE INDEX IF NOT EXISTS idx_price_cache_updated ON stock_price_cache(updated_at DESC)",
        "description": "加速查詢最近更新的股票",
    },
    
    # ============================================================
    # 情緒指數優化
    # ============================================================
    {
        "name": "idx_sentiment_market_date",
        "table": "market_sentiment",
        "sql": "CREATE INDEX IF NOT EXISTS idx_sentiment_market_date ON market_sentiment(market, date DESC)",
        "description": "加速按市場查詢最新情緒",
    },
    
    # ============================================================
    # 追蹤清單優化
    # ============================================================
    {
        "name": "idx_watchlist_user_symbol",
        "table": "watchlists",
        "sql": "CREATE INDEX IF NOT EXISTS idx_watchlist_user_symbol ON watchlists(user_id, symbol)",
        "description": "加速查詢用戶的追蹤清單",
    },
    {
        "name": "idx_watchlist_symbol",
        "table": "watchlists",
        "sql": "CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON watchlists(symbol)",
        "description": "加速統計熱門股票",
    },
    
    # ============================================================
    # 交易紀錄優化
    # ============================================================
    {
        "name": "idx_transactions_user_date",
        "table": "portfolio_transactions",
        "sql": "CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON portfolio_transactions(user_id, transaction_date DESC)",
        "description": "加速查詢用戶交易歷史",
    },
    {
        "name": "idx_transactions_symbol",
        "table": "portfolio_transactions",
        "sql": "CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON portfolio_transactions(symbol)",
        "description": "加速按股票查詢交易",
    },
    
    # ============================================================
    # 持股優化
    # ============================================================
    {
        "name": "idx_holdings_user",
        "table": "portfolio_holdings",
        "sql": "CREATE INDEX IF NOT EXISTS idx_holdings_user ON portfolio_holdings(user_id)",
        "description": "加速查詢用戶持股",
    },
    
    # ============================================================
    # 指數價格優化
    # ============================================================
    {
        "name": "idx_index_prices_symbol_date",
        "table": "index_prices",
        "sql": "CREATE INDEX IF NOT EXISTS idx_index_prices_symbol_date ON index_prices(symbol, date DESC)",
        "description": "加速查詢指數歷史",
    },
    
    # ============================================================
    # 訂閱精選優化
    # ============================================================
    {
        "name": "idx_subscription_picks_date",
        "table": "subscription_picks",
        "sql": "CREATE INDEX IF NOT EXISTS idx_subscription_picks_date ON subscription_picks(pick_date DESC)",
        "description": "加速查詢最新精選",
    },
]


def run_migration():
    """執行索引遷移"""
    logger.info("=" * 60)
    logger.info("開始執行資料庫索引優化遷移")
    logger.info("=" * 60)
    
    db = SyncSessionLocal()
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    try:
        for idx in OPTIMIZED_INDEXES:
            try:
                logger.info(f"\n處理索引: {idx['name']}")
                logger.info(f"  表格: {idx['table']}")
                logger.info(f"  說明: {idx['description']}")
                
                db.execute(text(idx['sql']))
                db.commit()
                
                logger.info(f"  ✅ 成功創建或已存在")
                success_count += 1
                
            except Exception as e:
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    logger.info(f"  ⏭️ 索引已存在，跳過")
                    skip_count += 1
                else:
                    logger.error(f"  ❌ 創建失敗: {e}")
                    fail_count += 1
                db.rollback()
        
        # 顯示摘要
        logger.info("\n" + "=" * 60)
        logger.info("遷移完成摘要")
        logger.info("=" * 60)
        logger.info(f"  ✅ 成功: {success_count}")
        logger.info(f"  ⏭️ 跳過: {skip_count}")
        logger.info(f"  ❌ 失敗: {fail_count}")
        logger.info(f"  📊 總計: {len(OPTIMIZED_INDEXES)}")
        
        if fail_count == 0:
            logger.info("\n🎉 所有索引處理完成！")
        else:
            logger.warning(f"\n⚠️ 有 {fail_count} 個索引創建失敗，請檢查日誌")
        
    finally:
        db.close()


def show_current_indexes():
    """顯示當前索引"""
    db = SyncSessionLocal()
    try:
        result = db.execute(text("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """))
        
        logger.info("\n當前索引列表:")
        logger.info("-" * 50)
        for row in result:
            logger.info(f"  {row[1]}.{row[0]}")
    except Exception as e:
        logger.error(f"查詢索引失敗: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="資料庫索引優化遷移")
    parser.add_argument("--show", action="store_true", help="顯示當前索引")
    parser.add_argument("--run", action="store_true", help="執行遷移")
    
    args = parser.parse_args()
    
    if args.show:
        show_current_indexes()
    elif args.run:
        run_migration()
    else:
        # 預設執行遷移
        run_migration()
