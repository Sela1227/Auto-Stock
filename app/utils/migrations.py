"""
資料庫自動遷移
在啟動時檢查並添加缺少的欄位
"""
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def run_migrations(db: Session):
    """執行資料庫遷移"""
    migrations = [
        # 2024-01-14: 追蹤清單 MA20 排序功能
        {
            "name": "add_ma20_to_price_cache",
            "check": "SELECT column_name FROM information_schema.columns WHERE table_name='stock_price_cache' AND column_name='ma20'",
            "sql": "ALTER TABLE stock_price_cache ADD COLUMN ma20 NUMERIC(12, 4)",
        },
    ]
    
    for migration in migrations:
        try:
            # 檢查是否已存在
            result = db.execute(text(migration["check"])).fetchone()
            if result:
                logger.debug(f"Migration '{migration['name']}' 已存在，跳過")
                continue
            
            # 執行遷移
            logger.info(f"執行 Migration: {migration['name']}")
            db.execute(text(migration["sql"]))
            db.commit()
            logger.info(f"Migration '{migration['name']}' 完成")
            
        except Exception as e:
            logger.warning(f"Migration '{migration['name']}' 失敗: {e}")
            db.rollback()
