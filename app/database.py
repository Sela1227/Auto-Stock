"""
è³‡æ–™åº«é€£ç·šèˆ‡ Session ç®¡ç†
æ”¯æ´ SQLite (é–‹ç™¼) å’Œ PostgreSQL (ç”Ÿç”¢)

ðŸ”§ ä¿®å¾©ç‰ˆæœ¬ - 2026-01-16
æ–°å¢ž get_sync_db åˆ¥å

ðŸš€ æ•ˆèƒ½å„ªåŒ– - 2026-01-16
æ–°å¢ž stock_prices æ­·å²è³‡æ–™è¡¨
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings


def get_async_url(url: str) -> str:
    """å°‡ä¸€èˆ¬çš„è³‡æ–™åº« URL è½‰æ›ç‚º async æ ¼å¼"""
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://")
    elif url.startswith("postgres://"):
        # Railway ä½¿ç”¨ postgres:// ä½† SQLAlchemy éœ€è¦ postgresql://
        return url.replace("postgres://", "postgresql+asyncpg://")
    return url


def get_sync_url(url: str) -> str:
    """ç¢ºä¿æ˜¯åŒæ­¥æ ¼å¼çš„ URL"""
    url = url.replace("+aiosqlite", "").replace("+asyncpg", "")
    # ä¿®æ­£ Railway çš„ postgres:// æ ¼å¼
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://")
    return url


def is_postgres(url: str) -> bool:
    """æª¢æŸ¥æ˜¯å¦ç‚º PostgreSQL"""
    return "postgresql" in url or "postgres" in url


# å–å¾—è³‡æ–™åº« URL
database_url = settings.DATABASE_URL

# éžåŒæ­¥å¼•æ“Ž (FastAPI ç”¨)
async_database_url = get_async_url(database_url)

# PostgreSQL éœ€è¦ç‰¹åˆ¥çš„é€£ç·šæ± è¨­å®š
if is_postgres(database_url):
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
        poolclass=NullPool,  # Railway å»ºè­°ä½¿ç”¨ NullPool
    )
else:
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
    )

# éžåŒæ­¥ Session
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# åŒæ­¥å¼•æ“Ž (CLI ç”¨)
sync_database_url = get_sync_url(database_url)

if is_postgres(database_url):
    sync_engine = create_engine(
        sync_database_url,
        echo=settings.DEBUG,
        poolclass=NullPool,
    )
else:
    sync_engine = create_engine(
        sync_database_url,
        echo=settings.DEBUG,
    )

# ============================================================
# ðŸ†• è‡ªå‹•è³‡æ–™åº«é·ç§»
# ============================================================
def run_auto_migrations():
    """å•Ÿå‹•æ™‚è‡ªå‹•åŸ·è¡Œè³‡æ–™åº«é·ç§»"""
    migrations = [
        # 2026-01-14: MA20 æŽ’åºåŠŸèƒ½
        {
            "name": "add_ma20_to_price_cache",
            "check_sql": "SELECT column_name FROM information_schema.columns WHERE table_name='stock_price_cache' AND column_name='ma20'",
            "migrate_sql": "ALTER TABLE stock_price_cache ADD COLUMN ma20 NUMERIC(12, 4)",
        },
        # 2026-01-14: è¨‚é–±ç²¾é¸åŠŸèƒ½ - è¨‚é–±æºè¡¨
        {
            "name": "create_subscription_sources",
            "check_sql": "SELECT table_name FROM information_schema.tables WHERE table_name='subscription_sources'",
            "migrate_sql": """
                CREATE TABLE subscription_sources (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    slug VARCHAR(50) UNIQUE NOT NULL,
                    url VARCHAR(500) NOT NULL,
                    type VARCHAR(20) DEFAULT 'substack',
                    description TEXT,
                    enabled BOOLEAN DEFAULT true,
                    last_fetched_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
        },
        # 2026-01-14: è¨‚é–±ç²¾é¸åŠŸèƒ½ - è‡ªå‹•ç²¾é¸è¡¨
        {
            "name": "create_auto_picks",
            "check_sql": "SELECT table_name FROM information_schema.tables WHERE table_name='auto_picks'",
            "migrate_sql": """
                CREATE TABLE auto_picks (
                    id SERIAL PRIMARY KEY,
                    source_id INTEGER REFERENCES subscription_sources(id),
                    symbol VARCHAR(20) NOT NULL,
                    article_url VARCHAR(500),
                    article_title VARCHAR(300),
                    article_date DATE,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    mention_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_id, symbol)
                )
            """,
        },
        # 2026-01-14: è¨‚é–±ç²¾é¸åŠŸèƒ½ - ç”¨æˆ¶è¨‚é–±è¡¨
        {
            "name": "create_user_subscriptions",
            "check_sql": "SELECT table_name FROM information_schema.tables WHERE table_name='user_subscriptions'",
            "migrate_sql": """
                CREATE TABLE user_subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    source_id INTEGER REFERENCES subscription_sources(id),
                    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, source_id)
                )
            """,
        },
        # 2026-01-15: P1 ç›®æ¨™åƒ¹åŠŸèƒ½
        {
            "name": "add_target_price_to_watchlists",
            "check_sql": "SELECT column_name FROM information_schema.columns WHERE table_name='watchlists' AND column_name='target_price'",
            "migrate_sql": "ALTER TABLE watchlists ADD COLUMN target_price NUMERIC(12, 4) DEFAULT NULL",
        },
            {
                "name": "add_target_direction_to_watchlists",
                "check_sql": "SELECT column_name FROM information_schema.columns WHERE table_name='watchlists' AND column_name='target_direction'",
                "migrate_sql": "ALTER TABLE watchlists ADD COLUMN target_direction VARCHAR(10) DEFAULT 'above'",
            },
        # ============================================================
        # ðŸš€ 2026-01-16: è‚¡ç¥¨æ­·å²è³‡æ–™å¿«å–è¡¨ï¼ˆæ•ˆèƒ½å„ªåŒ–ï¼‰
        # ============================================================
        {
            "name": "create_stock_prices",
            "check_sql": "SELECT table_name FROM information_schema.tables WHERE table_name='stock_prices'",
            "migrate_sql": """
                CREATE TABLE stock_prices (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    open NUMERIC(12, 4),
                    high NUMERIC(12, 4),
                    low NUMERIC(12, 4),
                    close NUMERIC(12, 4),
                    volume BIGINT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                )
            """,
        },
        {
            "name": "create_stock_prices_symbol_index",
            "check_sql": "SELECT indexname FROM pg_indexes WHERE indexname='idx_stock_prices_symbol'",
            "migrate_sql": "CREATE INDEX idx_stock_prices_symbol ON stock_prices(symbol)",
        },
        {
            "name": "create_stock_prices_date_index",
            "check_sql": "SELECT indexname FROM pg_indexes WHERE indexname='idx_stock_prices_date'",
            "migrate_sql": "CREATE INDEX idx_stock_prices_date ON stock_prices(date)",
        },

        # 2026-01-17: åˆ¸å•†åŠŸèƒ½
        {
            "name": "create_brokers",
            "check_sql": "SELECT table_name FROM information_schema.tables WHERE table_name='brokers'",
            "migrate_sql": """
                CREATE TABLE brokers (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(50) NOT NULL,
                    color VARCHAR(20) DEFAULT '#6B7280',
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
        },
        {
            "name": "create_brokers_user_index",
            "check_sql": "SELECT indexname FROM pg_indexes WHERE indexname='idx_broker_user'",
            "migrate_sql": "CREATE INDEX idx_broker_user ON brokers(user_id)",
        },
        {
            "name": "add_broker_id_to_transactions",
            "check_sql": "SELECT column_name FROM information_schema.columns WHERE table_name='portfolio_transactions' AND column_name='broker_id'",
            "migrate_sql": "ALTER TABLE portfolio_transactions ADD COLUMN broker_id INTEGER REFERENCES brokers(id) ON DELETE SET NULL",
        },    ]
    
    try:
        with sync_engine.connect() as conn:
            for migration in migrations:
                try:
                    result = conn.execute(text(migration["check_sql"])).fetchone()
                    if not result:
                        conn.execute(text(migration["migrate_sql"]))
                        conn.commit()
                        print(f"âœ… Migration: {migration['name']} completed")
                except Exception as e:
                    print(f"âš ï¸ Migration {migration['name']} skipped: {e}")
    except Exception as e:
        print(f"âš ï¸ Auto migration warning: {e}")

# å•Ÿå‹•æ™‚åŸ·è¡Œé·ç§»
run_auto_migrations()
# ============================================================

# åŒæ­¥ Session
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# ç‚ºäº†å‘å¾Œç›¸å®¹ï¼Œä¿ç•™ SessionLocal åˆ¥å
SessionLocal = SyncSessionLocal

# ORM Base
Base = declarative_base()


async def get_async_session():
    """FastAPI ä¾è³´æ³¨å…¥ç”¨"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """CLI ç”¨åŒæ­¥ Session"""
    session = SyncSessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


async def init_db():
    """åˆå§‹åŒ–è³‡æ–™åº«ï¼ˆå»ºç«‹æ‰€æœ‰è¡¨æ ¼ï¼‰"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db_sync():
    """åŒæ­¥åˆå§‹åŒ–è³‡æ–™åº«"""
    Base.metadata.create_all(bind=sync_engine)


# FastAPI ä¾è³´æ³¨å…¥ç”¨ï¼ˆåŒæ­¥ç‰ˆæœ¬ï¼Œç”¨æ–¼æŸäº› APIï¼‰
def get_db():
    """FastAPI ä¾è³´æ³¨å…¥ç”¨ï¼ˆåŒæ­¥ Sessionï¼‰"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# ðŸ†• æ–°å¢žåˆ¥å - ä¿®å¾© stock.py ImportError
# ============================================================
get_sync_db = get_db