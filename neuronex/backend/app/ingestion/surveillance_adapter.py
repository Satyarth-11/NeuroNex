"""
NeuroNex — Surveillance Reports Adapter (SYNTHETIC DATA ONLY)
Parses a plain-text file where each report is delimited by a line starting with
'--- REPORT' or separated by double newlines.
Fields embedded in the text:
    REPORT_ID:, TEAM:, LOCATION:, DATE:, followed by free-form narrative.
NER extracts Person, Location, Vehicle, Organisation from the full narrative.
"""
from __future__ import annotations
import re
from app.ingestion.base import BaseAdapter, InvestigationRecord, register_adapter

# Delimiter pattern for report blocks
_REPORT_SPLIT = re.compile(r"-{3,}\s*REPORT", re.IGNORECASE)
_FIELD = re.compile(r"^(REPORT_ID|TEAM|LOCATION|DATE|CASE_REF):\s*(.+)$", re.IGNORECASE | re.MULTILINE)


@register_adapter
class SurveillanceAdapter(BaseAdapter):
    source_type = "surveillance"

    def parse(self, file_bytes: bytes) -> list[InvestigationRecord]:
        records: list[InvestigationRecord] = []
        text = file_bytes.decode("utf-8", errors="replace")

        # Split by delimiter; if no delimiter, treat each paragraph as a report
        blocks = _REPORT_SPLIT.split(text)
        if len(blocks) == 1:
            blocks = [b.strip() for b in text.split("\n\n") if b.strip()]

        for block in blocks:
            if not block.strip():
                continue

            fields: dict[str, str] = {}
            for m in _FIELD.finditer(block):
                fields[m.group(1).upper()] = m.group(2).strip()

            report_id = fields.get("REPORT_ID", f"surv_{len(records)+1}")
            case_ref = fields.get("CASE_REF") or report_id

            records.append(
                InvestigationRecord.create(
                    source_type=self.source_type,
                    raw_text=block.strip(),
                    raw_fields=fields,
                    case_ref=case_ref,
                    timestamp=fields.get("DATE"),
                    doc_label=f"Surveillance {report_id}",
                )
            )
        return records
