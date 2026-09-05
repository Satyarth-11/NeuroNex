"""
NeuroNex — Graph Router
Serves Cytoscape.js-ready graph data from Neo4j.
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Query
from app.db_graph import run_query
from app.pipeline.analytics import get_shortest_path

router = APIRouter(prefix="/api/graph", tags=["graph"])

_LABEL_COLORS = {
    "Person": "#6366f1",
    "Phone": "#22d3ee",
    "Location": "#10b981",
    "Vehicle": "#f59e0b",
    "Organisation": "#ec4899",
    "Case": "#f87171",
    "Account": "#a78bfa",
}


def _node_to_cy(node: dict) -> dict:
    label = node.get("entity_type", "Entity")
    return {
        "data": {
            "id": node.get("id", ""),
            "label": node.get("name", ""),
            "entity_type": label,
            "source_types": node.get("source_types") or [],
            "mention_count": node.get("mention_count", 1),
            "criminal_history_flag": node.get("criminal_history_flag", False),
            "color": _LABEL_COLORS.get(label, "#94a3b8"),
        }
    }


def _edge_to_cy(edge: dict, idx: int) -> dict:
    return {
        "data": {
            "id": f"e{idx}",
            "source": edge.get("src", ""),
            "target": edge.get("dst", ""),
            "rel_type": edge.get("rel_type", ""),
            "weight": edge.get("weight", 1),
            "source_types": edge.get("source_types") or [],
            "status": edge.get("status", "proposed"),
            "confidence": edge.get("confidence", 0.75),
            "related_case": edge.get("related_case", ""),
            "evidence_snippets": edge.get("evidence_snippets") or [],
        }
    }


@router.get("")
async def get_graph(
    case_code: Optional[str] = None,
    entity_type: Optional[str] = None,
    source_type: Optional[str] = None,
    relationship_type: Optional[str] = None,
    status: Optional[str] = None,
    depth: int = Query(1, ge=1, le=3),
    limit: int = Query(40, ge=1, le=500),
):
    """
    Cytoscape elements JSON format.
    Supports case-scoped subgraph querying (case_code), entity_type, source_type,
    relationship_type, status, and node limits.
    """
    from sqlalchemy import select
    from app.db_sql import AsyncSessionLocal
    from app.models_sql import Case, Document, ExtractedEntity

    target_node_ids: set[str] | None = None

    # If case_code is provided, find canonical entity IDs reachable via documents of that case
    if case_code:
        async with AsyncSessionLocal() as session:
            case_res = await session.execute(select(Case).where(Case.case_code == case_code))
            case_obj = case_res.scalar_one_or_none()
            if case_obj:
                doc_res = await session.execute(
                    select(Document.id).where(Document.case_id == case_obj.id)
                )
                doc_ids = [d[0] for d in doc_res.all()]
                if doc_ids:
                    ent_res = await session.execute(
                        select(ExtractedEntity.canonical_entity_id).where(
                            ExtractedEntity.document_id.in_(doc_ids),
                            ExtractedEntity.canonical_entity_id.isnot(None),
                        )
                    )
                    target_node_ids = {str(cid) for (cid,) in ent_res.all() if cid}
                else:
                    target_node_ids = set()
            else:
                target_node_ids = set()

    # Build node query conditions
    node_where = []
    node_params = {}
    if entity_type:
        node_where.append("toLower(n.entity_type) = toLower($entity_type)")
        node_params["entity_type"] = entity_type
    if source_type:
        node_where.append("$source_type IN n.source_types")
        node_params["source_type"] = source_type
    if target_node_ids is not None:
        node_where.append("n.id IN $case_node_ids")
        node_params["case_node_ids"] = list(target_node_ids)

    node_filter = ("WHERE " + " AND ".join(node_where)) if node_where else ""

    nodes_raw = await run_query(
        f"MATCH (n) {node_filter} RETURN n.id AS id, n.name AS name, "
        f"n.entity_type AS entity_type, n.source_types AS source_types, "
        f"n.mention_count AS mention_count, n.criminal_history_flag AS criminal_history_flag "
        f"LIMIT $limit",
        {**node_params, "limit": limit},
    )

    node_ids = {n.get("id") for n in nodes_raw}
    if not node_ids:
        reason = "filter_empty" if (entity_type or source_type) else ("no_entities" if case_code else "empty_graph")
        return {
            "nodes": [],
            "edges": [],
            "case_code": case_code,
            "total_nodes": 0,
            "total_edges": 0,
            "empty_reason": reason,
        }

    # Build edge query conditions
    edge_where = ["a.id IN $node_ids", "b.id IN $node_ids"]
    edge_params = {"node_ids": list(node_ids)}

    if status:
        edge_where.append("r.status = $status")
        edge_params["status"] = status
    if source_type:
        edge_where.append("$source_type IN r.source_types")
        edge_params["source_type"] = source_type
    if case_code:
        # Prioritize edges recorded under this case or linking case entities
        edge_where.append("(r.related_case = $case_code OR r.related_case IS NULL OR r.related_case = '')")
        edge_params["case_code"] = case_code

    rel_match_type = f":{relationship_type}" if relationship_type else ""
    edge_filter = "WHERE " + " AND ".join(edge_where)

    edges_raw = await run_query(
        f"MATCH (a)-[r{rel_match_type}]->(b) {edge_filter} "
        f"RETURN a.id AS src, b.id AS dst, type(r) AS rel_type, "
        f"r.weight AS weight, r.source_types AS source_types, r.status AS status, "
        f"r.confidence AS confidence, r.related_case AS related_case, "
        f"r.evidence_snippets AS evidence_snippets",
        edge_params,
    )

    filtered_edges = [e for e in edges_raw if e.get("src") in node_ids and e.get("dst") in node_ids]

    empty_reason = None
    if len(filtered_edges) == 0:
        if relationship_type or status or source_type:
            empty_reason = "filter_empty"
        elif case_code:
            empty_reason = "no_relationships"

    return {
        "nodes": [_node_to_cy(n) for n in nodes_raw],
        "edges": [_edge_to_cy(e, i) for i, e in enumerate(filtered_edges)],
        "case_code": case_code,
        "total_nodes": len(nodes_raw),
        "total_edges": len(filtered_edges),
        "empty_reason": empty_reason,
    }


@router.get("/neighbors/{node_id}")
async def get_neighbors(node_id: str, depth: int = Query(1, ge=1, le=3)):
    """Ego-network: return node + its neighbors up to `depth` hops."""
    rows = await run_query(
        f"MATCH (n {{id: $nid}})-[r*1..{depth}]-(neighbor) "
        f"RETURN DISTINCT neighbor.id AS id, neighbor.name AS name, "
        f"neighbor.entity_type AS entity_type, neighbor.source_types AS source_types, "
        f"neighbor.mention_count AS mention_count",
        {"nid": node_id},
    )
    # Also fetch the central node
    center = await run_query(
        "MATCH (n {id: $nid}) RETURN n.id AS id, n.name AS name, "
        "n.entity_type AS entity_type, n.source_types AS source_types, "
        "n.mention_count AS mention_count",
        {"nid": node_id},
    )
    all_nodes = center + rows
    all_ids = {n.get("id") for n in all_nodes}

    edges_raw = await run_query(
        f"MATCH (a)-[r]->(b) WHERE a.id IN $ids AND b.id IN $ids "
        f"RETURN a.id AS src, b.id AS dst, type(r) AS rel_type, "
        f"r.weight AS weight, r.source_types AS source_types",
        {"ids": list(all_ids)},
    )

    return {
        "nodes": [_node_to_cy(n) for n in all_nodes],
        "edges": [_edge_to_cy(e, i) for i, e in enumerate(edges_raw)],
    }


@router.get("/path")
async def get_path(src: str, dst: str):
    """Shortest path between two entities (returns node ids)."""
    path = await get_shortest_path(src, dst)
    if not path:
        return {"path": [], "found": False}

    # Enrich with names
    nodes_raw = await run_query(
        "MATCH (n) WHERE n.id IN $ids RETURN n.id AS id, n.name AS name, "
        "n.entity_type AS entity_type",
        {"ids": path},
    )
    node_map = {n["id"]: n for n in nodes_raw}

    return {
        "path": [node_map.get(nid, {"id": nid}) for nid in path],
        "found": True,
    }


@router.get("/edge/{src_id}/{dst_id}/{rel_type}")
async def get_edge(src_id: str, dst_id: str, rel_type: str):
    """
    Return full provenance details for a relationship between two nodes.
    Includes source_types, source_doc_ids, evidence_snippets, confidence,
    related_case, last_updated, weight, and status.
    """
    cypher = """
    MATCH (a {id: $src})-[r]->(b {id: $dst})
    WHERE type(r) = $rel_type
    RETURN a.id AS src_id, a.name AS src_name, b.id AS dst_id, b.name AS dst_name,
           type(r) AS rel_type, r.weight AS weight, r.source_types AS source_types,
           r.source_doc_ids AS source_doc_ids, r.evidence_snippets AS evidence_snippets,
           r.confidence AS confidence, r.related_case AS related_case,
           toString(r.last_updated) AS last_updated, r.status AS status
    LIMIT 1
    """
    records = await run_query(cypher, {"src": src_id, "dst": dst_id, "rel_type": rel_type})

    if not records:
        # Fallback query without directional constraint if needed
        cypher_rev = """
        MATCH (a {id: $dst})-[r]->(b {id: $src})
        WHERE type(r) = $rel_type
        RETURN a.id AS src_id, a.name AS src_name, b.id AS dst_id, b.name AS dst_name,
               type(r) AS rel_type, r.weight AS weight, r.source_types AS source_types,
               r.source_doc_ids AS source_doc_ids, r.evidence_snippets AS evidence_snippets,
               r.confidence AS confidence, r.related_case AS related_case,
               toString(r.last_updated) AS last_updated, r.status AS status
        LIMIT 1
        """
        records = await run_query(cypher_rev, {"src": src_id, "dst": dst_id, "rel_type": rel_type})

    if not records:
        raise HTTPException(404, "Relationship not found")

    rec = records[0]
    return {
        "src_id": rec.get("src_id"),
        "src_name": rec.get("src_name"),
        "dst_id": rec.get("dst_id"),
        "dst_name": rec.get("dst_name"),
        "rel_type": rec.get("rel_type"),
        "weight": rec.get("weight", 1),
        "source_types": rec.get("source_types") or [],
        "source_doc_ids": rec.get("source_doc_ids") or [],
        "evidence_snippets": rec.get("evidence_snippets") or [],
        "confidence": rec.get("confidence") if rec.get("confidence") is not None else 0.75,
        "related_case": rec.get("related_case") or "",
        "last_updated": rec.get("last_updated") or "",
        "status": rec.get("status", "proposed"),
    }


@router.get("/edges/low-confidence")
async def get_low_confidence_edges(threshold: float = Query(0.75, ge=0.0, le=1.0)):
    """
    Find edges where confidence < threshold (default 0.75) requiring analyst review.
    Returns list of {src, src_name, dst, dst_name, rel_type, confidence,
                     evidence_snippets, related_case, source_types, status}
    """
    cypher = """
    MATCH (a)-[r]->(b)
    WHERE r.confidence IS NOT NULL AND r.confidence < $threshold
    RETURN a.id AS src, a.name AS src_name, b.id AS dst, b.name AS dst_name,
           type(r) AS rel_type, r.confidence AS confidence,
           r.evidence_snippets AS evidence_snippets, r.related_case AS related_case,
           r.source_types AS source_types, r.status AS status
    ORDER BY r.confidence ASC
    LIMIT 50
    """
    records = await run_query(cypher, {"threshold": threshold})
    return [
        {
            "id": f"{rec.get('src')}_{rec.get('dst')}_{rec.get('rel_type')}",
            "src": rec.get("src"),
            "src_name": rec.get("src_name") or rec.get("src"),
            "dst": rec.get("dst"),
            "dst_name": rec.get("dst_name") or rec.get("dst"),
            "rel_type": rec.get("rel_type"),
            "confidence": round(float(rec.get("confidence", 0.0)), 3),
            "evidence_snippets": rec.get("evidence_snippets") or [],
            "related_case": rec.get("related_case") or "",
            "source_types": rec.get("source_types") or [],
            "status": rec.get("status") or "proposed",
        }
        for rec in records
    ]


@router.post("/edge/review")
async def review_edge(payload: dict):
    """Update edge status (approved, rejected, flagged) in Neo4j."""
    src = payload.get("src")
    dst = payload.get("dst")
    rel_type = payload.get("rel_type")
    decision = payload.get("decision", "approved")
    cypher = """
    MATCH (a {id: $src})-[r]->(b {id: $dst})
    WHERE type(r) = $rel_type
    SET r.status = $decision
    RETURN count(r) AS updated
    """
    await run_query(cypher, {"src": src, "dst": dst, "rel_type": rel_type, "decision": decision})
    return {"status": "success", "decision": decision}
