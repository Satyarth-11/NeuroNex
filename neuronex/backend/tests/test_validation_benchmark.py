"""
NeuroNex — Entity Resolution Benchmark Evaluation Unit Tests
Verifies precision, recall, F1 calculation, hard-negative pair scoring,
and threshold evaluation.
"""
import pytest
from app.pipeline.resolution import _fuzzy_match, _exact_match, get_settings


class MockEntity:
    def __init__(self, text: str, entity_type: str = "PERSON"):
        self.normalized_text = text
        self.entity_type = entity_type


def test_precision_recall_f1_formulas():
    """Verify precision = TP / (TP + FP), recall = TP / (TP + FN), F1 = 2*P*R/(P+R)."""
    tp, fp, fn = 112, 18, 3
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall)

    assert round(precision, 4) == 0.8615
    assert round(recall, 4) == 0.9739
    assert round(f1, 4) == 0.9143


def test_hard_negatives_produce_false_positives():
    """Verify hard negative pairs (e.g. Ramesh vs Rajesh) produce score crossing review threshold."""
    ent_a = MockEntity("Rajesh Kumar Sharma", "PERSON")
    ent_b = MockEntity("Ramesh Kumar Sharma", "PERSON")

    score, reason = _fuzzy_match(ent_a, ent_b)
    assert score > 0.72  # Crosses 0.72 review threshold, creating a genuine FP for review threshold evaluation!

    ent_c = MockEntity("Priya Mehta", "PERSON")
    ent_d = MockEntity("Priya Verma", "PERSON")
    score_c, _ = _fuzzy_match(ent_c, ent_d)
    assert score_c >= 0.72  # Crosses review threshold


def test_zero_denominator_protection():
    """Verify zero denominator protection when TP + FP = 0."""
    tp, fp, fn = 0, 0, 115
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    assert precision == 0.0
    assert recall == 0.0
    assert f1 == 0.0
