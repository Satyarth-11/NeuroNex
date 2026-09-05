"""
NeuroNex — Knowledge Graph Builder
Upserts entities as Neo4j nodes and infers relationships based on source-type rules.
Every node and edge is tagged with source_types[] and source_doc_ids[] for traceability.

Canonical ID: deterministic SHA-256 hash of (entity_type + normalised_text)
This ensures the same real-world entity always resolves to the same node regardless
of which document it was first seen in.
"""
from __future__ import annotations
import hashlib
import logging
from typing import Any

from app.db_graph import run_write_tx, run_query
from app.ingestion.base import InvestigationRecord, normalize_source_type
from app.pipeline.ner import ExtractedEntity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Node label mapping
# ---------------------------------------------------------------------------
_TYPE_TO_LABEL = {
    "PERSON": "Person",
    "PHONE": "Phone",
    "LOCATION": "Location",
    "VEHICLE": "Vehicle",
    "ORGANISATION": "Organisation",
    "CASE_REF": "Case",
    "ACCOUNT": "Account",
}


def canonical_id(entity_type: str, normalized_text: str) -> str:
    """Deterministic canonical ID: hash of type+normalised_text."""
    key = f"{entity_type}::{normalized_text.lower().strip()}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Node upsert
# ---------------------------------------------------------------------------
async def upsert_node(
    entity_type: str,
    normalized_text: str,
    source_type: str,
    doc_id: str,
    extra_props: dict | None = None,
) -> str:
    """Upsert a Neo4j node; returns canonical_id."""
    label = _TYPE_TO_LABEL.get(entity_type, "Entity")
    cid = canonical_id(entity_type, normalized_text)
    extra = extra_props or {}

    cypher = f"""
    MERGE (n:{label} {{id: $cid}})
    ON CREATE SET
        n.name = $name,
        n.entity_type = $entity_type,
        n.source_types = [$source_type],
        n.source_doc_ids = [$doc_id],
        n.mention_count = 1,
        n.confidence = 1.0,
        n.criminal_history_flag = $crim_flag,
        n.prior_case_refs = $prior_cases
    ON MATCH SET
        n.mention_count = n.mention_count + 1,
        n.source_types = CASE
            WHEN $source_type IN n.source_types THEN n.source_types
            ELSE n.source_types + [$source_type]
        END,
        n.source_doc_ids = CASE
            WHEN $doc_id IN n.source_doc_ids THEN n.source_doc_ids
            ELSE n.source_doc_ids + [$doc_id]
        END
    RETURN n.id
    """
    await run_write_tx(cypher, {
        "cid": cid,
        "name": normalized_text,
        "entity_type": entity_type,
        "source_type": source_type,
        "doc_id": doc_id,
        "crim_flag": extra.get("criminal_history_flag", False),
        "prior_cases": extra.get("prior_case_refs", []),
    })
    return cid


# ---------------------------------------------------------------------------
# Edge upsert
# ---------------------------------------------------------------------------
async def upsert_edge(
    src_id: str,
    dst_id: str,
    rel_type: str,
    source_type: str,
    doc_id: str,
    weight: int = 1,
    evidence_snippet: str = "",
    confidence: float = 0.75,
    case_ref: str = "",
):
    """Upsert a directed relationship; increment weight and enrich provenance."""
    cypher = f"""
    MATCH (a {{id: $src}}), (b {{id: $dst}})
    MERGE (a)-[r:{rel_type}]->(b)
    ON CREATE SET
        r.weight = $weight,
        r.source_types = [$source_type],
        r.source_doc_ids = [$doc_id],
        r.evidence_snippets = CASE WHEN $evidence <> '' THEN [$evidence] ELSE [] END,
        r.confidence = $confidence,
        r.related_case = $case_ref,
        r.last_updated = toString(datetime()),
        r.status = 'proposed'
    ON MATCH SET
        r.weight = r.weight + $weight,
        r.source_types = CASE
            WHEN $source_type IN r.source_types THEN r.source_types
            ELSE r.source_types + [$source_type]
        END,
        r.source_doc_ids = CASE
            WHEN $doc_id IN r.source_doc_ids THEN r.source_doc_ids
            ELSE r.source_doc_ids + [$doc_id]
        END,
        r.evidence_snippets = CASE
            WHEN $evidence = '' THEN coalesce(r.evidence_snippets, [])
            WHEN $evidence IN coalesce(r.evidence_snippets, []) THEN coalesce(r.evidence_snippets, [])
            WHEN size(coalesce(r.evidence_snippets, [])) >= 5 THEN coalesce(r.evidence_snippets, [])
            ELSE coalesce(r.evidence_snippets, []) + [$evidence]
        END,
        r.confidence = CASE WHEN $confidence > coalesce(r.confidence, 0.0) THEN $confidence ELSE r.confidence END,
        r.related_case = CASE WHEN coalesce(r.related_case, '') = '' THEN $case_ref ELSE r.related_case END,
        r.last_updated = toString(datetime())
    """
    await run_write_tx(cypher, {
        "src": src_id,
        "dst": dst_id,
        "source_type": source_type,
        "doc_id": doc_id,
        "weight": weight,
        "evidence": evidence_snippet[:300],
        "confidence": float(confidence),
        "case_ref": case_ref or "",
    })


# ---------------------------------------------------------------------------
# Source-type relationship inference rules
# ---------------------------------------------------------------------------
async def _build_fir_edges(record: InvestigationRecord, entity_ids: dict[str, list[str]], doc_id: str) -> int:
    """FIR: accused persons → MENTIONED_IN → Case; persons → LOCATED_AT → locations."""
    edge_count = 0
    case_ref = record.case_ref or ""
    raw = record.raw_fields
    fir_no = raw.get("fir_no", case_ref)
    narrative = raw.get("narrative_text", "")
    evidence = f"FIR {fir_no} mention: {narrative[:150]}" if narrative else f"Mentioned in FIR {fir_no}"

    if case_ref:
        case_cid = canonical_id("CASE_REF", case_ref)
        for etype, cids in entity_ids.items():
            if etype.startswith("PERSON"):
                for cid in cids:
                    await upsert_edge(
                        cid, case_cid, "MENTIONED_IN", "fir", doc_id,
                        evidence_snippet=evidence, confidence=0.85, case_ref=case_ref,
                    )
                    edge_count += 1
    return edge_count


async def _build_cdr_edges(record: InvestigationRecord, entity_ids: dict[str, list[str]], doc_id: str) -> int:
    """CDR: caller → CONTACTED → callee (phone nodes)."""
    edge_count = 0
    raw = record.raw_fields
    caller = raw.get("caller_number", "")
    callee = raw.get("callee_number", "")
    case_ref = record.case_ref or ""
    ctype = raw.get("call_type", "voice")
    tower = raw.get("cell_tower_location", "")
    duration = int(raw.get("duration_sec", 1) or 1)

    if caller and callee:
        src_cid = await upsert_node("PHONE", caller, "cdr", doc_id)
        dst_cid = await upsert_node("PHONE", callee, "cdr", doc_id)
        evidence = f"{ctype.upper()} contact ({duration}s) via tower {tower}" if tower else f"{ctype.upper()} contact ({duration}s)"
        await upsert_edge(
            src_cid, dst_cid, "CONTACTED", "cdr", doc_id,
            weight=duration, evidence_snippet=evidence, confidence=0.90, case_ref=case_ref,
        )
        edge_count += 1

        # Link tower location
        if tower:
            loc_cid = await upsert_node("LOCATION", tower, "cdr", doc_id)
            loc_evidence = f"Cell tower signal observed at {tower}"
            await upsert_edge(
                src_cid, loc_cid, "LOCATED_AT", "cdr", doc_id,
                evidence_snippet=loc_evidence, confidence=0.90, case_ref=case_ref,
            )
            edge_count += 1
    return edge_count


async def _build_financial_edges(record: InvestigationRecord, entity_ids: dict[str, list[str]], doc_id: str) -> int:
    """Financial: sender → ASSOCIATED_WITH → receiver (account nodes)."""
    edge_count = 0
    raw = record.raw_fields
    sender = raw.get("sender_account", "")
    receiver = raw.get("receiver_account", "")
    case_ref = record.case_ref or ""
    mode = raw.get("txn_mode", "transfer")
    remarks = raw.get("remarks", "")
    amount = int(float(raw.get("amount", 1) or 1))

    if sender and receiver:
        src_cid = await upsert_node("ACCOUNT", sender, "financial", doc_id)
        dst_cid = await upsert_node("ACCOUNT", receiver, "financial", doc_id)
        evidence = f"{mode} txn ₹{amount:,}: {remarks[:120]}" if remarks else f"{mode} transaction ₹{amount:,}"
        await upsert_edge(
            src_cid, dst_cid, "TRANSFERRED_TO", "financial", doc_id,
            weight=amount, evidence_snippet=evidence, confidence=0.90, case_ref=case_ref,
        )
        edge_count += 1
    return edge_count


async def _build_social_edges(record: InvestigationRecord, entity_ids: dict[str, list[str]], doc_id: str) -> int:
    """Social media: poster → CONNECTED_TO → mentioned handles."""
    edge_count = 0
    raw = record.raw_fields
    poster = raw.get("display_name", raw.get("handle", ""))
    mentions_str = raw.get("mentioned_handles", "")
    post_text = raw.get("post_text", "")
    platform = raw.get("platform", "Social Media")
    case_ref = record.case_ref or ""

    if poster and mentions_str:
        poster_cid = await upsert_node("PERSON", poster, "social_media", doc_id)
        evidence = f"{platform} post by @{raw.get('handle', poster)}: \"{post_text[:120]}\""
        for handle in [h.strip() for h in mentions_str.split(";") if h.strip()]:
            handle_cid = await upsert_node("PERSON", handle, "social_media", doc_id)
            await upsert_edge(
                poster_cid, handle_cid, "CONNECTED_TO", "social_media", doc_id,
                evidence_snippet=evidence, confidence=0.75, case_ref=case_ref,
            )
            edge_count += 1
    return edge_count


async def _build_criminal_history_edges(
    record: InvestigationRecord, entity_ids: dict[str, list[str]], doc_id: str
) -> int:
    """Criminal history: person → ASSOCIATED_WITH → known associates."""
    edge_count = 0
    raw = record.raw_fields
    name = raw.get("name", "")
    prior_cases_str = raw.get("prior_cases", "")
    associates_str = raw.get("known_associates", "")
    prior_cases = [p.strip() for p in prior_cases_str.split(";") if p.strip()]
    case_ref = record.case_ref or ""

    if name:
        extra = {
            "criminal_history_flag": True,
            "prior_case_refs": prior_cases,
        }
        person_cid = await upsert_node("PERSON", name, "criminal_history", doc_id, extra_props=extra)

        for assoc in [a.strip() for a in associates_str.split(";") if a.strip()]:
            assoc_cid = await upsert_node("PERSON", assoc, "criminal_history", doc_id)
            assoc_evidence = f"Documented police associate of {name}"
            await upsert_edge(
                person_cid, assoc_cid, "ASSOCIATED_WITH", "criminal_history", doc_id,
                evidence_snippet=assoc_evidence, confidence=0.85, case_ref=case_ref,
            )
            edge_count += 1

        for p_case in prior_cases:
            case_cid = await upsert_node("CASE_REF", p_case, "criminal_history", doc_id)
            case_evidence = f"Prior case registration {p_case} for {name}"
            await upsert_edge(
                person_cid, case_cid, "INVOLVED_IN", "criminal_history", doc_id,
                evidence_snippet=case_evidence, confidence=0.90, case_ref=case_ref,
            )
            edge_count += 1
    return edge_count


# ---------------------------------------------------------------------------
# Main entry: build graph from a processed record + its extracted entities
# ---------------------------------------------------------------------------
async def build_graph(
    record: InvestigationRecord,
    entities: list[ExtractedEntity],
    doc_id: str,
) -> tuple[int, int]:
    """
    Upsert all entities as nodes and infer edges per source-type rules.
    Returns (nodes_upserted, edges_upserted).
    """
    nodes_upserted = 0
    edges_upserted = 0
    entity_ids: dict[str, list[str]] = {}  # entity_type → list of canonical_ids

    # Upsert all NER-extracted entity nodes
    for ent in entities:
        cid = await upsert_node(ent.entity_type, ent.normalized_text, record.source_type, doc_id)
        entity_ids.setdefault(ent.entity_type, []).append(cid)
        nodes_upserted += 1

    # Co-occurrence edges between persons in the same document
    person_cids = [
        canonical_id(e.entity_type, e.normalized_text)
        for e in entities if e.entity_type == "PERSON"
    ]
    co_evidence = f"Co-occurrence in {record.source_type} document #{doc_id}"
    for i in range(len(person_cids)):
        for j in range(i + 1, len(person_cids)):
            await upsert_edge(
                person_cids[i], person_cids[j],
                "ASSOCIATED_WITH", record.source_type, doc_id,
                weight=1,
                evidence_snippet=co_evidence,
                confidence=0.70,
                case_ref=record.case_ref or "",
            )
            edges_upserted += 1

    # Source-type specific structural edges
    stype = normalize_source_type(record.source_type)
    if stype == "fir":
        edges_upserted += await _build_fir_edges(record, entity_ids, doc_id)
    elif stype == "cdr":
        edges_upserted += await _build_cdr_edges(record, entity_ids, doc_id)
    elif stype == "financial":
        edges_upserted += await _build_financial_edges(record, entity_ids, doc_id)
    elif stype == "social_media":
        edges_upserted += await _build_social_edges(record, entity_ids, doc_id)
    elif stype == "criminal_history":
        edges_upserted += await _build_criminal_history_edges(record, entity_ids, doc_id)

    return nodes_upserted, edges_upserted
