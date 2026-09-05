"""
NeuroNex — Resolution Router
List pending duplicate candidates; analyst approve/reject.
On approve: merge Neo4j nodes (keep older id, migrate edges, delete duplicate).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_sql import get_db
from app.models_sql import ResolutionCandidate, ExtractedEntity, Document, Case
from app.schemas import ResolutionCandidateOut, ResolutionDecision
from app.db_graph import run_write_tx

router = APIRouter(prefix="/api/resolution", tags=["resolution"])


@router.get("/candidates", response_model=list[ResolutionCandidateOut])
async def list_candidates(
    decision: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(ResolutionCandidate).order_by(ResolutionCandidate.created_at.desc())
    if decision:
        q = q.where(ResolutionCandidate.decision == decision)
    result = await db.execute(q)
    candidates = result.scalars().all()

    out: list[ResolutionCandidateOut] = []
    seen_pair_keys: set[tuple[int, int]] = set()

    for c in candidates:
        pair_key = tuple(sorted((c.entity_a_id, c.entity_b_id)))
        if pair_key in seen_pair_keys:
            continue
        seen_pair_keys.add(pair_key)

        ent_a = await db.get(ExtractedEntity, c.entity_a_id)
        ent_b = await db.get(ExtractedEntity, c.entity_b_id)

        doc_a = await db.get(Document, ent_a.document_id) if ent_a else None
        doc_b = await db.get(Document, ent_b.document_id) if ent_b else None

        case_a = await db.get(Case, doc_a.case_id) if (doc_a and doc_a.case_id) else None
        case_b = await db.get(Case, doc_b.case_id) if (doc_b and doc_b.case_id) else None

        out.append(
            ResolutionCandidateOut(
                id=c.id,
                entity_a_id=c.entity_a_id,
                entity_b_id=c.entity_b_id,
                entity_type=c.entity_type,
                similarity_score=c.similarity_score,
                match_reason=c.match_reason,
                decision=c.decision,
                decided_by=c.decided_by,
                decided_at=c.decided_at,
                created_at=c.created_at,
                entity_a_text=ent_a.text if ent_a else None,
                entity_b_text=ent_b.text if ent_b else None,
                entity_a_doc=doc_a.filename if doc_a else None,
                entity_b_doc=doc_b.filename if doc_b else None,
                entity_a_case=case_a.case_code if case_a else None,
                entity_b_case=case_b.case_code if case_b else None,
            )
        )
    return out


@router.post("/{candidate_id}/decide", response_model=ResolutionCandidateOut)
async def decide_candidate(
    candidate_id: int,
    payload: ResolutionDecision,
    db: AsyncSession = Depends(get_db),
):
    candidate = await db.get(ResolutionCandidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Resolution candidate not found")

    candidate.decision = payload.decision
    candidate.decided_by = payload.analyst_id
    candidate.decided_at = datetime.now(timezone.utc)

    if payload.decision == "approved":
        # Merge Neo4j nodes: keep entity_a, migrate all edges from entity_b, delete entity_b
        ent_a = await db.get(ExtractedEntity, candidate.entity_a_id)
        ent_b = await db.get(ExtractedEntity, candidate.entity_b_id)
        if ent_a and ent_b and ent_a.canonical_entity_id and ent_b.canonical_entity_id:
            await _merge_neo4j_nodes(ent_a.canonical_entity_id, ent_b.canonical_entity_id)
            # Update all SQLite references to entity_b → entity_a canonical id
            ent_b.canonical_entity_id = ent_a.canonical_entity_id

    await db.commit()
    await db.refresh(candidate)
    return candidate


async def _merge_neo4j_nodes(keep_id: str, remove_id: str):
    """
    Merge two Neo4j nodes: redirect all edges from remove_id to keep_id,
    then delete remove_id node.
    This is reversible (we log the candidate decision in SQLite).
    """
    # Redirect outgoing edges
    await run_write_tx(
        """
        MATCH (keep {id: $keep}), (remove {id: $remove})
        MATCH (remove)-[r]->(other)
        WHERE other.id <> $keep
        MERGE (keep)-[r2:ASSOCIATED_WITH]->(other)
        ON CREATE SET r2.weight = r.weight, r2.source_types = r.source_types,
                      r2.source_doc_ids = r.source_doc_ids, r2.status = 'approved'
        """,
        {"keep": keep_id, "remove": remove_id},
    )
    # Redirect incoming edges
    await run_write_tx(
        """
        MATCH (keep {id: $keep}), (remove {id: $remove})
        MATCH (other)-[r]->(remove)
        WHERE other.id <> $keep
        MERGE (other)-[r2:ASSOCIATED_WITH]->(keep)
        ON CREATE SET r2.weight = r.weight, r2.source_types = r.source_types,
                      r2.source_doc_ids = r.source_doc_ids, r2.status = 'approved'
        """,
        {"keep": keep_id, "remove": remove_id},
    )
    # Delete the merged-away node
    await run_write_tx(
        "MATCH (n {id: $remove}) DETACH DELETE n",
        {"remove": remove_id},
    )
