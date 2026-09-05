"""
NeuroNex — Financial Transaction Records Adapter (SYNTHETIC DATA ONLY)
Parses CSV with columns:
    txn_id, sender_account, receiver_account, amount, txn_datetime,
    txn_mode (UPI/NEFT/cash), remarks
Remarks field is passed through lightweight NER for named entities.
"""
from __future__ import annotations
import csv
import io
from app.ingestion.base import BaseAdapter, InvestigationRecord, register_adapter


@register_adapter
class FinancialAdapter(BaseAdapter):
    source_type = "financial"

    def parse(self, file_bytes: bytes) -> list[InvestigationRecord]:
        records: list[InvestigationRecord] = []
        text = file_bytes.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))

        for row in reader:
            txn_id = row.get("txn_id", "").strip()
            remarks = row.get("remarks", "").strip()

            # NER will run on remarks for any embedded person/org names
            raw_text = (
                f"Transaction {txn_id}: {row.get('sender_account', '')} "
                f"sent {row.get('amount', '')} via {row.get('txn_mode', '')} "
                f"to {row.get('receiver_account', '')}. Remarks: {remarks}"
            )

            records.append(
                InvestigationRecord.create(
                    source_type=self.source_type,
                    raw_text=raw_text,
                    raw_fields=dict(row),
                    timestamp=row.get("txn_datetime"),
                    doc_label=f"TXN {txn_id}",
                )
            )
        return records
