"""
NeuroNex — Insights Router
Auto-generates insights from current graph state if none exist yet,
then serves them with full explanation + source trace.
"""
from __future__ import annotations
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_sql import get_db
from app.models_sql import Insight, ResolutionCandidate, ExtractedEntity
from app.schemas import InsightOut
from app.pipeline.analytics import get_top_entities
from app.pipeline.communities import get_communities
from app.pipeline.explainability import generate_all_insights
from app.pipeline.patterns import detect_all_patterns

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/insights", tags=["insights"])


async def _materialise_insights(db: AsyncSession, force: bool = False):
    """Generate and store insights if the table is empty, or add new ones on force."""
    if not force:
        count_result = await db.execute(select(Insight))
        existing = count_result.scalars().first()
        if existing:
            return  # already materialised

    top_entities = await get_top_entities(10)
    from app.pipeline.analytics import get_key_influencers
    key_influencers = await get_key_influencers(limit=10)
    communities = await get_communities()

    # Detect suspicious / anomaly patterns
    patterns = await detect_all_patterns(db)

    # Fetch pending resolution candidates with entity names
    cand_result = await db.execute(
        select(ResolutionCandidate).where(ResolutionCandidate.decision == "pending").limit(10)
    )
    candidates_db = cand_result.scalars().all()

    candidates = []
    for cand in candidates_db:
        ent_a = await db.get(ExtractedEntity, cand.entity_a_id)
        ent_b = await db.get(ExtractedEntity, cand.entity_b_id)
        candidates.append({
            "similarity_score": cand.similarity_score,
            "match_reason": cand.match_reason,
            "entity_type": cand.entity_type,
            "entity_a_name": ent_a.normalized_text if ent_a else "Entity A",
            "entity_b_name": ent_b.normalized_text if ent_b else "Entity B",
        })

    insight_dicts = generate_all_insights(
        top_entities=top_entities,
        communities=communities,
        pending_candidates=candidates,
        patterns=patterns,
        key_influencers=key_influencers,
    )

    import hashlib

    # Fetch existing insights to compare fingerprints
    existing_all = (await db.execute(select(Insight))).scalars().all()
    existing_fingerprints = set()
    for e in existing_all:
        e_refs = sorted([str(x) for x in (e.entity_refs or [])])
        s_refs = sorted([str(x) for x in (e.source_refs or [])])
        fp = hashlib.sha256(f"{e.insight_type}::{e.title}::{e_refs}::{s_refs}".encode()).hexdigest()
        existing_fingerprints.add(fp)

    added_count = 0
    for d in insight_dicts:
        e_refs = sorted([str(x) for x in (d.get("entity_refs") or [])])
        s_refs = sorted([str(x) for x in (d.get("source_refs") or [])])
        fp = hashlib.sha256(f"{d.get('insight_type')}::{d.get('title')}::{e_refs}::{s_refs}".encode()).hexdigest()
        if fp in existing_fingerprints:
            continue
        existing_fingerprints.add(fp)
        insight = Insight(**d)
        db.add(insight)
        added_count += 1
    await db.commit()
    logger.info("Materialised %d new insights (total existing: %d)", added_count, len(existing_all) + added_count)


@router.get("", response_model=list[InsightOut])
async def list_insights(
    insight_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List insights; auto-generates from current graph state if none exist."""
    await _materialise_insights(db)

    q = select(Insight).order_by(Insight.created_at.desc())
    if insight_type:
        q = q.where(Insight.insight_type == insight_type)
    if status:
        q = q.where(Insight.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{insight_id}", response_model=InsightOut)
async def get_insight(insight_id: int, db: AsyncSession = Depends(get_db)):
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(404, "Insight not found")
    return insight


@router.post("/regenerate")
async def regenerate_insights(db: AsyncSession = Depends(get_db)):
    """Regenerate insights from current graph state using deterministic fingerprint deduplication."""
    await _materialise_insights(db, force=True)
    count = (await db.execute(select(Insight))).scalars().all()
    return {"regenerated": len(count)}
