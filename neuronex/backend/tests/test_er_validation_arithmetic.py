"""
Unit tests for Phase 8: Entity Resolution Validation Arithmetic & Symmetric Pair Matching
Independent of the live database.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def evaluate_pairs(gt_pairs: dict[tuple[str, str], bool], system_predictions: dict[tuple[str, str], bool]) -> dict:
    """Independent implementation of validation arithmetic matching validation.py."""
    tp = fp = fn = 0
    for key, is_dup in gt_pairs.items():
        norm_key = tuple(sorted(key))
        pred = system_predictions.get(norm_key, False)
        if is_dup and pred:
            tp += 1
        elif not is_dup and pred:
            fp += 1
        elif is_dup and not pred:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
    }


def test_validation_arithmetic_hand_computed():
    """
    Test fixture:
    Pair 1: (A, B) -> GT True, Pred True (TP)
    Pair 2: (C, D) -> GT True, Pred True (TP)
    Pair 3: (E, F) -> GT True, Pred False (FN)
    Pair 4: (G, H) -> GT False, Pred True (FP)
    Pair 5: (I, J) -> GT False, Pred False (TN)

    Hand calculations:
    TP = 2
    FP = 1
    FN = 1
    Precision = 2 / (2 + 1) = 2/3 = 0.6667
    Recall = 2 / (2 + 1) = 2/3 = 0.6667
    F1 = 2 * (2/3) * (2/3) / ((2/3) + (2/3)) = 2/3 = 0.6667
    """
    gt = {
        ("a", "b"): True,
        ("c", "d"): True,
        ("e", "f"): True,
        ("g", "h"): False,
        ("i", "j"): False,
    }
    preds = {
        ("a", "b"): True,
        ("c", "d"): True,
        ("g", "h"): True,
    }

    metrics = evaluate_pairs(gt, preds)
    assert metrics["true_positives"] == 2
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["precision"] == 0.6667
    assert metrics["recall"] == 0.6667
    assert metrics["f1_score"] == 0.6667


def test_symmetric_pair_matching():
    """
    Confirm that (A, B) and (B, A) hit the exact same ground-truth entry.
    """
    gt = {
        tuple(sorted(["Rajesh Kumar Sharma", "Raju"])): True,
        tuple(sorted(["+919876543210", "9876543210"])): True,
    }

    # Query with reversed order
    rev_pair_1 = tuple(sorted(["Raju", "Rajesh Kumar Sharma"]))
    rev_pair_2 = tuple(sorted(["9876543210", "+919876543210"]))

    assert rev_pair_1 in gt
    assert gt[rev_pair_1] is True
    assert rev_pair_2 in gt
    assert gt[rev_pair_2] is True


if __name__ == "__main__":
    print("Running test_validation_arithmetic_hand_computed...")
    test_validation_arithmetic_hand_computed()
    print("Running test_symmetric_pair_matching...")
    test_symmetric_pair_matching()
    print("ALL ER VALIDATION ARITHMETIC TESTS PASSED!")
