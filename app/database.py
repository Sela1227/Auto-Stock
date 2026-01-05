"""
資料庫連線與 Session 管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


def get_async_url(url: str) -> str:
    """將一般的 sqlite URL 轉換為 async 格式"""
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url


def get_sync_url(url: str) -> str:
    """確保是同步格式的 URL"""
    url = url.replace("+aiosqlite", "").replace("+asyncpg", "")
    return url


# 非同步引擎 (FastAPI 用)
async_database_url = get_async_url(settings.DATABASE_URL)
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
sync_database_url = get_sync_url(settings.DATABASE_URL)
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
