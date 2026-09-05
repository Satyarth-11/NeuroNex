"""
NeuroNex — FastAPI Application Entry Point
Registers all routers, configures CORS, initialises databases on startup.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db_sql import init_db
from app.db_graph import close_driver

# Import ingestion adapters to register them (via @register_adapter decorators)
import app.ingestion  # noqa: F401

# Routers
from app.routers import (
    documents, entities, resolution, graph, analytics, insights, review, validation, admin
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup + shutdown lifecycle."""
    logger.info("NeuroNex backend starting — %s v%s", settings.app_name, settings.app_version)
    await init_db()
    logger.info("SQLite tables initialised")

    # Idempotent migration: normalize legacy source_types in documents table
    try:
        from app.db_sql import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text(
                "UPDATE documents SET source_type = 'financial' WHERE source_type IN ('financial_transaction', 'financial_transactions', 'finance');"
            ))
            await session.execute(text(
                "UPDATE documents SET source_type = 'cdr' WHERE source_type IN ('call_detail_record', 'call_detail_records');"
            ))
            await session.execute(text(
                "UPDATE documents SET source_type = 'surveillance' WHERE source_type IN ('surveillance_report', 'surveillance_reports');"
            ))
            await session.commit()
    except Exception as exc:
        logger.warning("Document source_type startup normalization skipped: %s", exc)

    # Idempotent migration: convert pre-existing financial ASSOCIATED_WITH edges to TRANSFERRED_TO
    try:
        from app.db_graph import run_query
        migrate_cypher = """
        MATCH (a)-[r:ASSOCIATED_WITH]->(b)
        WHERE r.source_types IS NOT NULL AND "financial" IN r.source_types
        CREATE (a)-[r2:TRANSFERRED_TO]->(b)
        SET r2 = properties(r)
        DELETE r
        RETURN count(r2) AS migrated_count
        """
        res = await run_query(migrate_cypher)
        if res and res[0].get("migrated_count", 0) > 0:
            logger.info("Migrated %d legacy financial ASSOCIATED_WITH edges to TRANSFERRED_TO", res[0]["migrated_count"])
    except Exception as exc:
        logger.warning("Financial edge startup migration skipped: %s", exc)

    yield
    await close_driver()
    logger.info("Neo4j driver closed — shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "NeuroNex — AI-Powered Criminal Network Analysis System. "
        "DECISION SUPPORT TOOL ONLY. All data is SYNTHETIC. "
        "No real investigative records are used anywhere in this prototype."
    ),
    lifespan=lifespan,
)

# CORS — allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(documents.router)
app.include_router(entities.router)
app.include_router(resolution.router)
app.include_router(graph.router)
app.include_router(analytics.router)
app.include_router(insights.router)
app.include_router(review.router)
app.include_router(validation.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {
        "system": settings.app_name,
        "version": settings.app_version,
        "data_notice": "ALL DATA IS SYNTHETIC — generated for SIH prototype demonstration only.",
        "docs": "/docs",
    }


@app.get("/health")
@app.get("/api/health")
async def health():
    from sqlalchemy import select, func
    from app.models_sql import Document, ExtractedEntity, Insight, ResolutionCandidate

    neo4j_ok = False
    graph_nodes = 0
    graph_edges = 0
    try:
        from app.db_graph import run_query
        res_n = await run_query("MATCH (n) RETURN count(n) AS cnt")
        if res_n:
            graph_nodes = int(res_n[0].get("cnt", 0))
        res_e = await run_query("MATCH ()-[r]->() RETURN count(r) AS cnt")
        if res_e:
            graph_edges = int(res_e[0].get("cnt", 0))
        neo4j_ok = True
    except Exception:
        pass

    db_ok = False
    doc_count = 0
    entity_count = 0
    insight_count = 0
    candidate_count = 0
    try:
        from app.db_sql import AsyncSessionLocal
        async with AsyncSessionLocal() as s:
            d_res = await s.execute(select(func.count(Document.id)))
            doc_count = d_res.scalar() or 0

            e_res = await s.execute(select(func.count(ExtractedEntity.id)))
            entity_count = e_res.scalar() or 0

            i_res = await s.execute(select(func.count(Insight.id)))
            insight_count = i_res.scalar() or 0

            c_res = await s.execute(select(func.count(ResolutionCandidate.id)))
            candidate_count = c_res.scalar() or 0
        db_ok = True
    except Exception:
        pass

    # Check NLP availability
    nlp_ok = False
    try:
        from app.pipeline.ner import _get_nlp
        nlp_ok = (_get_nlp() is not None)
    except Exception:
        pass

    overall_status = "Healthy" if (neo4j_ok and db_ok) else "Degraded" if (neo4j_ok or db_ok) else "Unavailable"

    return {
        "status": overall_status.lower(),
        "overall_status": overall_status,
        "components": {
            "backend": "Healthy",
            "sqlite": "Healthy" if db_ok else "Unavailable",
            "neo4j": "Healthy" if neo4j_ok else "Unavailable",
            "nlp": "Healthy" if nlp_ok else "Degraded",
            "entity_resolution": "Healthy" if db_ok else "Unavailable",
            "graph_analytics": "Healthy" if neo4j_ok else "Unavailable",
        },
        "counts": {
            "document_count": doc_count,
            "entity_count": entity_count,
            "graph_node_count": graph_nodes,
            "graph_edge_count": graph_edges,
            "insight_count": insight_count,
            "resolution_candidate_count": candidate_count,
        },
        "backend": "ok",
        "neo4j": "ok" if neo4j_ok else "unreachable",
        "database": "ok" if db_ok else "unreachable",
    }
