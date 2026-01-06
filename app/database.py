"""
資料庫連線與 Session 管理
支援 SQLite (開發) 和 PostgreSQL (生產)
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
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

# 同步 Session
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

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
