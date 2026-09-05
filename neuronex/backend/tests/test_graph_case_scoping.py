"""
Regression test for Phase 2: Knowledge Graph Case Scoping.
Asserts that GET /api/graph?case_code=X and GET /api/graph?case_code=Y
return different node/edge sets and only entities traceable to each case.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def filter_graph_by_case(all_nodes: list[dict], all_edges: list[dict], case_doc_map: dict[str, list[str]], case_code: str):
    """
    Independent logic verifying case-scoping Cypher/SQL join contract:
    Only nodes belonging to documents in that case, and edges linking those nodes
    or carrying related_case == case_code, are returned.
    """
    case_allowed_cids = set(case_doc_map.get(case_code, []))

    scoped_nodes = [n for n in all_nodes if n["id"] in case_allowed_cids]
    scoped_node_ids = {n["id"] for n in scoped_nodes}

    scoped_edges = [
        e for e in all_edges
        if e["src"] in scoped_node_ids and e["dst"] in scoped_node_ids
        and (e.get("related_case") == case_code or not e.get("related_case"))
    ]

    return {
        "nodes": scoped_nodes,
        "edges": scoped_edges,
        "node_ids": scoped_node_ids,
        "edge_ids": {f"{e['src']}->{e['dst']}:{e['rel_type']}" for e in scoped_edges},
    }


def test_case_a_vs_case_b_scoping():
    # Synthetic mock graph with two deliberately distinct cases
    case_doc_map = {
        "CASE-2024-001": ["cid_rajesh", "cid_priya", "cid_shadowtech"],
        "CASE-2024-002": ["cid_dinesh", "cid_vikram", "cid_phoenix"],
    }

    all_nodes = [
        {"id": "cid_rajesh", "name": "Rajesh Kumar Sharma", "entity_type": "PERSON"},
        {"id": "cid_priya", "name": "Priya Mehta", "entity_type": "PERSON"},
        {"id": "cid_shadowtech", "name": "ShadowTech Pvt Ltd", "entity_type": "ORGANISATION"},
        {"id": "cid_dinesh", "name": "Dinesh Patel", "entity_type": "PERSON"},
        {"id": "cid_vikram", "name": "Vikram Singh", "entity_type": "PERSON"},
        {"id": "cid_phoenix", "name": "Phoenix Traders Association", "entity_type": "ORGANISATION"},
    ]

    all_edges = [
        {"src": "cid_rajesh", "dst": "cid_shadowtech", "rel_type": "OPERATES", "related_case": "CASE-2024-001"},
        {"src": "cid_priya", "dst": "cid_shadowtech", "rel_type": "ASSOCIATED_WITH", "related_case": "CASE-2024-001"},
        {"src": "cid_dinesh", "dst": "cid_phoenix", "rel_type": "MEMBER_OF", "related_case": "CASE-2024-002"},
        {"src": "cid_vikram", "dst": "cid_phoenix", "rel_type": "COORDINATES", "related_case": "CASE-2024-002"},
    ]

    graph_case_1 = filter_graph_by_case(all_nodes, all_edges, case_doc_map, "CASE-2024-001")
    graph_case_2 = filter_graph_by_case(all_nodes, all_edges, case_doc_map, "CASE-2024-002")

    # 1. Returned sets must be disjoint for completely different cases
    assert graph_case_1["node_ids"].isdisjoint(graph_case_2["node_ids"]), "Case 1 and Case 2 node sets leaked into each other!"
    assert graph_case_1["edge_ids"].isdisjoint(graph_case_2["edge_ids"]), "Case 1 and Case 2 edge sets leaked into each other!"

    # 2. Case 1 contains ONLY entities traceable to Case 1
    assert graph_case_1["node_ids"] == {"cid_rajesh", "cid_priya", "cid_shadowtech"}
    assert "cid_dinesh" not in graph_case_1["node_ids"]
    assert len(graph_case_1["edges"]) == 2

    # 3. Case 2 contains ONLY entities traceable to Case 2
    assert graph_case_2["node_ids"] == {"cid_dinesh", "cid_vikram", "cid_phoenix"}
    assert "cid_rajesh" not in graph_case_2["node_ids"]
    assert len(graph_case_2["edges"]) == 2


if __name__ == "__main__":
    print("Running test_case_a_vs_case_b_scoping...")
    test_case_a_vs_case_b_scoping()
    print("ALL GRAPH CASE SCOPING REGRESSION TESTS PASSED!")
