"""
NeuroNex — Entities Router
List extracted entities, trace an entity back to its source documents,
and provide summary data for exploratory analysis.
"""
from __future__ import annotations
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_sql import get_db
from app.models_sql import ExtractedEntity, Document, Case, ResolutionCandidate
from app.schemas import EntityOut, EntityTraceOut, EntitySummaryOut
from app.db_graph import run_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/entities", tags=["entities"])


@router.get("/summary", response_model=EntitySummaryOut)
async def get_entities_summary(db: AsyncSession = Depends(get_db)):
    """Summary counts for Entity Explorer header cards."""
    res = await db.execute(select(ExtractedEntity.entity_type, ExtractedEntity.document_id))
    rows = res.all()

    by_type: dict[str, int] = {
        "PERSON": 0,
        "PHONE": 0,
        "LOCATION": 0,
        "VEHICLE": 0,
        "ORGANISATION": 0,
        "ACCOUNT": 0,
        "CASE_REF": 0,
    }
    doc_ids = set()
    for etype, doc_id in rows:
        if etype in by_type:
            by_type[etype] += 1
        elif etype:
            by_type[etype] = by_type.get(etype, 0) + 1
        if doc_id:
            doc_ids.add(doc_id)

    cases_count = 0
    if doc_ids:
        c_res = await db.execute(
            select(Document.case_id).where(Document.id.in_(doc_ids), Document.case_id.isnot(None)).distinct()
        )
        cases_count = len(c_res.scalars().all())

    return EntitySummaryOut(
        total=len(rows),
        by_type=by_type,
        by_case=cases_count,
        cases_count=cases_count,
    )


@router.get("", response_model=list[EntityOut])
async def list_entities(
    entity_type: Optional[str] = None,
    source_type: Optional[str] = None,
    case_id: Optional[int] = None,
    search: Optional[str] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(ExtractedEntity)
    if source_type or case_id:
        q = q.join(Document, ExtractedEntity.document_id == Document.id)
        if source_type:
            q = q.where(Document.source_type == source_type)
        if case_id:
            q = q.where(Document.case_id == case_id)

    if entity_type:
        q = q.where(ExtractedEntity.entity_type == entity_type)
    if search:
        q = q.where(
            or_(
                ExtractedEntity.text.ilike(f"%{search}%"),
                ExtractedEntity.normalized_text.ilike(f"%{search}%"),
            )
        )

    q = q.order_by(ExtractedEntity.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(q)
    entities = result.scalars().all()

    if not entities:
        return []

    # Efficient batch enrichment
    cids = {e.canonical_entity_id for e in entities if e.canonical_entity_id}
    entity_ids = [e.id for e in entities]

    # 1. Canonical grouping metrics
    canonical_metrics: dict[str, dict] = {}
    if cids:
        mentions_q = (
            select(
                ExtractedEntity.canonical_entity_id,
                ExtractedEntity.document_id,
                Document.source_type,
                Document.case_id,
            )
            .join(Document, ExtractedEntity.document_id == Document.id, isouter=True)
            .where(ExtractedEntity.canonical_entity_id.in_(cids))
        )
        m_res = await db.execute(mentions_q)
        m_rows = m_res.all()
        for cid, doc_id, stype, cid_case in m_rows:
            if not cid:
                continue
            if cid not in canonical_metrics:
                canonical_metrics[cid] = {
                    "mention_count": 0,
                    "doc_ids": set(),
                    "source_types": set(),
                    "case_ids": set(),
                }
            canonical_metrics[cid]["mention_count"] += 1
            if doc_id:
                canonical_metrics[cid]["doc_ids"].add(doc_id)
            if stype:
                canonical_metrics[cid]["source_types"].add(stype)
            if cid_case:
                canonical_metrics[cid]["case_ids"].add(cid_case)

    # 2. Resolution status lookup
    res_status_map: dict[int, str] = {}
    if entity_ids:
        cand_q = select(ResolutionCandidate).where(
            or_(
                ResolutionCandidate.entity_a_id.in_(entity_ids),
                ResolutionCandidate.entity_b_id.in_(entity_ids),
            )
        )
        cand_res = await db.execute(cand_q)
        for cand in cand_res.scalars().all():
            res_status_map[cand.entity_a_id] = cand.decision
            res_status_map[cand.entity_b_id] = cand.decision

    # 3. Build enriched EntityOut models
    output = []
    for ent in entities:
        cid_stats = canonical_metrics.get(ent.canonical_entity_id, {}) if ent.canonical_entity_id else {}
        mention_count = cid_stats.get("mention_count", 1)
        doc_count = len(cid_stats.get("doc_ids", [])) or 1
        stype_count = len(cid_stats.get("source_types", [])) or 1
        case_count = len(cid_stats.get("case_ids", []))
        resolution_status = res_status_map.get(ent.id, "unresolved")

        output.append(
            EntityOut(
                id=ent.id,
                document_id=ent.document_id,
                text=ent.text,
                entity_type=ent.entity_type,
                normalized_text=ent.normalized_text,
                context_snippet=ent.context_snippet,
                canonical_entity_id=ent.canonical_entity_id,
                created_at=ent.created_at,
                mention_count=mention_count,
                source_document_count=doc_count,
                source_type_count=stype_count,
                related_case_count=case_count,
                resolution_status=resolution_status,
            )
        )
    return output


@router.get("/search/graph")
async def search_graph_entities(q: str = Query(..., min_length=1)):
    """Search entities in Neo4j graph by name (case-insensitive prefix search)."""
    rows = await run_query(
        "MATCH (n) WHERE toLower(n.name) CONTAINS toLower($q) "
        "RETURN n.id AS id, n.name AS name, n.entity_type AS entity_type, "
        "n.source_types AS source_types LIMIT 50",
        {"q": q},
    )
    return rows


@router.get("/{canonical_id}/trace", response_model=EntityTraceOut)
async def trace_entity(canonical_id: str, db: AsyncSession = Depends(get_db)):
    """Full trace: all SQL mentions + source documents + related cases + Neo4j node data."""

    # SQL mentions
    result = await db.execute(
        select(ExtractedEntity).where(
            ExtractedEntity.canonical_entity_id == canonical_id
        )
    )
    mentions_db = result.scalars().all()

    if not mentions_db:
        raise HTTPException(404, f"No entity found with canonical_id={canonical_id}")

    # Source documents
    doc_ids = list({m.document_id for m in mentions_db})
    doc_result = await db.execute(
        select(Document).where(Document.id.in_(doc_ids))
    )
    docs = doc_result.scalars().all()

    source_types = list({d.source_type for d in docs})

    # Related cases reachable via documents
    case_ids = list({d.case_id for d in docs if d.case_id is not None})
    related_cases = []
    if case_ids:
        cases_res = await db.execute(select(Case).where(Case.id.in_(case_ids)))
        related_cases = [
            {"id": c.id, "case_code": c.case_code, "title": c.title}
            for c in cases_res.scalars().all()
        ]

    # Neo4j node data & co-occurring graph neighbors
    neo_rows = await run_query(
        "MATCH (n {id: $cid}) RETURN n", {"cid": canonical_id}
    )
    neo_node = dict(neo_rows[0]["n"]) if neo_rows else None

    related_entities = []
    try:
        neo_rel_rows = await run_query(
            "MATCH (n {id: $cid})-[r]-(m) "
            "RETURN DISTINCT m.id AS id, m.name AS name, m.entity_type AS entity_type, "
            "type(r) AS rel_type LIMIT 20",
            {"cid": canonical_id},
        )
        related_entities = [
            {
                "id": row.get("id"),
                "name": row.get("name") or row.get("id"),
                "entity_type": row.get("entity_type") or "Entity",
                "rel_type": row.get("rel_type") or "CONNECTED_TO",
            }
            for row in neo_rel_rows
        ]
    except Exception as e:
        logger.warning("Could not fetch graph neighbors for trace %s: %s", canonical_id, e)

    sample = mentions_db[0]

    return EntityTraceOut(
        canonical_entity_id=canonical_id,
        entity_type=sample.entity_type,
        name=sample.normalized_text,
        mentions=[
            {
                "id": m.id,
                "text": m.text,
                "context_snippet": m.context_snippet,
                "document_id": m.document_id,
            }
            for m in mentions_db
        ],
        source_documents=[
            {
                "id": d.id,
                "filename": d.filename,
                "source_type": d.source_type,
                "case_id": d.case_id,
            }
            for d in docs
        ],
        source_types=source_types,
        graph_node=neo_node,
        related_cases=related_cases,
        related_entities=related_entities,
    )
