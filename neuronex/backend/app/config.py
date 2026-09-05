"""
NeuroNex Configuration
Reads from environment variables (with .env file support).
All thresholds and connection strings are centralised here so they can be
overridden without touching source code.
"""
import os
try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseModel as BaseSettings
    except ImportError:
        class BaseSettings:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "NeuroNex — Criminal Network Analysis System"
    app_version: str = "1.0.0"
    debug: bool = False

    # SQLite (swappable to PostgreSQL via DATABASE_URL)
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./neuronex.db")

    # Neo4j (password required from environment)
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")

    # NLP — isolated so a transformer can replace spaCy later
    spacy_model: str = "en_core_web_sm"

    # Entity Resolution thresholds
    resolution_auto_merge_threshold: float = 0.85
    resolution_review_threshold: float = 0.72

    # CORS
    cors_origins: list[str] = ["http://localhost:3001", "http://localhost:3000"]

    # Synthetic data seed
    synthetic_seed: int = 42

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
