"""
NeuroNex — Documents Router
Handles upload, listing, processing of documents across all 7 source types.
"""
from __future__ import annotations
import io
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_sql import get_db
from app.models_sql import Case, Document, ExtractedEntity, ResolutionCandidate
from app.schemas import (
    CaseCreate, CaseOut, CaseDetailOut, DocumentOut, DocumentDetailOut,
    ProcessResult, SourceSummaryItem, TopConnectedEntity
)
from app.ingestion.base import get_adapter, normalize_source_type, SOURCE_TYPES
from app.pipeline.cleaning import clean_record
from app.pipeline.ner import extract_entities
from app.pipeline.resolution import resolve_entities
from app.pipeline.kg_builder import build_graph, canonical_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
@router.post("/cases", response_model=CaseOut, status_code=201)
async def create_case(payload: CaseCreate, db: AsyncSession = Depends(get_db)):
    case = Case(**payload.model_dump())
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@router.get("/cases/all", response_model=list[CaseOut])
async def list_cases(db: AsyncSession = Depends(get_db)):
    cases_res = await db.execute(select(Case).order_by(Case.created_at.desc()))
    cases = cases_res.scalars().all()
    if not cases:
        return []

    # Document counts per case
    doc_cnt_res = await db.execute(
        select(Document.case_id, func.count(Document.id)).group_by(Document.case_id)
    )
    doc_counts = dict(doc_cnt_res.all())

    # Entity counts per case
    ent_cnt_res = await db.execute(
        select(Document.case_id, func.count(ExtractedEntity.id))
        .join(ExtractedEntity, ExtractedEntity.document_id == Document.id)
        .group_by(Document.case_id)
    )
    ent_counts = dict(ent_cnt_res.all())

    # Relationship counts from Neo4j per case
    from app.db_graph import run_query
    case_codes = [c.case_code for c in cases]
    rel_counts = {}
    try:
        cypher = """
        MATCH ()-[r]->()
        WHERE r.related_case IN $codes
        RETURN r.related_case AS code, count(r) AS cnt
        """
        res = await run_query(cypher, {"codes": case_codes})
        for row in res:
            rel_counts[row.get("code")] = row.get("cnt", 0)
    except Exception as e:
        logger.warning("Could not fetch case edge counts: %s", e)

    out = []
    for c in cases:
        out.append(CaseOut(
            id=c.id,
            case_code=c.case_code,
            title=c.title,
            description=c.description or "",
            created_at=c.created_at,
            document_count=doc_counts.get(c.id, 0),
            entity_count=ent_counts.get(c.id, 0),
            relationship_count=rel_counts.get(c.case_code, 0),
        ))
    return out


@router.get("/cases/{case_id}", response_model=CaseDetailOut)
async def get_case_detail(case_id: int, db: AsyncSession = Depends(get_db)):
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    docs_res = await db.execute(
        select(Document).where(Document.case_id == case_id).order_by(Document.uploaded_at.desc())
    )
    docs = docs_res.scalars().all()
    doc_ids = [d.id for d in docs]

    ent_cnt = 0
    canonical_cids = set()
    if doc_ids:
        ent_res = await db.execute(
            select(ExtractedEntity.canonical_entity_id).where(
                ExtractedEntity.document_id.in_(doc_ids)
            )
        )
        for (cid,) in ent_res.all():
            ent_cnt += 1
            if cid:
                canonical_cids.add(str(cid))

    from app.db_graph import run_query
    rel_cnt = 0
    try:
        res = await run_query(
            "MATCH ()-[r]->() WHERE r.related_case = $code RETURN count(r) AS cnt",
            {"code": case.case_code}
        )
        if res:
            rel_cnt = res[0].get("cnt", 0)
    except Exception as e:
        logger.warning("Could not fetch relationship count for case %d: %s", case_id, e)

    # Community count touching this case (real set intersection check, no fabricated fallback)
    comm_count = 0
    try:
        from app.pipeline.communities import get_communities
        comms = await get_communities()
        comm_list = comms if isinstance(comms, list) else comms.get("communities", [])
        for c_comm in comm_list:
            members = c_comm.get("members", [])
            m_ids = {m.get("node_id", "") if isinstance(m, dict) else str(m) for m in members}
            if canonical_cids and (m_ids & canonical_cids):
                comm_count += 1
    except Exception as e:
        logger.warning("Could not calculate community count for case %d: %s", case_id, e)

    # Insights touching this case (via source_refs containing any document_id of this case)
    from app.models_sql import Insight
    ins_res = await db.execute(select(Insight))
    all_insights = ins_res.scalars().all()
    doc_id_strs = {str(d) for d in doc_ids}
    ins_cnt = 0
    for ins in all_insights:
        if ins.source_refs:
            clean_refs = {str(r).replace("doc_", "").strip() for r in ins.source_refs}
            if clean_refs & doc_id_strs:
                ins_cnt += 1

    # Top connected entities within this case subgraph (Phase 7)
    top_connected = []
    try:
        top_res = await run_query(
            "MATCH (n)-[r]-(m) WHERE r.related_case = $code "
            "RETURN n.id AS id, n.name AS name, n.entity_type AS entity_type, count(r) AS degree "
            "ORDER BY degree DESC LIMIT 5",
            {"code": case.case_code}
        )
        for row in top_res:
            top_connected.append(TopConnectedEntity(
                id=str(row.get("id")),
                name=str(row.get("name") or row.get("id")),
                entity_type=str(row.get("entity_type") or "UNKNOWN"),
                degree=int(row.get("degree", 0)),
            ))
    except Exception as e:
        logger.warning("Could not fetch top connected entities for case %s: %s", case.case_code, e)

    return CaseDetailOut(
        id=case.id,
        case_code=case.case_code,
        title=case.title,
        description=case.description or "",
        created_at=case.created_at,
        document_count=len(docs),
        entity_count=ent_cnt,
        relationship_count=rel_cnt,
        community_count=comm_count,
        insight_count=ins_cnt,
        canonical_entity_ids=sorted(list(canonical_cids)),
        documents=[DocumentOut.model_validate(d) for d in docs],
        top_connected_entities=top_connected,
    )


# ---------------------------------------------------------------------------
# Source summary (for Overview dashboard)
# ---------------------------------------------------------------------------
@router.get("/sources/summary", response_model=list[SourceSummaryItem])
async def sources_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Document.source_type,
            func.count(Document.id).label("document_count"),
            func.coalesce(func.sum(Document.record_count), 0).label("record_count"),
        ).group_by(Document.source_type)
    )
    rows = result.all()
    return [
        SourceSummaryItem(
            source_type=row.source_type,
            document_count=row.document_count,
            record_count=int(row.record_count),
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    case_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    source_type = normalize_source_type(source_type)
    if source_type not in SOURCE_TYPES:
        raise HTTPException(400, f"Invalid source_type. Must be one of: {list(SOURCE_TYPES)}")

    ALLOWED_EXTENSIONS = {"csv", "txt", "pdf", "json"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Unsupported file extension '.{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, "Uploaded file exceeds maximum permitted size of 10MB.")

    # Parse with the matching adapter
    try:
        adapter = get_adapter(source_type)
        records = adapter.parse(file_bytes)
    except Exception as exc:
        logger.error("Adapter parse error: %s", exc)
        raise HTTPException(422, f"Could not parse file: {exc}")

    doc = Document(
        case_id=case_id,
        filename=filename,
        source_type=source_type,
        file_type=ext,
        raw_text=file_bytes.decode("utf-8", errors="replace")[:50_000],
        status="uploaded",
        record_count=len(records),
        structured_payload=[r.raw_fields for r in records],
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


# ---------------------------------------------------------------------------
# List documents
# ---------------------------------------------------------------------------
@router.get("", response_model=list[DocumentOut])
async def list_documents(
    source_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Document).order_by(Document.uploaded_at.desc())
    if source_type:
        q = q.where(Document.source_type == source_type)
    result = await db.execute(q)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Process a document (cleaning → NER → resolution → KG)
# ---------------------------------------------------------------------------
@router.post("/{doc_id}/process", response_model=ProcessResult)
async def process_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.status == "processing":
        raise HTTPException(409, "Document is already being processed")

    filename_str = doc.filename or "unknown"
    source_type_str = normalize_source_type(doc.source_type)
    doc.status = "processing"
    doc.source_type = source_type_str
    await db.commit()

    stage = "ADAPTER_PARSE"
    try:
        adapter = get_adapter(source_type_str)
        raw_bytes = (doc.raw_text or "").encode("utf-8")
        records = adapter.parse(raw_bytes)

        all_entities = []
        total_nodes = 0
        total_edges = 0
        resolution_count = 0

        for record in records:
            # 1. Clean
            stage = "CLEANING"
            cleaned = clean_record(record)

            # 2. NER
            stage = "NER_EXTRACTION"
            ner_entities = extract_entities(cleaned.raw_text)

            # 3. Store extracted entities in SQLite
            stage = "DATABASE_ENTITY_STORE"
            for ent in ner_entities:
                cid = canonical_id(ent.entity_type, ent.normalized_text)
                db_ent = ExtractedEntity(
                    document_id=doc.id,
                    text=ent.text,
                    entity_type=ent.entity_type,
                    normalized_text=ent.normalized_text,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    context_snippet=ent.context_snippet[:500],
                    canonical_entity_id=cid,
                )
                db.add(db_ent)
                all_entities.append(ent)

            # 4. Build graph
            stage = "KNOWLEDGE_GRAPH_BUILD"
            try:
                nodes, edges = await build_graph(cleaned, ner_entities, str(doc.id))
                total_nodes += nodes
                total_edges += edges
            except Exception as graph_err:
                logger.warning("Graph building non-fatal warning for doc %d: %s", doc_id, graph_err)

        await db.flush()

        # 5. System-wide entity resolution across stored entities
        stage = "ENTITY_RESOLUTION"
        cand_res = await db.execute(
            select(ResolutionCandidate.entity_a_id, ResolutionCandidate.entity_b_id)
        )
        existing_pairs = {
            tuple(sorted((row[0], row[1]))) for row in cand_res.all()
        }

        all_ent_res = await db.execute(select(ExtractedEntity))
        all_system_entities = all_ent_res.scalars().all()

        if all_system_entities:
            candidates = resolve_entities(all_system_entities, existing_pairs=existing_pairs)
            resolution_count = len(candidates)

            for cand in candidates:
                rc = ResolutionCandidate(
                    entity_a_id=cand.entity_a.id,
                    entity_b_id=cand.entity_b.id,
                    entity_type=cand.entity_a.entity_type,
                    similarity_score=cand.similarity_score,
                    match_reason=cand.match_reason,
                    decision=cand.decision,
                )
                db.add(rc)
                existing_pairs.add(tuple(sorted((cand.entity_a.id, cand.entity_b.id))))

                # If auto-merged, unify Neo4j nodes if different
                if cand.decision == "auto_merged":
                    stage = "NEO4J_MERGE"
                    if cand.entity_a.canonical_entity_id and cand.entity_b.canonical_entity_id:
                        if cand.entity_a.canonical_entity_id != cand.entity_b.canonical_entity_id:
                            try:
                                from app.routers.resolution import _merge_neo4j_nodes
                                await _merge_neo4j_nodes(
                                    cand.entity_a.canonical_entity_id,
                                    cand.entity_b.canonical_entity_id,
                                )
                                cand.entity_b.canonical_entity_id = cand.entity_a.canonical_entity_id
                            except Exception as merge_err:
                                logger.warning("Neo4j merge non-fatal warning for doc %d: %s", doc_id, merge_err)

        stage = "COMMIT"
        doc.status = "processed"
        doc.error_message = None
        doc.cleaned_text = " ".join(r.raw_text for r in records)[:50_000]
        await db.commit()

        return ProcessResult(
            document_id=doc.id,
            records_parsed=len(records),
            entities_extracted=len(all_entities),
            resolution_candidates=resolution_count,
            graph_nodes_upserted=total_nodes,
            graph_edges_upserted=total_edges,
            status="processed",
        )

    except Exception as exc:
        logger.exception(
            "[Doc %d (%s, type=%s, stage=%s)] Processing failed: %s",
            doc_id, filename_str, source_type_str, stage, exc
        )
        await db.rollback()
        try:
            fail_doc = await db.get(Document, doc_id)
            if fail_doc:
                fail_doc.status = "failed"
                fail_doc.error_message = f"[{stage}] {str(exc)}"
                await db.commit()
        except Exception as rollback_err:
            logger.warning("Could not set failed status on doc %d: %s", doc_id, rollback_err)
        raise HTTPException(500, f"Processing failed at stage [{stage}]: {exc}")


@router.get("/{doc_id}/detail", response_model=DocumentDetailOut)
async def get_document_detail(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Return comprehensive detail for a single document including extracted entities and errors."""
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    case_code = None
    case_title = None
    if doc.case_id:
        c = await db.get(Case, doc.case_id)
        if c:
            case_code = c.case_code
            case_title = c.title

    ents_res = await db.execute(
        select(ExtractedEntity).where(ExtractedEntity.document_id == doc_id)
    )
    ents = ents_res.scalars().all()
    ent_list = [
        {
            "id": e.id,
            "text": e.text,
            "entity_type": e.entity_type,
            "normalized_text": e.normalized_text,
            "canonical_entity_id": e.canonical_entity_id,
            "context_snippet": e.context_snippet,
        }
        for e in ents
    ]

    return DocumentDetailOut(
        id=doc.id,
        case_id=doc.case_id,
        case_code=case_code,
        case_title=case_title,
        filename=doc.filename,
        source_type=doc.source_type,
        file_type=doc.file_type,
        status=doc.status,
        uploaded_at=doc.uploaded_at,
        record_count=doc.record_count,
        raw_text=doc.raw_text or "",
        cleaned_text=doc.cleaned_text or "",
        error_message=doc.error_message,
        extracted_entities=ent_list,
    )

