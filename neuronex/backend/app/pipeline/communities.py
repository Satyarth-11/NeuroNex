"""
NeuroNex — Community Detection Module
Isolated behind detect_communities() so the algorithm can be swapped via config.

Primary algorithm: Louvain (python-louvain)
Fallback: NetworkX greedy_modularity_communities

Returns a list of community dicts with members, density, source type breakdown,
and a plain-language summary.
"""
from __future__ import annotations
import logging
import networkx as nx
from app.db_graph import run_query

logger = logging.getLogger(__name__)


async def _load_undirected_graph() -> nx.Graph:
    """Load Neo4j graph as undirected NetworkX graph for community detection."""
    G = nx.Graph()

    nodes = await run_query(
        "MATCH (n) RETURN n.id AS id, n.name AS name, "
        "n.entity_type AS entity_type, n.source_types AS source_types"
    )
    for row in nodes:
        if row.get("id"):
            G.add_node(
                row["id"],
                name=row.get("name", ""),
                entity_type=row.get("entity_type", ""),
                source_types=row.get("source_types") or [],
            )

    edges = await run_query(
        "MATCH (a)-[r]->(b) RETURN a.id AS src, b.id AS dst, r.weight AS weight"
    )
    for row in edges:
        if row.get("src") and row.get("dst"):
            G.add_edge(row["src"], row["dst"], weight=row.get("weight", 1))

    return G


def _compute_louvain(G: nx.Graph) -> list[set]:
    """Run Louvain algorithm; return list of node sets per community."""
    try:
        import community as community_louvain
        partition: dict[str, int] = community_louvain.best_partition(G)
        communities: dict[int, set] = {}
        for node, comm_id in partition.items():
            communities.setdefault(comm_id, set()).add(node)
        return list(communities.values())
    except Exception as exc:
        logger.warning("Louvain failed (%s), falling back to greedy modularity", exc)
        return _compute_greedy(G)


def _compute_greedy(G: nx.Graph) -> list[set]:
    """Greedy modularity fallback."""
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        return [set(c) for c in greedy_modularity_communities(G)]
    except Exception as exc:
        logger.error("Greedy modularity also failed: %s", exc)
        return []


def detect_communities(G: nx.Graph) -> list[set]:
    """
    Isolated entry point — swap algorithm here without touching callers.
    Returns list of sets of node IDs.
    """
    return _compute_louvain(G)


async def get_communities() -> list[dict]:
    """
    Detect communities in the current graph and return enriched community dicts.
    Each dict contains: community_id, members, member_count,
    internal_edge_density, source_types, summary.
    """
    G = await _load_undirected_graph()
    if G.number_of_nodes() == 0:
        return []

    raw_communities = detect_communities(G)

    result = []
    for idx, node_set in enumerate(sorted(raw_communities, key=len, reverse=True)):
        subgraph = G.subgraph(node_set)

        # Internal edge density
        density = nx.density(subgraph) if len(node_set) > 1 else 0.0

        # Collect source types across all members
        all_source_types: set[str] = set()
        members = []
        for nid in node_set:
            data = G.nodes[nid]
            for st in data.get("source_types", []):
                all_source_types.add(st)
            members.append({
                "node_id": nid,
                "name": data.get("name", ""),
                "entity_type": data.get("entity_type", ""),
            })

        source_types = sorted(all_source_types)
        summary = (
            f"Community {idx + 1} contains {len(node_set)} entities with "
            f"{subgraph.number_of_edges()} internal connections "
            f"(density {density:.2f}). "
            f"Data sources: {', '.join(source_types) if source_types else 'unknown'}. "
            f"This is a detected network pattern, not a factual finding. "
            f"Human analyst review is required before any action."
        )

        result.append({
            "community_id": idx,
            "members": members,
            "member_count": len(node_set),
            "internal_edge_density": round(density, 4),
            "source_types": source_types,
            "summary": summary,
        })

    return result


async def get_community_detail(community_id: int) -> dict | None:
    """Return enriched details for a single community cluster."""
    comms = await get_communities()
    target = None
    for c in comms:
        if c.get("community_id") == community_id:
            target = c
            break
    if not target:
        return None

    members = target.get("members", [])
    type_counts = {"PERSON": 0, "PHONE": 0, "VEHICLE": 0, "LOCATION": 0, "ACCOUNT": 0, "OTHER": 0}
    for m in members:
        t = (m.get("entity_type") or "OTHER").upper()
        if t in type_counts:
            type_counts[t] += 1
        else:
            type_counts["OTHER"] += 1

    member_ids = [m["node_id"] for m in members]
    cases = []
    if member_ids:
        try:
            cypher = """
            MATCH (n)-[r]-(target)
            WHERE n.id IN $node_ids AND r.related_case IS NOT NULL AND r.related_case <> ''
            RETURN DISTINCT r.related_case AS case_code
            """
            res = await run_query(cypher, {"node_ids": member_ids})
            cases = sorted([r["case_code"] for r in res if r.get("case_code")])
        except Exception as e:
            logger.warning("Could not query community cases: %s", e)

    G = await _load_undirected_graph()
    subgraph = G.subgraph(member_ids)
    degrees = dict(subgraph.degree())
    sorted_members = sorted(members, key=lambda m: degrees.get(m["node_id"], 0), reverse=True)

    from app.pipeline.explainability import generate_community_insight
    ins = generate_community_insight(target)

    return {
        "community_id": community_id,
        "member_count": len(members),
        "members": members,
        "type_counts": type_counts,
        "person_count": type_counts.get("PERSON", 0),
        "phone_count": type_counts.get("PHONE", 0),
        "vehicle_count": type_counts.get("VEHICLE", 0),
        "location_count": type_counts.get("LOCATION", 0),
        "account_count": type_counts.get("ACCOUNT", 0),
        "related_cases": cases,
        "source_types": target.get("source_types", []),
        "internal_edge_density": target.get("internal_edge_density", 0.0),
        "key_members": sorted_members[:5],
        "explanation": ins.get("explanation", target.get("summary", "")),
    }

