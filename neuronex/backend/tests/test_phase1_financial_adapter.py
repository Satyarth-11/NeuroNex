"""
Targeted test for Phase 1: Financial Source-Type Normalization & Adapter Resolution.
Verifies:
1. normalize_source_type converts legacy variants to canonical types
2. get_adapter successfully resolves "financial_transaction" to FinancialAdapter
3. Financial CSV parsing produces InvestigationRecords with source_type="financial"
4. kg_builder generates TRANSFERRED_TO edges for financial records
"""
import sys
import os
import io
import csv

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.base import normalize_source_type, get_adapter, SOURCE_TYPES
from app.ingestion.financial_adapter import FinancialAdapter


def test_source_type_normalization():
    assert normalize_source_type("financial_transaction") == "financial"
    assert normalize_source_type("financial_transactions") == "financial"
    assert normalize_source_type("finance") == "financial"
    assert normalize_source_type("financial") == "financial"
    assert normalize_source_type("call_detail_record") == "cdr"
    assert normalize_source_type("surveillance_report") == "surveillance"
    assert normalize_source_type("first_information_report") == "fir"
    assert normalize_source_type("fir") == "fir"
    print("[PASS] test_source_type_normalization passed")


def test_get_adapter_resolution():
    adapter = get_adapter("financial_transaction")
    assert isinstance(adapter, FinancialAdapter)
    assert adapter.source_type == "financial"

    # Also check canonical
    adapter2 = get_adapter("financial")
    assert isinstance(adapter2, FinancialAdapter)
    print("[PASS] test_get_adapter_resolution passed")


def test_financial_adapter_parse():
    adapter = get_adapter("financial_transaction")
    sample_csv = (
        "txn_id,sender_account,receiver_account,amount,txn_datetime,txn_mode,remarks\n"
        "TXN9901,ACC100200300,ACC400500600,250000,2024-03-15T10:30:00Z,NEFT,Consulting fee payment\n"
    ).encode("utf-8")

    records = adapter.parse(sample_csv)
    assert len(records) == 1
    rec = records[0]
    assert rec.source_type == "financial"
    assert rec.raw_fields["sender_account"] == "ACC100200300"
    assert rec.raw_fields["receiver_account"] == "ACC400500600"
    assert rec.raw_fields["amount"] == "250000"
    assert "ACC100200300" in rec.raw_text
    print("[PASS] test_financial_adapter_parse passed")


def test_financial_edge_inference():
    from app.ingestion.base import InvestigationRecord
    from app.pipeline.kg_builder import _build_financial_edges

    record = InvestigationRecord.create(
        source_type="financial",
        raw_text="Transaction TXN9901: ACC100200300 sent 250000 via NEFT to ACC400500600",
        raw_fields={
            "txn_id": "TXN9901",
            "sender_account": "ACC100200300",
            "receiver_account": "ACC400500600",
            "amount": "250000",
            "txn_mode": "NEFT",
            "remarks": "Consulting fee payment",
        },
        case_ref="CASE-2024-001",
    )

    upsert_edges = []

    async def mock_upsert_node(entity_type, name, source_type, doc_id):
        return f"{entity_type}_{name}"

    async def mock_upsert_edge(src, dst, rel_type, source_type, doc_id, **kwargs):
        upsert_edges.append({
            "src": src,
            "dst": dst,
            "rel_type": rel_type,
            "source_type": source_type,
            "doc_id": doc_id,
            "kwargs": kwargs,
        })

    import asyncio
    from unittest.mock import patch

    async def run():
        with patch("app.pipeline.kg_builder.upsert_node", side_effect=mock_upsert_node), \
             patch("app.pipeline.kg_builder.upsert_edge", side_effect=mock_upsert_edge):
            edge_count = await _build_financial_edges(record, {}, "doc_99")
            assert edge_count == 1
            assert len(upsert_edges) == 1
            edge = upsert_edges[0]
            assert edge["rel_type"] == "TRANSFERRED_TO"
            assert edge["source_type"] == "financial"
            assert edge["src"] == "ACCOUNT_ACC100200300"
            assert edge["dst"] == "ACCOUNT_ACC400500600"
            assert edge["kwargs"]["weight"] == 250000
            assert edge["kwargs"]["case_ref"] == "CASE-2024-001"

    asyncio.run(run())
    print("[PASS] test_financial_edge_inference passed")


if __name__ == "__main__":
    print("Running Phase 1 targeted tests...")
    test_source_type_normalization()
    test_get_adapter_resolution()
    test_financial_adapter_parse()
    test_financial_edge_inference()
    print("ALL PHASE 1 TARGETED TESTS PASSED!")
