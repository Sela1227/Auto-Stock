"""
資料庫連線與 Session 管理
支援 SQLite (開發) 和 PostgreSQL (生產)

🔧 修復版本 - 2026-01-16
新增 get_sync_db 別名

🚀 效能優化 - 2026-01-16
新增 stock_prices 歷史資料表
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings


def get_async_url(url: str) -> str:
    """將一般的資料庫 URL 轉換為 async 格式"""
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://")
    elif url.startswith("postgres://"):
        # Railway 使用 postgres:// 但 SQLAlchemy 需要 postgresql://
        return url.replace("postgres://", "postgresql+asyncpg://")
    return url


def get_sync_url(url: str) -> str:
    """確保是同步格式的 URL"""
    url = url.replace("+aiosqlite", "").replace("+asyncpg", "")
    # 修正 Railway 的 postgres:// 格式
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://")
    return url


def is_postgres(url: str) -> bool:
    """檢查是否為 PostgreSQL"""
    return "postgresql" in url or "postgres" in url


# 取得資料庫 URL
database_url = settings.DATABASE_URL

# 非同步引擎 (FastAPI 用)
async_database_url = get_async_url(database_url)

# PostgreSQL 需要特別的連線池設定
if is_postgres(database_url):
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
        poolclass=NullPool,  # Railway 建議使用 NullPool
    )
else:
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.DEBUG,
    )

# 非同步 Session
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 同步引擎 (CLI 用)
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
# 🆕 自動資料庫遷移
# ============================================================
def run_auto_migrations():
    """啟動時自動執行資料庫遷移"""
    migrations = [
        # 2026-01-14: MA20 排序功能
        {
            "name": "add_ma20_to_price_cache",
            "check_sql": "SELECT column_name FROM information_schema.columns WHERE table_name='stock_price_cache' AND column_name='ma20'",
            "migrate_sql": "ALTER TABLE stock_price_cache ADD COLUMN ma20 NUMERIC(12, 4)",
        },
        # 2026-01-14: 訂閱精選功能 - 訂閱源表
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
        # 2026-01-14: 訂閱精選功能 - 自動精選表
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
        # 2026-01-14: 訂閱精選功能 - 用戶訂閱表
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
        # 2026-01-15: P1 目標價功能
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
        # 🚀 2026-01-16: 股票歷史資料快取表（效能優化）
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

        # 2026-01-17: 券商功能
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
                        print(f"✅ Migration: {migration['name']} completed")
                except Exception as e:
                    print(f"⚠️ Migration {migration['name']} skipped: {e}")
    except Exception as e:
        print(f"⚠️ Auto migration warning: {e}")

# 啟動時執行遷移
run_auto_migrations()
# ============================================================

# 同步 Session
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# 為了向後相容，保留 SessionLocal 別名
SessionLocal = SyncSessionLocal

# ORM Base
Base = declarative_base()


async def get_async_session():
    """FastAPI 依賴注入用"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """CLI 用同步 Session"""
    session = SyncSessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


async def init_db():
    """初始化資料庫（建立所有表格）"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db_sync():
    """同步初始化資料庫"""
    Base.metadata.create_all(bind=sync_engine)


# FastAPI 依賴注入用（同步版本，用於某些 API）
def get_db():
    """FastAPI 依賴注入用（同步 Session）"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# 🆕 新增別名 - 修復 stock.py ImportError
# ============================================================
get_sync_db = get_db
