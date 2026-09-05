"""
NeuroNex — Ingestion Base
Defines the shared InvestigationRecord dataclass and the adapter registry.

All seven source-type adapters inherit from BaseAdapter and expose:
    parse(file_bytes: bytes) -> list[InvestigationRecord]

The `raw_text` field carries free-text for NER; `raw_fields` carries structured rows
for tabular sources (CDR, Financial, Criminal History).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import uuid


# ---------------------------------------------------------------------------
# Shared record shape — every adapter produces this before entering the pipeline
# ---------------------------------------------------------------------------
@dataclass
class InvestigationRecord:
    """
    Common internal representation of one investigative record, regardless of source type.

    Fields
    ------
    record_id       : Unique ID for this record (UUID)
    source_type     : One of the seven canonical source types
    case_ref        : Optional case/FIR reference string from the source
    raw_text        : Concatenated free-text for NER (may be empty for structured sources)
    raw_fields      : Original structured fields for tabular sources; empty dict otherwise
    timestamp       : The event timestamp from the source record
    ingested_at     : When this record was created in memory
    doc_label       : A short human-readable label (e.g. FIR number, txn_id)
    """
    record_id: str
    source_type: str
    case_ref: Optional[str]
    raw_text: str
    raw_fields: dict[str, Any]
    timestamp: Optional[str]
    ingested_at: str
    doc_label: str = ""

    @classmethod
    def create(
        cls,
        source_type: str,
        raw_text: str = "",
        raw_fields: dict | None = None,
        case_ref: str | None = None,
        timestamp: str | None = None,
        doc_label: str = "",
    ) -> "InvestigationRecord":
        return cls(
            record_id=str(uuid.uuid4()),
            source_type=source_type,
            case_ref=case_ref,
            raw_text=raw_text,
            raw_fields=raw_fields or {},
            timestamp=timestamp,
            ingested_at=datetime.now(timezone.utc).isoformat(),
            doc_label=doc_label,
        )


# ---------------------------------------------------------------------------
# Canonical source type identifiers
# ---------------------------------------------------------------------------
SOURCE_TYPES = {
    "fir": "FIR / Police Reports",
    "cdr": "Call Detail Records",
    "financial": "Financial Transactions",
    "surveillance": "Surveillance Reports",
    "social_media": "Social Media Intelligence",
    "criminal_history": "Criminal History Database",
    "intelligence_report": "Intelligence Agency Reports",
}


# ---------------------------------------------------------------------------
# Base adapter — all adapters must implement parse()
# ---------------------------------------------------------------------------
class BaseAdapter:
    source_type: str = "unknown"

    def parse(self, file_bytes: bytes) -> list[InvestigationRecord]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Adapter registry — maps source_type string -> adapter class
# ---------------------------------------------------------------------------
_registry: dict[str, type[BaseAdapter]] = {}


def register_adapter(cls: type[BaseAdapter]) -> type[BaseAdapter]:
    """Class decorator to register an adapter."""
    _registry[cls.source_type] = cls
    return cls


def normalize_source_type(source_type: str) -> str:
    """
    Canonicalize incoming source_type strings, accommodating legacy or external variants:
    - 'financial_transaction', 'financial_transactions', 'finance' -> 'financial'
    - 'call_detail_record', 'call_detail_records', 'cdrs' -> 'cdr'
    - 'surveillance_report', 'surveillance_reports' -> 'surveillance'
    - 'first_information_report', 'firs' -> 'fir'
    """
    if not source_type:
        return "unknown"
    s = source_type.strip().lower()
    if s in ("financial_transaction", "financial_transactions", "finance", "financials"):
        return "financial"
    if s in ("call_detail_record", "call_detail_records", "cdrs"):
        return "cdr"
    if s in ("surveillance_report", "surveillance_reports"):
        return "surveillance"
    if s in ("first_information_report", "firs"):
        return "fir"
    if s in ("intelligence", "intel_report"):
        return "intelligence_report"
    return s


def get_adapter(source_type: str) -> BaseAdapter:
    """Return an instantiated adapter for the given source_type."""
    canonical = normalize_source_type(source_type)
    if canonical not in _registry:
        raise ValueError(
            f"No adapter registered for source_type='{source_type}' (canonical: '{canonical}'). "
            f"Valid types: {list(_registry.keys())}"
        )
    return _registry[canonical]()
