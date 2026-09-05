"""
NeuroNex — Validation Router
Runs precision/recall/F1 calculation against the synthetic ground-truth pairs file.
"""
from __future__ import annotations
import csv
import os
import re
import logging
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_sql import get_db
from app.models_sql import ValidationRun, ResolutionCandidate, ExtractedEntity
from app.schemas import ValidationRunOut

from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/validation", tags=["validation"])

GROUND_TRUTH_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "synthetic", "ground_truth_pairs.csv"
)

DATASET_NOTE = (
    "Prototype validation on synthetic ground-truth dataset. "
    "Not representative of real-world law-enforcement accuracy."
)


async def _validate_entity_resolution(db: AsyncSession) -> dict:
    """Evaluate entity resolution against synthetic ground truth pairs."""
    if not os.path.exists(GROUND_TRUTH_PATH):
        return {
            "status": "missing_ground_truth",
            "precision": None,
            "recall": None,
            "f1_score": None,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "total_evaluated": 0,
            "notes": "ground_truth_pairs.csv not found — run generate_synthetic_data.py first",
        }

    from app.pipeline.cleaning import normalise_phone
    from app.pipeline.resolution import _fuzzy_match, _exact_match, get_settings

    def _norm_val(val: str) -> str:
        v = " ".join(val.strip().split()).lower()
        if re.match(r"^\+?91?[6-9]\d{9}$", v.replace("-", "").replace(" ", "")):
            return normalise_phone(v).lower()
        return v

    class _MockEnt:
        def __init__(self, text: str, etype: str):
            self.normalized_text = text
            self.entity_type = etype

    # Load all ground truth benchmark pairs (both positive duplicate pairs and hard-negative pairs)
    gt_pairs: list[dict] = []
    with open(GROUND_TRUTH_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            a_norm = _norm_val(row["normalized_a"])
            b_norm = _norm_val(row["normalized_b"])
            gt_pairs.append({
                "a_norm": a_norm,
                "b_norm": b_norm,
                "key": tuple(sorted([a_norm, b_norm])),
                "is_dup": row["is_duplicate"].strip().lower() == "true",
                "entity_type": row.get("entity_type", "PERSON"),
            })

    settings = get_settings()
    review_threshold = settings.resolution_review_threshold
    auto_threshold = settings.resolution_auto_merge_threshold

    # 1. Run pairwise scorer across ALL ground-truth benchmark pairs (positives + hard negatives)
    scored_gt_pairs = []
    for p in gt_pairs:
        ent_a = _MockEnt(p["a_norm"], p["entity_type"])
        ent_b = _MockEnt(p["b_norm"], p["entity_type"])
        if p["entity_type"] == "PHONE":
            score, reason = _exact_match(ent_a, ent_b)
        else:
            score, reason = _fuzzy_match(ent_a, ent_b)
        scored_gt_pairs.append({
            "key": p["key"],
            "is_dup": p["is_dup"],
            "score": score,
            "reason": reason,
        })

    def _eval_scored_benchmark(predicate_fn, notes: str, threshold: float | None = None) -> dict:
        tp = fp = tn = fn = 0
        for item in scored_gt_pairs:
            system_pred = predicate_fn(item)
            is_dup = item["is_dup"]
            if is_dup and system_pred:
                tp += 1
            elif not is_dup and system_pred:
                fp += 1
            elif not is_dup and not system_pred:
                tn += 1
            elif is_dup and not system_pred:
                fn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        out = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "total_benchmark_pairs": len(scored_gt_pairs),
            "notes": notes,
        }
        if threshold is not None:
            out["evaluation_threshold"] = threshold
        return out

    algorithmic = _eval_scored_benchmark(
        lambda item: item["score"] >= review_threshold,
        notes="Evaluates resolver similarity predictions (score >= review threshold) across all benchmark positive and hard-negative pairs.",
        threshold=review_threshold,
    )

    auto_merge_only = _eval_scored_benchmark(
        lambda item: item["score"] >= auto_threshold,
        notes="Evaluates strict high-confidence auto-merged predictions (score >= auto-merge threshold) across all benchmark positive and hard-negative pairs.",
        threshold=auto_threshold,
    )

    # 2. Evaluate Analyst-Approved Merges against DB candidates (Human Workflow)
    result = await db.execute(select(ResolutionCandidate))
    candidates = result.scalars().all()

    approved_cands = [c for c in candidates if c.decision == "approved"]
    if approved_cands:
        ent_ids = set()
        for c in approved_cands:
            ent_ids.add(c.entity_a_id)
            ent_ids.add(c.entity_b_id)

        ents_res = await db.execute(select(ExtractedEntity).where(ExtractedEntity.id.in_(ent_ids)))
        ent_map = {e.id: _norm_val(e.normalized_text) for e in ents_res.scalars().all()}

        approved_keys = set()
        for c in approved_cands:
            if c.entity_a_id in ent_map and c.entity_b_id in ent_map:
                approved_keys.add(tuple(sorted([ent_map[c.entity_a_id], ent_map[c.entity_b_id]])))

        analyst_approved = _eval_scored_benchmark(
            lambda item: item["key"] in approved_keys,
            notes="Measures manual analyst-approved merges from human review workflow against ground-truth pairs.",
        )
    else:
        total_gt_positives = sum(1 for p in gt_pairs if p["is_dup"])
        total_gt_negatives = sum(1 for p in gt_pairs if not p["is_dup"])
        analyst_approved = {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": total_gt_negatives,
            "false_negatives": total_gt_positives,
            "total_benchmark_pairs": len(gt_pairs),
            "notes": "0 manual approvals submitted in review screen — reflects analyst workflow usage.",
        }

    # Candidate coverage breakdown
    gt_positive_keys = {item["key"] for item in gt_pairs if item["is_dup"]}
    surfaced_keys = {item["key"] for item in scored_gt_pairs if item["score"] >= review_threshold}
    gt_positives_found = gt_positive_keys & surfaced_keys
    gt_positives_missed = gt_positive_keys - surfaced_keys

    coverage_breakdown = {
        "ground_truth_positive_pairs": len(gt_positive_keys),
        "candidate_pairs_surfaced": len(surfaced_keys),
        "gt_positives_found_as_candidates": len(gt_positives_found),
        "gt_positives_missed_entirely": len(gt_positives_missed),
    }

    return {
        "status": "evaluated",
        "precision": algorithmic["precision"],
        "recall": algorithmic["recall"],
        "f1_score": algorithmic["f1_score"],
        "true_positives": algorithmic["true_positives"],
        "false_positives": algorithmic["false_positives"],
        "false_negatives": algorithmic["false_negatives"],
        "algorithmic": algorithmic,
        "auto_merge_only": auto_merge_only,
        "analyst_approved": analyst_approved,
        "coverage_breakdown": coverage_breakdown,
        "total_evaluated": len(gt_pairs),
        "notes": f"Evaluated against {len(gt_pairs)} synthetic ground-truth pairs across 3 evaluation criteria.",
    }


NER_GT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "synthetic", "ner_ground_truth.csv"
)


def _validate_ner_extraction() -> dict:
    """Evaluate NER extraction against ground truth spans."""
    if not os.path.exists(NER_GT_PATH):
        return {
            "status": "no_ground_truth",
            "message": "No labelled NER ground-truth dataset available for this prototype run.",
            "precision": None,
            "recall": None,
            "f1_score": None,
        }

    from app.pipeline.ner import extract_entities
    tp = fp = fn = 0
    total_samples = 0
    type_stats: dict[str, dict[str, int]] = {}

    with open(NER_GT_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_samples += 1
            text = row.get("text", "")
            raw_expected = row.get("expected_entities", "")
            expected_set = {
                item.strip().lower() for item in raw_expected.split(";") if item.strip()
            }

            extracted = extract_entities(text)
            extracted_set = {
                f"{e.entity_type.lower()}:{e.normalized_text.lower()}"
                for e in extracted
            }

            matched = expected_set.intersection(extracted_set)
            tp += len(matched)
            fp += len(extracted_set - expected_set)
            fn += len(expected_set - extracted_set)

            # Per entity type tracking
            for item in expected_set:
                etype = item.split(":")[0].upper()
                type_stats.setdefault(etype, {"tp": 0, "fp": 0, "fn": 0})
                if item in matched:
                    type_stats[etype]["tp"] += 1
                else:
                    type_stats[etype]["fn"] += 1

            for item in (extracted_set - expected_set):
                etype = item.split(":")[0].upper()
                type_stats.setdefault(etype, {"tp": 0, "fp": 0, "fn": 0})
                type_stats[etype]["fp"] += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    by_type_metrics = {}
    for etype, stats in type_stats.items():
        t_tp, t_fp, t_fn = stats["tp"], stats["fp"], stats["fn"]
        t_prec = t_tp / (t_tp + t_fp) if (t_tp + t_fp) > 0 else 0.0
        t_rec = t_tp / (t_tp + t_fn) if (t_tp + t_fn) > 0 else 0.0
        t_f1 = (2 * t_prec * t_rec / (t_prec + t_rec)) if (t_prec + t_rec) > 0 else 0.0
        by_type_metrics[etype] = {
            "precision": round(t_prec, 4),
            "recall": round(t_rec, 4),
            "f1_score": round(t_f1, 4),
            "true_positives": t_tp,
            "false_positives": t_fp,
            "false_negatives": t_fn,
        }

    return {
        "status": "evaluated",
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "by_type": by_type_metrics,
        "total_samples": total_samples,
        "notes": f"Evaluated against {total_samples} labelled synthetic sentences across spaCy and regex extraction.",
    }


async def _validate_pattern_detection(db: AsyncSession) -> dict:
    """Evaluate unsupervised pattern detection by detector coverage across modalities."""
    from app.pipeline.patterns import detect_all_patterns
    patterns = await detect_all_patterns(db)

    all_detectors = [
        "cross_case_entity",
        "unusual_transaction_amount",
        "high_frequency_communication",
        "multi_source_convergence",
        "dense_local_cluster",
    ]

    breakdown = {d: 0 for d in all_detectors}
    for p in patterns:
        ptype = p.get("pattern_type")
        if ptype in breakdown:
            breakdown[ptype] += 1
        elif ptype:
            breakdown[ptype] = breakdown.get(ptype, 0) + 1

    patterns_fired = sum(1 for cnt in breakdown.values() if cnt > 0)
    patterns_evaluated = len(all_detectors)
    total_detections = len(patterns)
    coverage_pct = round((patterns_fired / patterns_evaluated) * 100, 1) if patterns_evaluated else 0.0

    return {
        "status": "evaluated",
        "patterns_evaluated": patterns_evaluated,
        "patterns_fired": patterns_fired,
        "total_detections": total_detections,
        "coverage_pct": coverage_pct,
        "breakdown": breakdown,
        "total_patterns_flagged": total_detections,
        "distinct_pattern_types": patterns_fired,
        "detector_coverage": round(patterns_fired / patterns_evaluated, 2) if patterns_evaluated else 0.0,
        "active_detectors": [k for k, v in breakdown.items() if v > 0],
        "available_detectors": all_detectors,
        "notes": (
            "Unsupervised rule-based pattern detection is evaluated by detector coverage across data modalities, "
            "not classification accuracy, as ground-truth labels are not defined for synthetic exploratory analysis."
        ),
    }


@router.post("/run", response_model=ValidationRunOut, status_code=201)
async def run_validation(db: AsyncSession = Depends(get_db)):
    """
    Run multi-task validation suite across Entity Resolution, NER Extraction,
    Pattern Detection, and Genuine ML Priority Classification.
    """
    er_res = await _validate_entity_resolution(db)
    ner_res = _validate_ner_extraction()
    pat_res = await _validate_pattern_detection(db)

    from app.pipeline.ml_model import train_and_evaluate_logistic_regression
    ml_res = train_and_evaluate_logistic_regression()

    run_timestamp = datetime.now(timezone.utc).isoformat()

    run = ValidationRun(
        precision=er_res.get("precision"),
        recall=er_res.get("recall"),
        f1_score=er_res.get("f1_score"),
        true_positives=er_res.get("true_positives", 0),
        false_positives=er_res.get("false_positives", 0),
        false_negatives=er_res.get("false_negatives", 0),
        notes=er_res.get("notes", ""),
        extra_metrics={
            "entity_resolution": er_res,
            "ner_extraction": ner_res,
            "pattern_detection": pat_res,
            "ml_priority_model": ml_res,
            "dataset_note": DATASET_NOTE,
            "run_at": run_timestamp,
        },
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    return ValidationRunOut(
        id=run.id,
        precision=run.precision,
        recall=run.recall,
        f1_score=run.f1_score,
        true_positives=run.true_positives,
        false_positives=run.false_positives,
        false_negatives=run.false_negatives,
        notes=run.notes,
        created_at=run.created_at,
        extra_metrics=run.extra_metrics,
        entity_resolution=er_res,
        ner_extraction=ner_res,
        pattern_detection=pat_res,
        ml_priority_model=ml_res,
        dataset_note=DATASET_NOTE,
        run_at=run_timestamp,
    )


@router.get("/history", response_model=list[ValidationRunOut])
async def validation_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ValidationRun).order_by(ValidationRun.created_at.desc()))
    runs = result.scalars().all()

    output = []
    from app.pipeline.ml_model import train_and_evaluate_logistic_regression
    cached_ml_res = None

    for r in runs:
        extras = r.extra_metrics or {}
        er_metrics = extras.get("entity_resolution") or {
            "status": "evaluated" if r.precision is not None else "missing_ground_truth",
            "precision": r.precision,
            "recall": r.recall,
            "f1_score": r.f1_score,
            "true_positives": r.true_positives,
            "false_positives": r.false_positives,
            "false_negatives": r.false_negatives,
            "notes": r.notes,
        }
        ner_metrics = extras.get("ner_extraction") or _validate_ner_extraction()
        pat_metrics = extras.get("pattern_detection") or _validate_pattern_detection()
        ml_metrics = extras.get("ml_priority_model")
        if ml_metrics is None:
            if cached_ml_res is None:
                cached_ml_res = train_and_evaluate_logistic_regression()
            ml_metrics = cached_ml_res

        output.append(
            ValidationRunOut(
                id=r.id,
                precision=r.precision,
                recall=r.recall,
                f1_score=r.f1_score,
                true_positives=r.true_positives,
                false_positives=r.false_positives,
                false_negatives=r.false_negatives,
                notes=r.notes,
                created_at=r.created_at,
                extra_metrics=r.extra_metrics,
                entity_resolution=er_metrics,
                ner_extraction=ner_metrics,
                pattern_detection=pat_metrics,
                ml_priority_model=ml_metrics,
                dataset_note=extras.get("dataset_note", DATASET_NOTE),
                run_at=extras.get("run_at", r.created_at.isoformat() if r.created_at else None),
            )
        )
    return output
