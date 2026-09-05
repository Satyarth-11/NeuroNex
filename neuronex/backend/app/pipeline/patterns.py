"""
NeuroNex — Suspicious & Anomaly Pattern Detection
============================================================
Explainable, rule-based pattern detectors operating across graph topology,
source documents, transaction distributions, and communications.

CRITICAL POLICY:
- Decision-support only — surfaces investigative leads for human analysts.
- Every pattern description ends with either:
  "— Potential anomaly, requires analyst review."
  OR
  "— Investigative lead, not a finding."
- Never uses "criminal", "guilty", "suspect is", or "gang".
"""
from __future__ import annotations
import logging
import math
from typing import Any
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_graph import run_query
from app.models_sql import Document, Case
from app.pipeline.communities import get_communities

logger = logging.getLogger(__name__)


async def detect_cross_case_entities(db: AsyncSession) -> list[dict]:
    """
    1. Cross-Case Entity Overlap Detector
    Identifies canonical entity nodes whose source document references span
    more than one distinct investigation Case.
    """
    patterns = []
    # Query Neo4j nodes that have more than 1 source_doc_id
    cypher = """
    MATCH (n)
    WHERE size(n.source_doc_ids) > 1 AND n.entity_type IN ['Person', 'Phone', 'Vehicle', 'Account']
    RETURN n.id AS node_id, n.name AS name, n.entity_type AS entity_type,
           n.source_doc_ids AS source_doc_ids, n.source_types AS source_types
    """
    nodes = await run_query(cypher)
    if not nodes:
        return []

    # Map all document IDs to their case_id and case_code
    doc_res = await db.execute(select(Document.id, Document.case_id))
    doc_to_case_id = dict(doc_res.all())

    case_res = await db.execute(select(Case.id, Case.case_code))
    case_id_to_code = dict(case_res.all())

    for node in nodes:
        doc_ids = [int(d) for d in node.get("source_doc_ids", []) if str(d).isdigit()]
        case_pairs = []
        seen_cases = set()

        for d_id in doc_ids:
            c_id = doc_to_case_id.get(d_id)
            if c_id and c_id in case_id_to_code:
                c_code = case_id_to_code[c_id]
                case_pairs.append({"case_code": c_code, "document_id": d_id})
                seen_cases.add(c_code)

        if len(seen_cases) > 1:
            name = node.get("name", "Unknown")
            etype = node.get("entity_type", "Entity")
            cases_str = ", ".join(sorted(seen_cases))
            patterns.append({
                "pattern_type": "cross_case_entity",
                "title": f"Cross-Case Entity Overlap: {name} ({etype})",
                "description": (
                    f"Entity '{name}' ({etype}) appears across {len(seen_cases)} distinct investigation "
                    f"cases ({cases_str}) spanning {len(doc_ids)} separate documents. This multi-case "
                    f"presence suggests a shared point of contact across independent case records "
                    f"— Investigative lead, not a finding."
                ),
                "evidence": {
                    "entity_id": node.get("node_id"),
                    "cases": list(seen_cases),
                    "case_document_pairs": case_pairs,
                    "source_types": node.get("source_types", []),
                },
                "entity_refs": [node.get("node_id", "")],
                "source_doc_ids": doc_ids,
                "confidence": 0.88,
            })

    return patterns


async def detect_unusual_transaction_amounts(db: AsyncSession) -> list[dict]:
    """
    2. Unusual Financial Transaction Detector
    Finds account nodes in the graph, extracts associated transaction amounts,
    and flags transactions exceeding 2.5 standard deviations from the account mean
    (or > 3x dataset median if fewer than 5 transactions).
    """
    patterns = []
    # Pull financial documents from SQLite (canonical: 'financial')
    doc_res = await db.execute(select(Document).where(Document.source_type.in_(["financial", "financial_transaction"])))
    docs = doc_res.scalars().all()
    if not docs:
        return []

    account_txns = defaultdict(list)
    all_amounts = []

    for doc in docs:
        # Parse CSV lines
        lines = (doc.raw_text or "").strip().splitlines()
        if len(lines) < 2:
            continue
        header = [h.strip() for h in lines[0].split(",")]
        try:
            amt_idx = header.index("amount")
            sender_idx = header.index("sender_account") if "sender_account" in header else -1
            rcv_idx = header.index("receiver_account") if "receiver_account" in header else -1
            txn_id_idx = header.index("txn_id") if "txn_id" in header else -1
        except ValueError:
            continue

        for line in lines[1:]:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) > amt_idx:
                try:
                    amount = float(parts[amt_idx])
                    all_amounts.append(amount)
                    txn_id = parts[txn_id_idx] if txn_id_idx >= 0 and len(parts) > txn_id_idx else "TXN"
                    record_info = {
                        "txn_id": txn_id,
                        "amount": amount,
                        "document_id": doc.id,
                        "sender": parts[sender_idx] if sender_idx >= 0 and len(parts) > sender_idx else "",
                        "receiver": parts[rcv_idx] if rcv_idx >= 0 and len(parts) > rcv_idx else "",
                    }
                    if sender_idx >= 0 and len(parts) > sender_idx and parts[sender_idx]:
                        account_txns[parts[sender_idx]].append(record_info)
                    if rcv_idx >= 0 and len(parts) > rcv_idx and parts[rcv_idx]:
                        account_txns[parts[rcv_idx]].append(record_info)
                except ValueError:
                    continue

    if not all_amounts:
        return []

    sorted_all = sorted(all_amounts)
    median_amount = sorted_all[len(sorted_all) // 2]

    # Evaluate per account
    for acc, txns in account_txns.items():
        amounts = [t["amount"] for t in txns]
        n = len(amounts)
        mean_amt = sum(amounts) / n

        if n >= 5:
            variance = sum((x - mean_amt) ** 2 for x in amounts) / n
            std_dev = math.sqrt(variance)
            threshold = mean_amt + (2.5 * std_dev)
            method = "2.5 standard deviations above account mean"
        else:
            threshold = 3.0 * median_amount
            method = "3x dataset-wide median"

        for t in txns:
            if t["amount"] > threshold:
                patterns.append({
                    "pattern_type": "unusual_transaction_amount",
                    "title": f"Unusual Transaction Value: Account {acc} (₹{t['amount']:,.0f})",
                    "description": (
                        f"Transaction {t['txn_id']} involving Account '{acc}' has an amount of ₹{t['amount']:,.0f}, "
                        f"which exceeds the anomaly threshold of ₹{threshold:,.0f} calculated via {method}. "
                        f"This represents a high-value deviation from standard baseline activity "
                        f"— Potential anomaly, requires analyst review."
                    ),
                    "evidence": {
                        "account": acc,
                        "transaction_id": t["txn_id"],
                        "amount": t["amount"],
                        "threshold": round(threshold, 2),
                        "baseline_method": method,
                        "account_mean": round(mean_amt, 2),
                    },
                    "entity_refs": [acc],
                    "source_doc_ids": [t["document_id"]],
                    "confidence": 0.82,
                })

    return patterns


async def detect_high_frequency_communication(db: AsyncSession) -> list[dict]:
    """
    3. High-Frequency Communication Detector
    Flags phone pairs connected via CONTACTED relationships whose call weight
    is in the top 5% of all communication edge weights.
    """
    patterns = []
    cypher = """
    MATCH (a:Phone)-[r:CONTACTED]->(b:Phone)
    RETURN a.id AS src_id, a.name AS caller, b.id AS dst_id, b.name AS callee,
           r.weight AS weight, r.source_doc_ids AS source_doc_ids, r.source_types AS source_types
    """
    edges = await run_query(cypher)
    if not edges:
        return []

    weights = [int(e.get("weight", 1) or 1) for e in edges]
    if not weights:
        return []

    n = len(weights)
    if n < 10:
        # Too few observations for a meaningful percentile — use an honest minimum-
        # threshold approach instead: flag only pairs with weight >= 3x the dataset
        # mean AND weight >= 5 (an absolute floor so single high-weight edges in a
        # near-empty dataset aren't over-flagged).
        mean_w = sum(weights) / n if n else 0
        threshold = max(5, round(mean_w * 3))
        basis = f"absolute-threshold (dataset too small for percentile analysis, n={n})"
    else:
        weights_sorted = sorted(weights)
        cutoff_idx = max(0, int(n * 0.95) - 1)
        threshold = weights_sorted[cutoff_idx]
        basis = f"95th-percentile (n={n} communication edges)"

    for edge in edges:
        w = int(edge.get("weight", 1) or 1)
        if w >= threshold and w > 1:
            caller = edge.get("caller", "Phone A")
            callee = edge.get("callee", "Phone B")
            doc_ids = [int(d) for d in edge.get("source_doc_ids", []) if str(d).isdigit()]
            desc = (
                f"Communication frequency ({w} contacts) is unusually high relative to the "
                f"{n} communication records available in this dataset ({basis}). "
                f"Potential anomaly, requires analyst review."
            )
            patterns.append({
                "pattern_type": "high_frequency_communication",
                "title": f"High Communication Volume: {caller} ↔ {callee}",
                "description": desc,
                "evidence": {
                    "caller": caller,
                    "callee": callee,
                    "weight": w,
                    "threshold": threshold,
                    "sample_size": n,
                    "comparison_basis": basis,
                    "source_doc_ids": doc_ids,
                },
                "entity_refs": [edge.get("src_id", ""), edge.get("dst_id", "")],
                "source_doc_ids": doc_ids,
                "sample_size": n,
                "threshold_used": float(threshold),
                "comparison_basis": basis,
                "confidence": 0.85,
            })

    return patterns


async def detect_multi_source_convergence(db: AsyncSession) -> list[dict]:
    """
    4. Multi-Source Convergence Detector
    Identifies entity nodes corroborated by 4 or more distinct source types
    (e.g., FIR + CDR + Financial + Surveillance + Social Media).
    """
    patterns = []
    cypher = """
    MATCH (n)
    WHERE size(n.source_types) >= 4
    RETURN n.id AS node_id, n.name AS name, n.entity_type AS entity_type,
           n.source_types AS source_types, n.source_doc_ids AS source_doc_ids,
           n.mention_count AS mention_count
    """
    nodes = await run_query(cypher)
    if not nodes:
        return []

    for node in nodes:
        stypes = node.get("source_types") or []
        doc_ids = [int(d) for d in node.get("source_doc_ids", []) if str(d).isdigit()]
        name = node.get("name", "Unknown")
        etype = node.get("entity_type", "Entity")
        st_str = ", ".join(stypes)
        patterns.append({
            "pattern_type": "multi_source_convergence",
            "title": f"Multi-Source Evidence Convergence: {name} ({len(stypes)} sources)",
            "description": (
                f"Entity '{name}' ({etype}) is independently referenced across {len(stypes)} distinct source types "
                f"({st_str}) across {len(doc_ids)} documents. Such cross-modal convergence highlights an entity "
                f"with substantial multi-stream observational footprint "
                f"— Potential anomaly, requires analyst review."
            ),
            "evidence": {
                "entity_id": node.get("node_id"),
                "source_types": stypes,
                "source_count": len(stypes),
                "mention_count": node.get("mention_count", 1),
                "source_doc_ids": doc_ids,
            },
            "entity_refs": [node.get("node_id", "")],
            "source_doc_ids": doc_ids,
            "confidence": 0.90,
        })

    return patterns


async def detect_dense_local_cluster(db: AsyncSession) -> list[dict]:
    """
    5. Dense Local Cluster Detector
    Identifies communities detected via Louvain that exhibit internal edge density > 0.6
    and size >= 4.
    """
    patterns = []
    communities = await get_communities()

    for comm in communities:
        density = comm.get("internal_edge_density", 0.0)
        size = comm.get("member_count", 0)
        cid = comm.get("community_id", 0)

        if density > 0.6 and size >= 4:
            members = comm.get("members", [])
            member_names = [m.get("name", "") for m in members[:5] if m.get("name")]
            names_str = ", ".join(member_names)
            if len(members) > 5:
                names_str += f" and {len(members) - 5} others"

            stypes = comm.get("source_types", [])
            node_ids = [m.get("node_id", "") for m in members]

            patterns.append({
                "pattern_type": "dense_local_cluster",
                "title": f"Dense Sub-Network Cluster: Community {cid + 1} (Density {density:.2f})",
                "description": (
                    f"Network community {cid + 1} exhibits high internal edge density of {density:.2f} "
                    f"across {size} closely interconnected entities including {names_str}. "
                    f"High cohesion indicates an active, tightly-knit subgroup with strong reciprocal relationships "
                    f"— Investigative lead, not a finding."
                ),
                "evidence": {
                    "community_id": cid,
                    "member_count": size,
                    "internal_edge_density": round(density, 3),
                    "source_types": stypes,
                    "members": member_names,
                },
                "entity_refs": node_ids,
                "source_doc_ids": [],
                "confidence": round(min(density, 0.95), 3),
            })

    return patterns


async def detect_all_patterns(db: AsyncSession) -> list[dict]:
    """Execute all 5 pattern detectors and aggregate results."""
    all_patterns = []

    try:
        cross_case = await detect_cross_case_entities(db)
        all_patterns.extend(cross_case)
    except Exception as e:
        logger.warning("Error in detect_cross_case_entities: %s", e)

    try:
        financial_anomalies = await detect_unusual_transaction_amounts(db)
        all_patterns.extend(financial_anomalies)
    except Exception as e:
        logger.warning("Error in detect_unusual_transaction_amounts: %s", e)

    try:
        high_freq = await detect_high_frequency_communication(db)
        all_patterns.extend(high_freq)
    except Exception as e:
        logger.warning("Error in detect_high_frequency_communication: %s", e)

    try:
        multi_source = await detect_multi_source_convergence(db)
        all_patterns.extend(multi_source)
    except Exception as e:
        logger.warning("Error in detect_multi_source_convergence: %s", e)

    try:
        dense_clusters = await detect_dense_local_cluster(db)
        all_patterns.extend(dense_clusters)
    except Exception as e:
        logger.warning("Error in detect_dense_local_cluster: %s", e)

    logger.info("Pattern Detection: discovered %d patterns of interest", len(all_patterns))
    return all_patterns
