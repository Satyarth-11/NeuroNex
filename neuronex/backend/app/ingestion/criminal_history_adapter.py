"""
NeuroNex — Criminal History Database Adapter (SYNTHETIC DATA ONLY)
Parses CSV with columns:
    person_id, name, aliases (semicolon-separated), known_associates (semicolon-separated),
    prior_cases (semicolon-separated), last_known_address
Note: criminal_history_flag is INFORMATIONAL ONLY — never used for automated scoring.
"""
from __future__ import annotations
import csv
import io
from app.ingestion.base import BaseAdapter, InvestigationRecord, register_adapter


@register_adapter
class CriminalHistoryAdapter(BaseAdapter):
    source_type = "criminal_history"

    def parse(self, file_bytes: bytes) -> list[InvestigationRecord]:
        records: list[InvestigationRecord] = []
        text = file_bytes.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))

        for row in reader:
            person_id = row.get("person_id", "").strip()
            name = row.get("name", "").strip()
            aliases = row.get("aliases", "").strip()
            associates = row.get("known_associates", "").strip()
            prior_cases = row.get("prior_cases", "").strip()
            address = row.get("last_known_address", "").strip()

            # Free-text summary for NER (names, locations from address)
            raw_text = (
                f"Criminal history record for {name} (ID: {person_id}). "
                f"Also known as: {aliases}. "
                f"Known associates: {associates}. "
                f"Prior case references: {prior_cases}. "
                f"Last known address: {address}."
            )

            records.append(
                InvestigationRecord.create(
                    source_type=self.source_type,
                    raw_text=raw_text,
                    raw_fields=dict(row),
                    case_ref=None,
                    timestamp=None,
                    doc_label=f"CrimHistory {person_id} {name}",
                )
            )
        return records
