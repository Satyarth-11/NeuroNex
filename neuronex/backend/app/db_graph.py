"""
NeuroNex — Neo4j driver singleton.
Uses the official neo4j Python driver (bolt protocol).
All graph write/read operations go through this module.
"""
from typing import Any
try:
    from neo4j import AsyncGraphDatabase, AsyncDriver
except ImportError:
    AsyncGraphDatabase = None
    AsyncDriver = None

from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
_driver: Any = None


async def get_driver() -> Any:
    """Return the singleton Neo4j async driver, creating it if needed."""
    global _driver
    if _driver is None:
        if AsyncGraphDatabase is None:
            raise RuntimeError("Neo4j driver is not installed in this environment.")
        settings = get_settings()
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            connection_timeout=2.0,
        )
        logger.info("Neo4j driver initialised — %s", settings.neo4j_uri)
    return _driver


async def close_driver():
    """Cleanly close the driver on application shutdown."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed.")


async def run_query(cypher: str, params: dict | None = None) -> list[dict]:
    """
    Execute a read Cypher query and return rows as list of dicts.
    For write queries use run_write().
    """
    driver = await get_driver()
    async with driver.session() as session:
        result = await session.run(cypher, params or {})
        return [dict(record) async for record in result]


async def run_write(cypher: str, params: dict | None = None) -> list[dict]:
    """Execute a write Cypher query and return any records produced."""
    driver = await get_driver()
    async with driver.session() as session:
        result = await session.run(cypher, params or {})
        return [dict(record) async for record in result]


async def run_write_tx(cypher: str, params: dict | None = None):
    """Execute a write Cypher query and consume its result."""
    driver = await get_driver()
    async with driver.session() as session:
        result = await session.run(cypher, params or {})
        await result.consume()
