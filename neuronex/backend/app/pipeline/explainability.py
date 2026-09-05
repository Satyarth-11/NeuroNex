"""
NeuroNex — Explainability Module
Converts raw analytics, resolution candidates, and community detection output into
plain-language, evidence-referencing insights.

DESIGN PRINCIPLE: Every insight MUST:
  1. Name the contributing source_type(s)
  2. Reference specific source documents / entities
  3. Explicitly state it is a LEAD, not a confirmed conclusion
  4. Never declare guilt or assign a risk score

Output: list of insight dicts ready for insertion into the SQLite `insights` table.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_central_entity_insight(entity: dict) -> dict:
    """
    Generate an insight for a highly central / influential entity.
    `entity` is a row from analytics.get_centrality().
    """
    name = entity.get("name", "Unknown")
    etype = entity.get("entity_type", "Entity")
    degree = entity.get("degree_centrality", 0.0)
    betweenness = entity.get("betweenness_centrality", 0.0)
    pagerank = entity.get("pagerank", 0.0)
    eigenvector = entity.get("eigenvector_centrality", 0.0)
    source_types = entity.get("source_types", [])
    mention_count = entity.get("mention_count", 1)

    source_str = (
        ", ".join(source_types) if source_types
        else "multiple sources"
    )

    metric_signals = []
    if betweenness >= 0.01:
        metric_signals.append(f"betweenness centrality ({betweenness:.3f}), indicating it may bridge otherwise weakly-connected parts of the network")
    if pagerank >= 0.01:
        metric_signals.append(f"PageRank ({pagerank:.3f}), indicating multiple well-connected entities link to it")
    if degree >= 0.01 and not metric_signals:
        metric_signals.append(f"degree centrality ({degree:.3f}), indicating a high volume of direct links")

    signals_desc = "; ".join(metric_signals) if metric_signals else f"degree ({degree:.3f}) and betweenness ({betweenness:.3f})"

    explanation = (
        f"Entity '{name}' (type: {etype}) appears in {mention_count} records across {source_str}. "
        f"It shows high {signals_desc}. "
        f"This is a network-position signal for analyst review suggesting a potentially influential node "
        f"— not evidence of a leadership role or illegal activity. All AI-generated leads require "
        f"human analyst review before any action is taken."
    )

    combined_score = betweenness + pagerank
    return {
        "insight_type": "central_entity",
        "title": f"Potentially Influential Entity: {name}",
        "explanation": explanation,
        "entity_refs": [entity.get("node_id", "")],
        "source_refs": [],
        "contributing_source_types": source_types,
        "confidence": round(min(max(combined_score * 2.5, 0.6), 0.95), 3),
        "status": "proposed",
    }


def generate_community_insight(community: dict) -> dict:
    """Generate an insight for a detected community."""
    cid = community.get("community_id", 0)
    count = community.get("member_count", 0)
    density = community.get("internal_edge_density", 0.0)
    source_types = community.get("source_types", [])
    members = community.get("members", [])

    member_names = [m.get("name", "") for m in members[:5]]
    name_str = ", ".join(filter(None, member_names))
    if len(members) > 5:
        name_str += f" and {len(members) - 5} others"

    source_str = ", ".join(source_types) if source_types else "multiple sources"

    explanation = (
        f"Community {cid + 1} consists of {count} entities including {name_str}. "
        f"These entities show a high internal connection density of {density:.2f}, "
        f"suggesting frequent co-occurrence across {source_str}. "
        f"The grouping was detected by the Louvain community detection algorithm. "
        f"This is a structural pattern in the data — it does NOT imply that these "
        f"entities are members of a criminal organisation. Human analyst review is "
        f"mandatory before any investigative action."
    )

    entity_refs = [m.get("node_id", "") for m in members]

    return {
        "insight_type": "community",
        "title": f"Detected Network Cluster — Community {cid + 1} ({count} entities)",
        "explanation": explanation,
        "entity_refs": entity_refs,
        "source_refs": [],
        "contributing_source_types": source_types,
        "confidence": round(min(density * 0.9, 0.9), 3),
        "status": "proposed",
    }


def generate_duplicate_insight(candidate: dict, entity_a_name: str, entity_b_name: str) -> dict:
    """Generate an insight for a pending entity resolution candidate."""
    score = candidate.get("similarity_score", 0.0)
    reason = candidate.get("match_reason", "")
    etype = candidate.get("entity_type", "Entity")

    explanation = (
        f"Two {etype} entities — '{entity_a_name}' and '{entity_b_name}' — "
        f"have a similarity score of {score:.2f} ({reason}). "
        f"They may refer to the same real-world entity. "
        f"Merging them would consolidate their connections in the knowledge graph, "
        f"potentially revealing additional links. "
        f"This is a possible duplicate flagged for analyst review — "
        f"no automatic merge action has been taken."
    )

    return {
        "insight_type": "possible_duplicate",
        "title": f"Possible Duplicate: '{entity_a_name}' ↔ '{entity_b_name}'",
        "explanation": explanation,
        "entity_refs": [],
        "source_refs": [],
        "contributing_source_types": [],
        "confidence": round(score, 3),
        "status": "proposed",
    }


def generate_pattern_insights(patterns: list[dict]) -> list[dict]:
    """
    Convert detected anomaly/suspicious patterns into insight dicts.
    """
    insights = []
    for p in patterns:
        source_doc_ids = p.get("source_doc_ids", [])
        evidence = p.get("evidence", {})
        source_types = evidence.get("source_types", [])

        ins = {
            "insight_type": "suspicious_pattern",
            "title": p.get("title", "Detected Anomaly Pattern"),
            "explanation": p.get("description", ""),
            "entity_refs": p.get("entity_refs", []),
            "source_refs": [f"doc_{d}" for d in source_doc_ids] if source_doc_ids else [],
            "contributing_source_types": source_types,
            "confidence": round(p.get("confidence", 0.85), 3),
            "status": "proposed",
        }
        if "sample_size" in p:
            ins["sample_size"] = p["sample_size"]
        if "threshold_used" in p:
            ins["threshold_used"] = p["threshold_used"]
        if "comparison_basis" in p:
            ins["comparison_basis"] = p["comparison_basis"]
        insights.append(ins)
    return insights


def generate_edge_explanation(
    rel_type: str,
    src_name: str,
    dst_name: str,
    props: dict | None = None,
) -> str:
    """
    Generate plain-language explanation for a relationship edge.
    Adheres strictly to decision support language (never implies guilt).
    """
    props = props or {}
    weight = props.get("weight") or props.get("amount") or 0
    timestamp = props.get("timestamp") or "the recorded period"

    if rel_type == "TRANSFERRED_TO":
        return (
            f"Account {src_name} transferred ₹{int(weight):,} to account {dst_name} on {timestamp}. "
            f"Financial relationship identified — requires analyst review."
        )
    return (
        f"Entity {src_name} has {rel_type} connection to {dst_name}. "
        f"Network association identified — requires analyst review."
    )


def generate_all_insights(
    top_entities: list[dict],
    communities: list[dict],
    pending_candidates: list[dict] | None = None,
    patterns: list[dict] | None = None,
    key_influencers: list[dict] | None = None,
) -> list[dict]:
    """
    Generate all insights from current analytics state.
    Returns a list of insight dicts for bulk insertion.
    """
    insights = []

    # Central entity insights for top entities
    for ent in top_entities[:5]:  # top 5 by betweenness/PageRank
        if (ent.get("betweenness_centrality", 0) + ent.get("pagerank", 0)) > 0.01:
            insights.append(generate_central_entity_insight(ent))

    # Community insights
    for community in communities:
        if community.get("member_count", 0) >= 2:
            insights.append(generate_community_insight(community))

    # Duplicate resolution insights
    for cand in (pending_candidates or [])[:10]:
        insights.append(generate_duplicate_insight(
            cand,
            cand.get("entity_a_name", "Entity A"),
            cand.get("entity_b_name", "Entity B"),
        ))

    # Suspicious pattern insights
    if patterns:
        insights.extend(generate_pattern_insights(patterns))

    # Key influential entity insights (Option a from Fix 4)
    if key_influencers:
        for inf in key_influencers:
            insights.append(generate_key_influencer_insight(inf))

    logger.info("Explainability: generated %d insights", len(insights))
    return insights


def generate_key_influencer_insight(influencer: dict) -> dict:
    """Generate reviewable insight for a key influencer in the PERSON domain."""
    name = influencer.get("name", "Unknown")
    node_id = influencer.get("node_id", "")
    explanation = influencer.get("explanation") or generate_key_influencer_explanation(influencer)
    cases = influencer.get("related_cases", [])
    source_types = influencer.get("source_types", [])

    return {
        "insight_type": "key_influencer",
        "title": f"Key Influential Entity: {name} (PERSON)",
        "explanation": explanation,
        "entity_refs": [node_id] if node_id else [],
        "source_refs": [f"case_{c}" for c in cases] if cases else [],
        "contributing_source_types": source_types,
        "confidence": round(min(0.95, 0.75 + float(influencer.get("pagerank", 0.0))), 3),
        "status": "proposed",
    }


def generate_key_influencer_explanation(influencer: dict) -> str:
    """
    Generate plain-language explanation for key influencer detection.
    Strictly follows decision support wording (never 'leader' or 'kingpin').
    """
    name = influencer.get("name", "Unknown")
    betweenness = influencer.get("betweenness_centrality", 0.0)
    pagerank = influencer.get("pagerank", 0.0)
    degree = influencer.get("degree_centrality", 0.0)

    signals = []
    if betweenness > 0.02:
        signals.append(f"high betweenness centrality ({betweenness:.4f}), suggesting it may bridge otherwise weakly-connected parts of the network")
    if pagerank > 0.02:
        signals.append(f"high PageRank ({pagerank:.4f}), indicating prominent incoming connectivity from central nodes")
    if degree > 0.02 and not signals:
        signals.append(f"high degree centrality ({degree:.4f}), indicating extensive direct connections")
    if not signals:
        signals.append(f"betweenness centrality ({betweenness:.4f}) and PageRank ({pagerank:.4f})")

    reasons_str = "; ".join(signals)
    return (
        f"Entity '{name}' shows {reasons_str}. "
        f"Identifies a potentially influential network entity within the PERSON domain "
        f"— investigative lead, not a finding; requires analyst review."
    )
