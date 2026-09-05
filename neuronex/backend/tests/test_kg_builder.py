try:
    import pytest
except ImportError:
    pytest = None
from unittest.mock import AsyncMock, patch
from app.pipeline.kg_builder import build_graph
from app.models_sql import ExtractedEntity
from app.ingestion.base import InvestigationRecord


class _PytestMock:
    def mark(self):
        return self
    def asyncio(self, f):
        return f

if pytest is None:
    pytest = _PytestMock()


@pytest.mark.asyncio
async def test_fir_multi_person_linking():
    """
    FIX A verification: build_graph() on a synthetic FIR record containing
    3 PERSON entities must result in 3 separate MENTIONED_IN edges to the case, not 1.
    """
    record = InvestigationRecord(
        source_type="fir",
        raw_text="FIR details...",
        case_ref="CASE-TEST-001",
        raw_fields={"fir_no": "CASE-TEST-001", "narrative_text": "A, B, and C involved."}
    )

    entities = [
        ExtractedEntity(document_id=1, text="Rajesh Sharma", entity_type="PERSON", normalized_text="rajesh sharma"),
        ExtractedEntity(document_id=1, text="Vikram Singh", entity_type="PERSON", normalized_text="vikram singh"),
        ExtractedEntity(document_id=1, text="Amit Verma", entity_type="PERSON", normalized_text="amit verma"),
    ]

    upsert_edge_calls = []

    async def mock_upsert_node(entity_type, text, source_type, doc_id, extra_props=None):
        return f"{entity_type}_{text.replace(' ', '_').lower()}"

    async def mock_upsert_edge(src_id, dst_id, rel_type, source_type, doc_id, **kwargs):
        upsert_edge_calls.append({
            "src": src_id,
            "dst": dst_id,
            "rel_type": rel_type,
            "source_type": source_type,
            "doc_id": doc_id,
            "kwargs": kwargs
        })

    with patch("app.pipeline.kg_builder.upsert_node", side_effect=mock_upsert_node), \
         patch("app.pipeline.kg_builder.upsert_edge", side_effect=mock_upsert_edge):
        nodes, edges = await build_graph(record, entities, doc_id="101")

    # Verify 3 nodes upserted
    assert nodes == 3

    # Filter MENTIONED_IN edges to the case
    mentioned_edges = [e for e in upsert_edge_calls if e["rel_type"] == "MENTIONED_IN"]
    assert len(mentioned_edges) == 3, f"Expected 3 MENTIONED_IN edges, got {len(mentioned_edges)}"

    # Check that each distinct person has a MENTIONED_IN edge
    src_ids = {e["src"] for e in mentioned_edges}
    assert src_ids == {"person_rajesh_sharma", "person_vikram_singh", "person_amit_verma"}

    # Also verify person-person co-occurrence edges (3 pairs: A-B, A-C, B-C) + 3 MENTIONED_IN = 6 edges
    assert edges == 6


if __name__ == "__main__":
    import asyncio
    print("Running test_fir_multi_person_linking...")
    asyncio.run(test_fir_multi_person_linking())
    print("ALL KG BUILDER TESTS PASSED!")
