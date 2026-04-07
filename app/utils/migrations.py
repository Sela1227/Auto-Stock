"""
è³‡æ–™åº«è‡ªå‹•é·ç§»
åœ¨å•Ÿå‹•æ™‚æª¢æŸ¥ä¸¦æ·»åŠ ç¼ºå°‘çš„æ¬„ä½
"""
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def run_migrations(db: Session):
    """åŸ·è¡Œè³‡æ–™åº«é·ç§»"""
    migrations = [
        # 2024-01-14: è¿½è¹¤æ¸…å–® MA20 æŽ’åºåŠŸèƒ½
        {
            "name": "add_ma20_to_price_cache",
            "check": "SELECT column_name FROM information_schema.columns WHERE table_name='stock_price_cache' AND column_name='ma20'",
            "sql": "ALTER TABLE stock_price_cache ADD COLUMN ma20 NUMERIC(12, 4)",
        },
    ]
    
    for migration in migrations:
        try:
            # æª¢æŸ¥æ˜¯å¦å·²å­˜åœ¨
            result = db.execute(text(migration["check"])).fetchone()
            if result:
                logger.debug(f"Migration '{migration['name']}' å·²å­˜åœ¨ï¼Œè·³éŽ")
                continue
            
            # åŸ·è¡Œé·ç§»
            logger.info(f"åŸ·è¡Œ Migration: {migration['name']}")
            db.execute(text(migration["sql"]))
            db.commit()
            logger.info(f"Migration '{migration['name']}' å®Œæˆ")
            
        except Exception as e:
            logger.warning(f"Migration '{migration['name']}' å¤±æ•—: {e}")
            db.rollback()