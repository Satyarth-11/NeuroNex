import time
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.pipeline.resolution import resolve_entities, find_candidates, _get_blocking_keys


@dataclass
class MockEntity:
    id: int
    entity_type: str
    normalized_text: str
    document_id: int = 1


def test_fix0_blocking_and_indexing_performance():
    """
    FIX 0 Unit Test:
    Generate 2,000 synthetic PERSON entities with a fixed seed,
    confirm find_candidates() completes in under 5 seconds and still correctly
    finds deliberately-planted duplicate pairs.
    """
    entities = []

    # Deliberately plant known duplicate pairs
    planted_pairs = [
        ("Rajesh Kumar Sharma", "R.K. Sharma"),
        ("Dinesh Patel", "D. Patel"),
        ("Priya Mehta", "Priya M"),
        ("Arjun Malhotra", "Arjun M"),
        ("Vikram Singh", "V. Singh"),
    ]

    ent_id = 1
    for a, b in planted_pairs:
        entities.append(MockEntity(id=ent_id, entity_type="PERSON", normalized_text=a, document_id=1))
        ent_id += 1
        entities.append(MockEntity(id=ent_id, entity_type="PERSON", normalized_text=b, document_id=2))
        ent_id += 1

    # Generate 1,990 background entities with realistic distinct names
    for idx in range(11, 2001):
        entities.append(MockEntity(
            id=ent_id,
            entity_type="PERSON",
            normalized_text=f"User{idx} Person{idx}",
            document_id=ent_id + 10,
        ))
        ent_id += 1

    start_time = time.time()
    candidates = find_candidates(entities)
    elapsed = time.time() - start_time

    print(f"\n[FIX 0 UNIT TEST] 2,000 PERSON entities resolved in {elapsed:.3f} seconds. Candidates found: {len(candidates)}")

    # 1. Performance assertion: strictly under 5 seconds
    assert elapsed < 5.0, f"Resolution took {elapsed:.2f}s, expected < 5.0s!"

    # 2. Recall assertion: ensure planted pairs are recovered
    found_matches = set()
    for c in candidates:
        pair = tuple(sorted([c.entity_a.normalized_text, c.entity_b.normalized_text]))
        found_matches.add(pair)

    for a, b in planted_pairs:
        target_pair = tuple(sorted([a, b]))
        assert target_pair in found_matches, f"Planted pair {target_pair} was missed by blocking/indexing!"


def test_fix0_exact_types_bucketing():
    """
    Confirm EXACT_TYPES (PHONE, ACCOUNT, VEHICLE, CASE_REF) use O(n) exact grouping
    without comparing non-identical items.
    """
    phones = [
        MockEntity(id=1, entity_type="PHONE", normalized_text="+919876543210", document_id=1),
        MockEntity(id=2, entity_type="PHONE", normalized_text="+919876543210", document_id=2),
        MockEntity(id=3, entity_type="PHONE", normalized_text="+919123456789", document_id=3),
        MockEntity(id=4, entity_type="PHONE", normalized_text="+919988776655", document_id=4),
    ]
    cands = resolve_entities(phones)
    assert len(cands) == 1
    assert cands[0].entity_a.id == 1 and cands[0].entity_b.id == 2
    assert cands[0].similarity_score == 1.0


def test_fix0_safety_cap():
    """
    Confirm bucket safety cap skips comparison when a single bucket exceeds 500 entities.
    """
    large_bucket = [
        MockEntity(id=i, entity_type="PHONE", normalized_text="+919000000000", document_id=i)
        for i in range(1, 505)
    ]
    # Bucket size 504 > 500 safety cap
    cands = resolve_entities(large_bucket)
    assert len(cands) == 0  # Bypassed by safety cap


if __name__ == "__main__":
    print("Running test_fix0_blocking_and_indexing_performance...")
    test_fix0_blocking_and_indexing_performance()
    print("Running test_fix0_exact_types_bucketing...")
    test_fix0_exact_types_bucketing()
    print("Running test_fix0_safety_cap...")
    test_fix0_safety_cap()
    print("ALL FIX 0 TESTS PASSED!")
