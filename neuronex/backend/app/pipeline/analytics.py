"""
NeuroNex — Graph Analytics Module
Pulls the Neo4j graph into NetworkX and computes:
  - Degree centrality
  - Betweenness centrality
  - Network density
  - Shortest paths between two nodes

All results are returned as plain Python dicts / lists — no ORM objects.
"""
from __future__ import annotations
import logging
import networkx as nx
from app.db_graph import run_query

logger = logging.getLogger(__name__)


async def _load_graph() -> nx.DiGraph:
    """Load the current Neo4j graph into a NetworkX DiGraph."""
    G = nx.DiGraph()

    # Load nodes
    nodes = await run_query(
        "MATCH (n) RETURN n.id AS id, n.name AS name, n.entity_type AS entity_type, "
        "n.source_types AS source_types, n.mention_count AS mention_count"
    )
    for row in nodes:
        if row.get("id"):
            G.add_node(
                row["id"],
                name=row.get("name", ""),
                entity_type=row.get("entity_type", ""),
                source_types=row.get("source_types") or [],
                mention_count=row.get("mention_count", 1),
            )

    # Load edges
    edges = await run_query(
        "MATCH (a)-[r]->(b) RETURN a.id AS src, b.id AS dst, "
        "type(r) AS rel_type, r.weight AS weight, r.source_types AS source_types"
    )
    for row in edges:
        if row.get("src") and row.get("dst"):
            G.add_edge(
                row["src"], row["dst"],
                rel_type=row.get("rel_type", ""),
                weight=row.get("weight", 1),
                source_types=row.get("source_types") or [],
            )

    logger.info("NetworkX graph loaded: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return G


async def get_centrality() -> dict:
    """Compute degree + betweenness centrality for all nodes."""
    G = await _load_graph()
    if G.number_of_nodes() == 0:
        return {"nodes": [], "stats": {"node_count": 0, "edge_count": 0, "density": 0.0}}

    undirected = G.to_undirected()
    degree_c = nx.degree_centrality(undirected)
    try:
        betweenness_c = nx.betweenness_centrality(undirected, normalized=True)
    except Exception:
        betweenness_c = {n: 0.0 for n in undirected.nodes}

    density = nx.density(undirected)

    try:
        pagerank = nx.pagerank(G, weight='weight') if G.number_of_edges() > 0 else {n: 0.0 for n in G.nodes}
    except Exception as pr_err:
        logger.warning("nx.pagerank failed (%s); using power iteration fallback", pr_err)
        nodes_list = list(G.nodes)
        n_count = len(nodes_list)
        if n_count == 0 or G.number_of_edges() == 0:
            pagerank = {n: (1.0 / n_count if n_count else 0.0) for n in nodes_list}
        else:
            p = {n: 1.0 / n_count for n in nodes_list}
            alpha = 0.85
            for _ in range(50):
                next_p = {n: (1.0 - alpha) / n_count for n in nodes_list}
                for u in nodes_list:
                    out_deg = G.out_degree(u, weight='weight')
                    if out_deg == 0:
                        for v in nodes_list:
                            next_p[v] += alpha * p[u] / n_count
                    else:
                        for _, v, edata in G.out_edges(u, data=True):
                            w = edata.get('weight', 1.0)
                            next_p[v] += alpha * p[u] * (w / out_deg)
                p = next_p
            pagerank = p
    try:
        eigenvector = nx.eigenvector_centrality(undirected, max_iter=500, weight='weight')
    except (nx.PowerIterationFailedConvergence, nx.NetworkXError):
        eigenvector = {n: 0.0 for n in undirected.nodes}

    results = []
    for node_id, data in G.nodes(data=True):
        results.append({
            "node_id": node_id,
            "name": data.get("name", ""),
            "entity_type": data.get("entity_type", ""),
            "degree_centrality": round(degree_c.get(node_id, 0.0), 4),
            "betweenness_centrality": round(betweenness_c.get(node_id, 0.0), 4),
            "pagerank": round(pagerank.get(node_id, 0.0), 4),
            "eigenvector_centrality": round(eigenvector.get(node_id, 0.0), 4),
            "source_types": data.get("source_types", []),
            "mention_count": data.get("mention_count", 1),
        })

    # Rank by combined network influence (betweenness + PageRank)
    results.sort(key=lambda x: (x["betweenness_centrality"] + x["pagerank"]), reverse=True)

    return {
        "nodes": results,
        "stats": {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": round(density, 4),
        },
    }


async def get_top_entities(n: int = 10, entity_type: str | None = None) -> list[dict]:
    """Return top-N entities by combined influence (betweenness + PageRank), optionally filtered by entity_type."""
    result = await get_centrality()
    nodes = result["nodes"]
    if entity_type:
        nodes = [x for x in nodes if (x.get("entity_type") or "").upper() == entity_type.upper()]
    return nodes[:n]


async def get_key_influencers(limit: int = 10) -> list[dict]:
    """
    Key influencer detection for PERSON entities only.
    Ranked by (betweenness_centrality + pagerank) descending.
    Includes related cases, community_id, and explainability text.
    """
    from app.pipeline.communities import get_communities
    from app.pipeline.explainability import generate_key_influencer_explanation
    from app.db_graph import run_query

    top_persons = await get_top_entities(n=limit * 2, entity_type="PERSON")

    # Get communities mapping
    comms_data = await get_communities()
    node_to_comm = {}
    comms_list = comms_data if isinstance(comms_data, list) else (comms_data.get("communities", []) if isinstance(comms_data, dict) else [])
    for c in comms_list:
        cid = c.get("community_id")
        for m in c.get("members", []):
            node_to_comm[m.get("node_id")] = cid

    # Query related cases from Neo4j edges
    cases_query = """
    MATCH (n)-[r]-(target)
    WHERE n.id IN $node_ids
    RETURN n.id AS node_id, collect(DISTINCT r.related_case) AS cases
    """
    node_ids = [p["node_id"] for p in top_persons]
    cases_map = {}
    if node_ids:
        try:
            res = await run_query(cases_query, {"node_ids": node_ids})
            for row in res:
                raw_cases = [c for c in row.get("cases", []) if c]
                cases_map[row["node_id"]] = sorted(list(set(raw_cases)))
        except Exception as e:
            logger.warning("Could not fetch related cases for influencers: %s", e)

    influencers = []
    for p in top_persons[:limit]:
        nid = p["node_id"]
        comm_id = node_to_comm.get(nid)
        rel_cases = cases_map.get(nid, [])
        inf_dict = {
            "node_id": nid,
            "name": p.get("name", ""),
            "entity_type": "PERSON",
            "degree_centrality": p.get("degree_centrality", 0.0),
            "betweenness_centrality": p.get("betweenness_centrality", 0.0),
            "pagerank": p.get("pagerank", 0.0),
            "eigenvector_centrality": p.get("eigenvector_centrality", 0.0),
            "related_cases": rel_cases,
            "community_id": comm_id,
        }
        inf_dict["explanation"] = generate_key_influencer_explanation(inf_dict)
        influencers.append(inf_dict)

    return influencers


async def get_shortest_path(src_id: str, dst_id: str) -> list[str]:
    """Return shortest path node IDs between src and dst in Neo4j graph."""
    G = await _load_graph()
    undirected = G.to_undirected()
    try:
        path = nx.shortest_path(undirected, source=src_id, target=dst_id)
        return path
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []
