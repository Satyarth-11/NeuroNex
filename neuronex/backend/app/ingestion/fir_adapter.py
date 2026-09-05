"""
NeuroNex — FIR / Police Reports Adapter (SYNTHETIC DATA ONLY)
Parses CSV files with columns:
    fir_no, police_station, date, sections_of_law, complainant_name,
    accused_names (semicolon-separated), narrative_text
NER will run richest on narrative_text (persons, locations, vehicles).
"""
from __future__ import annotations
import csv
import io
from app.ingestion.base import BaseAdapter, InvestigationRecord, register_adapter


@register_adapter
class FIRAdapter(BaseAdapter):
    source_type = "fir"

    def parse(self, file_bytes: bytes) -> list[InvestigationRecord]:
        records: list[InvestigationRecord] = []
        text = file_bytes.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))

        for row in reader:
            fir_no = row.get("fir_no", "").strip()
            narrative = row.get("narrative_text", "").strip()

            # Build rich free-text for NER: combine structured fields + narrative
            rich_text = (
                f"FIR {fir_no} registered at {row.get('police_station', '')}. "
                f"Complainant: {row.get('complainant_name', '')}. "
                f"Accused: {row.get('accused_names', '')}. "
                f"{narrative}"
            )

            records.append(
                InvestigationRecord.create(
                    source_type=self.source_type,
                    raw_text=rich_text,
                    raw_fields=dict(row),
                    case_ref=fir_no,
                    timestamp=row.get("date"),
                    doc_label=f"FIR {fir_no}",
                )
            )
        return records
