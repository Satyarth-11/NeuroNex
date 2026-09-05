"""
NeuroNex — Call Detail Records (CDR) Adapter (SYNTHETIC DATA ONLY)
Parses CSV with columns:
    caller_number, callee_number, call_datetime, duration_sec,
    cell_tower_location, call_type (voice/sms)
Structured ingestion — no free-text NER needed; phone numbers become graph nodes directly.
"""
from __future__ import annotations
import csv
import io
from app.ingestion.base import BaseAdapter, InvestigationRecord, register_adapter


@register_adapter
class CDRAdapter(BaseAdapter):
    source_type = "cdr"

    def parse(self, file_bytes: bytes) -> list[InvestigationRecord]:
        records: list[InvestigationRecord] = []
        text = file_bytes.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))

        for row in reader:
            caller = row.get("caller_number", "").strip()
            callee = row.get("callee_number", "").strip()

            # Minimal free-text — phone numbers are extracted structurally, not via NER
            raw_text = (
                f"Call from {caller} to {callee} "
                f"at {row.get('cell_tower_location', 'unknown location')}."
            )

            records.append(
                InvestigationRecord.create(
                    source_type=self.source_type,
                    raw_text=raw_text,
                    raw_fields=dict(row),
                    timestamp=row.get("call_datetime"),
                    doc_label=f"CDR {caller}→{callee}",
                )
            )
        return records
