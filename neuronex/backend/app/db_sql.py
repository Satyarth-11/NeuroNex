"""
NeuroNex — SQLAlchemy async engine + session factory.
Database: SQLite for prototype (swappable to PostgreSQL by changing DATABASE_URL).
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables on startup and apply light column migrations."""
    from sqlalchemy import text
    from app import models_sql  # noqa: F401 — registers ORM models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(text("ALTER TABLE documents ADD COLUMN error_message TEXT"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE validation_runs ADD COLUMN extra_metrics JSON"))
        except Exception:
            pass
        for col, col_type in [("sample_size", "INTEGER"), ("threshold_used", "REAL"), ("comparison_basis", "TEXT")]:
            try:
                await conn.execute(text(f"ALTER TABLE insights ADD COLUMN {col} {col_type}"))
            except Exception:
                pass
