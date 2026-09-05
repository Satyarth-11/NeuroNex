"""
NeuroNex — Temporal Intelligence Pipeline
Extracts multi-source timestamped events across FIR, CDR, Financial, Surveillance,
and Social Media records, orders them chronologically, and detects temporal correlations.
ALL DATA IS SYNTHETIC. All outputs use neutral investigative terminology.
"""
from __future__ import annotations

import csv
import io
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

SYNTHETIC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic")
)
if not os.path.exists(SYNTHETIC_DIR):
    SYNTHETIC_DIR = "/app/data/synthetic"


def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    dt_str = dt_str.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def get_timeline_for_case(
    case_code: str,
    window_hours: int = 48,
    entity_filter: Optional[str] = None,
) -> dict:
    """
    Extracts chronological timeline events for a given case_code across all source files,
    and identifies temporal correlations (e.g., communication within X hours of a financial transfer).
    """
    events = []

    # 1. FIR reports
    fir_path = os.path.join(SYNTHETIC_DIR, "fir_reports.csv")
    if os.path.exists(fir_path):
        with open(fir_path, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                if row.get("case_ref") == case_code:
                    dt = _parse_datetime(row.get("date"))
                    accused = [a.strip() for a in row.get("accused_names", "").split(";") if a.strip()]
                    comp = row.get("complainant_name", "").strip()
                    entities = [comp] + accused if comp else accused
                    events.append({
                        "event_id": f"fir_{row.get('fir_no', len(events))}",
                        "source_type": "fir",
                        "timestamp": dt.isoformat() if dt else row.get("date"),
                        "datetime_obj": dt,
                        "title": f"FIR Registered: {row.get('fir_no')}",
                        "description": f"FIR registered at {row.get('police_station')}. Complainant: {comp}. Sections: {row.get('sections_of_law')}.",
                        "entities": entities,
                        "raw_fields": {
                            "police_station": row.get("police_station"),
                            "sections": row.get("sections_of_law"),
                        },
                    })

    # 2. CDR records
    cdr_path = os.path.join(SYNTHETIC_DIR, "cdr_records.csv")
    if os.path.exists(cdr_path):
        with open(cdr_path, encoding="utf-8", errors="replace") as f:
            for idx, row in enumerate(csv.DictReader(f)):
                if row.get("case_ref") == case_code:
                    dt = _parse_datetime(row.get("call_datetime"))
                    caller = row.get("caller_number", "").strip()
                    callee = row.get("callee_number", "").strip()
                    dur = row.get("duration_sec", "0")
                    ctype = row.get("call_type", "voice")
                    events.append({
                        "event_id": f"cdr_{idx}",
                        "source_type": "cdr",
                        "timestamp": dt.isoformat() if dt else row.get("call_datetime"),
                        "datetime_obj": dt,
                        "title": f"Communication: {caller} → {callee}",
                        "description": f"{ctype.upper()} call ({dur}s) via tower at {row.get('cell_tower_location', 'unknown')}.",
                        "entities": [caller, callee],
                        "raw_fields": {
                            "caller": caller,
                            "callee": callee,
                            "duration_sec": dur,
                            "call_type": ctype,
                            "tower": row.get("cell_tower_location"),
                        },
                    })

    # 3. Financial transactions
    fin_path = os.path.join(SYNTHETIC_DIR, "financial_transactions.csv")
    if os.path.exists(fin_path):
        with open(fin_path, encoding="utf-8", errors="replace") as f:
            for idx, row in enumerate(csv.DictReader(f)):
                if row.get("case_ref") == case_code:
                    dt = _parse_datetime(row.get("txn_datetime"))
                    sender = row.get("sender_account", "").strip()
                    recv = row.get("receiver_account", "").strip()
                    amt = row.get("amount", "0")
                    mode = row.get("txn_mode", "NEFT")
                    events.append({
                        "event_id": f"fin_{row.get('txn_id', idx)}",
                        "source_type": "financial",
                        "timestamp": dt.isoformat() if dt else row.get("txn_datetime"),
                        "datetime_obj": dt,
                        "title": f"Fund Transfer: Rs {float(amt):,.2f}",
                        "description": f"{sender} transferred Rs {float(amt):,.2f} to {recv} via {mode}. Remarks: {row.get('remarks', 'N/A')}",
                        "entities": [sender, recv],
                        "raw_fields": {
                            "amount": amt,
                            "mode": mode,
                            "remarks": row.get("remarks"),
                        },
                    })

    # 4. Surveillance reports
    surv_path = os.path.join(SYNTHETIC_DIR, "surveillance_reports.txt")
    if os.path.exists(surv_path):
        with open(surv_path, encoding="utf-8", errors="replace") as f:
            raw_text = f.read()
        blocks = re.split(r"-{3,}\s*REPORT", raw_text, flags=re.IGNORECASE)
        for idx, block in enumerate(blocks):
            if not block.strip():
                continue
            if f"CASE_REF: {case_code}" in block or f"CASE_REF:{case_code}" in block or case_code in block:
                date_m = re.search(r"DATE:\s*([^\n\r]+)", block, re.IGNORECASE)
                loc_m = re.search(r"LOCATION:\s*([^\n\r]+)", block, re.IGNORECASE)
                team_m = re.search(r"TEAM:\s*([^\n\r]+)", block, re.IGNORECASE)
                id_m = re.search(r"REPORT_ID:\s*([^\n\r]+)", block, re.IGNORECASE)
                dt = _parse_datetime(date_m.group(1).strip()) if date_m else None
                events.append({
                    "event_id": f"surv_{id_m.group(1).strip() if id_m else idx}",
                    "source_type": "surveillance",
                    "timestamp": dt.isoformat() if dt else (date_m.group(1).strip() if date_m else None),
                    "datetime_obj": dt,
                    "title": f"Surveillance Log: {loc_m.group(1).strip() if loc_m else 'Field Sighting'}",
                    "description": block.strip()[:250] + ("..." if len(block.strip()) > 250 else ""),
                    "entities": [],
                    "raw_fields": {
                        "team": team_m.group(1).strip() if team_m else None,
                        "location": loc_m.group(1).strip() if loc_m else None,
                    },
                })

    # 5. Social Media posts
    sm_path = os.path.join(SYNTHETIC_DIR, "social_media_posts.csv")
    if os.path.exists(sm_path):
        with open(sm_path, encoding="utf-8", errors="replace") as f:
            for idx, row in enumerate(csv.DictReader(f)):
                if row.get("case_ref") == case_code:
                    dt = _parse_datetime(row.get("timestamp"))
                    handle = row.get("handle", "").strip()
                    post_text = row.get("post_text", "").strip()
                    events.append({
                        "event_id": f"sm_{row.get('post_id', idx)}",
                        "source_type": "social_media",
                        "timestamp": dt.isoformat() if dt else row.get("timestamp"),
                        "datetime_obj": dt,
                        "title": f"Social Media Mention ({row.get('platform', 'Social')})",
                        "description": f"@{handle}: {post_text[:180]}",
                        "entities": [handle],
                        "raw_fields": {
                            "platform": row.get("platform"),
                            "handle": handle,
                        },
                    })

    # Filter by entity if provided
    if entity_filter:
        norm_ent = entity_filter.lower().strip()
        events = [
            e for e in events
            if any(norm_ent in str(ent).lower() for ent in e.get("entities", []))
            or norm_ent in e.get("description", "").lower()
        ]

    # Sort events chronologically (events without valid datetime go to end)
    events.sort(key=lambda x: x["datetime_obj"] or datetime.max)

    # Detect multi-source temporal correlations
    correlations = []
    window = timedelta(hours=window_hours)
    dated_events = [e for e in events if e["datetime_obj"] is not None]

    for i in range(len(dated_events)):
        for j in range(i + 1, len(dated_events)):
            e1 = dated_events[i]
            e2 = dated_events[j]
            delta = e2["datetime_obj"] - e1["datetime_obj"]
            if delta > window:
                break
            # Check for cross-source correlation (different source modalities)
            if e1["source_type"] != e2["source_type"]:
                hours_diff = round(delta.total_seconds() / 3600.0, 1)
                corr_type = f"{e1['source_type'].upper()} → {e2['source_type'].upper()}"
                desc = (
                    f"{e1['source_type'].title()} event '{e1['title']}' was followed within "
                    f"{hours_diff}h by {e2['source_type'].title()} event '{e2['title']}'."
                )
                correlations.append({
                    "correlation_id": f"corr_{e1['event_id']}_{e2['event_id']}",
                    "event_a_id": e1["event_id"],
                    "event_b_id": e2["event_id"],
                    "event_a_type": e1["source_type"],
                    "event_b_type": e2["source_type"],
                    "time_delta_hours": hours_diff,
                    "correlation_label": "Temporal Correlation",
                    "explanation": desc,
                    "neutral_disclaimer": "Temporal correlation reflects proximity in synthetic records; it does not constitute proof of coordinated activity.",
                })

    # Remove datetime_obj from output JSON
    serializable_events = []
    for e in events:
        item = dict(e)
        item.pop("datetime_obj", None)
        serializable_events.append(item)

    return {
        "case_code": case_code,
        "total_events": len(serializable_events),
        "events": serializable_events,
        "correlations": correlations,
        "window_hours": window_hours,
        "sources_represented": list({e["source_type"] for e in serializable_events}),
        "notes": (
            f"Chronological timeline of {len(serializable_events)} events across "
            f"{len({e['source_type'] for e in serializable_events})} synthetic source types. "
            f"Identified {len(correlations)} temporal correlations within a {window_hours}-hour window."
        ),
    }
