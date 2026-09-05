"""
NeuroNex — Intelligence Agency Reports Adapter (SYNTHETIC DATA ONLY)
Parses a plain-text file with a distinct source_type tag for traceability.
Each report block format:
    --- INTEL REPORT <report_id> ---
    CLASSIFICATION: RESTRICTED - DEMO  (synthetic classification marking)
    DATE: <date>
    SUMMARY: <free text, possibly with [REDACTED] placeholders>
NER runs on the full block including summary.
"""
from __future__ import annotations
import re
from app.ingestion.base import BaseAdapter, InvestigationRecord, register_adapter

_REPORT_SPLIT = re.compile(r"-{3,}\s*INTEL REPORT", re.IGNORECASE)
_FIELD = re.compile(r"^(REPORT_ID|CLASSIFICATION|DATE|SUMMARY|CASE_REF):\s*(.+)$", re.IGNORECASE | re.MULTILINE)


@register_adapter
class IntelligenceReportAdapter(BaseAdapter):
    source_type = "intelligence_report"

    def parse(self, file_bytes: bytes) -> list[InvestigationRecord]:
        records: list[InvestigationRecord] = []
        text = file_bytes.decode("utf-8", errors="replace")

        # Split by delimiter; fallback to double-newline paragraphs
        blocks = _REPORT_SPLIT.split(text)
        if len(blocks) == 1:
            blocks = [b.strip() for b in text.split("\n\n") if b.strip()]

        for block in blocks:
            if not block.strip():
                continue

            fields: dict[str, str] = {}
            for m in _FIELD.finditer(block):
                fields[m.group(1).upper()] = m.group(2).strip()

            report_id = fields.get("REPORT_ID", f"intel_{len(records)+1}")
            case_ref = fields.get("CASE_REF") or report_id

            records.append(
                InvestigationRecord.create(
                    source_type=self.source_type,
                    raw_text=block.strip(),
                    raw_fields=fields,
                    case_ref=case_ref,
                    timestamp=fields.get("DATE"),
                    doc_label=f"Intel Report {report_id}",
                )
            )
        return records
