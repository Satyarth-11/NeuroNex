"""
NeuroNex — Analytics Router
Centrality, top entities, communities, pattern detection, timeline, and genuine ML.
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_sql import get_db
from app.pipeline.analytics import get_centrality, get_top_entities
from app.pipeline.communities import get_communities
from app.pipeline.patterns import detect_all_patterns
from app.pipeline.temporal import get_timeline_for_case
from app.pipeline.ml_model import train_and_evaluate_logistic_regression

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/centrality")
async def centrality():
    """Degree + betweenness centrality for all nodes, plus network stats."""
    return await get_centrality()


@router.get("/top-entities")
async def top_entities(n: int = Query(10, ge=1, le=50)):
    """Top-N entities by betweenness centrality."""
    return await get_top_entities(n)


@router.get("/communities")
async def communities():
    """Louvain community detection results."""
    return await get_communities()


@router.get("/communities/{community_id}")
async def community_detail(community_id: int):
    """Detailed composition and breakdown of a specific community cluster."""
    from app.pipeline.communities import get_community_detail
    detail = await get_community_detail(community_id)
    if not detail:
        raise HTTPException(404, f"Community {community_id} not found")
    return detail


@router.get("/patterns")
async def patterns(db: AsyncSession = Depends(get_db)):
    """Run all 5 rule-based anomaly & pattern detectors on-demand."""
    return await detect_all_patterns(db)


@router.get("/key-influencers")
async def key_influencers(limit: int = Query(10, ge=1, le=50)):
    """Top influential PERSON entities with PageRank, betweenness, and explainability text."""
    from app.pipeline.analytics import get_key_influencers
    return await get_key_influencers(limit=limit)


@router.get("/timeline")
async def timeline(
    case_code: str = Query(..., description="Target case code (e.g. CASE-2024-001)"),
    window_hours: int = Query(48, ge=1, le=720, description="Correlation window in hours"),
    entity: Optional[str] = Query(None, description="Optional entity name to filter timeline events"),
    entity_id: Optional[str] = Query(None, description="Optional entity ID to filter timeline events"),
):
    """
    Chronological investigative timeline and cross-source temporal correlation detection.
    """
    ent_filt = entity_id or entity
    return get_timeline_for_case(case_code=case_code, window_hours=window_hours, entity_filter=ent_filt)


@router.get("/ml-model")
async def ml_model_evaluation():
    """
    Evaluates explainable Logistic Regression classifier for Investigative Priority
    trained on ~80% development cases and evaluated strictly on ~20% held-out cases.
    """
    return train_and_evaluate_logistic_regression()


@router.post("/ml-model/train")
async def train_ml_model():
    """
    Triggers on-demand training and held-out evaluation of the Logistic Regression model.
    """
    return train_and_evaluate_logistic_regression()
