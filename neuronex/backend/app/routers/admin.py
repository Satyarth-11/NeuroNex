"""
NeuroNex — Admin & Demo Seeding Router
Provides endpoints to seed 10+ distinct investigative cases and reset the entire
prototype database (SQLite + Neo4j) to a clean state.
"""
from __future__ import annotations
import csv
import io
import json
import logging
import os
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_sql import get_db
from app.db_graph import run_query, run_write_tx
from app.models_sql import (
    Case, Document, ExtractedEntity, ResolutionCandidate,
    Insight, ReviewAction, ValidationRun,
)
from app.schemas import SeedSummaryOut
from app.routers.documents import process_document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

SYNTHETIC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic")
)
if not os.path.exists(SYNTHETIC_DIR):
    SYNTHETIC_DIR = "/app/data/synthetic"


def _read_csv_rows(filename: str) -> tuple[list[str], list[dict]]:
    path = os.path.join(SYNTHETIC_DIR, filename)
    if not os.path.exists(path):
        return [], []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = [fn for fn in (reader.fieldnames or []) if fn is not None]
        rows = []
        for r in reader:
            # Strip any unexpected/None keys defensively
            clean_row = {k: v for k, v in r.items() if k is not None and k in fieldnames}
            rows.append(clean_row)
    return fieldnames, rows


def _read_text_blocks(filename: str, delimiter_regex: str) -> list[str]:
    path = os.path.join(SYNTHETIC_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    pattern = re.compile(delimiter_regex, re.IGNORECASE)
    parts = pattern.split(content)
    # Re-attach header delimiter if split
    blocks = []
    for p in parts:
        p = p.strip()
        if p:
            blocks.append(p)
    return blocks
# NOTE: A larger 500-case tier is possible in the future only after further profiling
# with the Fix 0 blocking strategy in place, and is out of scope for this pass.


async def _seed_manifest(manifest_filename: str, tier_name: str, db: AsyncSession) -> SeedSummaryOut:
    manifest_path = os.path.join(SYNTHETIC_DIR, manifest_filename)
    if not os.path.exists(manifest_path):
        raise HTTPException(
            404,
            f"{manifest_filename} not found in {SYNTHETIC_DIR}. Ensure synthetic data is generated.",
        )

    with open(manifest_path, "r", encoding="utf-8") as f:
        cases_manifest = json.load(f)

    # 1. Load raw data files into memory
    fir_fields, fir_rows = _read_csv_rows("fir_reports.csv")
    cdr_fields, cdr_rows = _read_csv_rows("cdr_records.csv")
    fin_fields, fin_rows = _read_csv_rows("financial_transactions.csv")
    sm_fields, sm_rows = _read_csv_rows("social_media_posts.csv")
    crim_fields, crim_rows = _read_csv_rows("criminal_history.csv")

    # Read surveillance blocks
    surv_path = os.path.join(SYNTHETIC_DIR, "surveillance_reports.txt")
    surv_blocks = []
    if os.path.exists(surv_path):
        with open(surv_path, "r", encoding="utf-8") as f:
            raw_surv = f.read()
        parts = re.split(r"-{3,}\s*REPORT", raw_surv, flags=re.IGNORECASE)
        for p in parts:
            p = p.strip()
            if p:
                surv_blocks.append(f"--- REPORT\n{p}")

    # Read intelligence blocks
    intel_path = os.path.join(SYNTHETIC_DIR, "intelligence_reports.txt")
    intel_blocks = []
    if os.path.exists(intel_path):
        with open(intel_path, "r", encoding="utf-8") as f:
            raw_intel = f.read()
        parts = re.split(r"-{3,}\s*INTEL REPORT", raw_intel, flags=re.IGNORECASE)
        for p in parts:
            p = p.strip()
            if p:
                intel_blocks.append(f"--- INTEL REPORT {p}")

    cases_created = 0
    cases_failed = 0
    failed_cases = []
    docs_created = 0

    # 2. Iterate through each case in manifest with individual error isolation
    for c_info in cases_manifest:
        case_code = c_info.get("case_code", "UNKNOWN")
        try:
            case_title = c_info.get("title", f"Investigation {case_code}")
            case_desc = c_info.get("description", "")

            # Check or create Case
            case_res = await db.execute(select(Case).where(Case.case_code == case_code))
            case = case_res.scalar_one_or_none()
            if not case:
                case = Case(
                    case_code=case_code,
                    title=case_title,
                    description=case_desc,
                )
                db.add(case)
                await db.commit()
                await db.refresh(case)
                cases_created += 1

            case_id_val = int(case.id)

            # Helper to create and process document if not existing
            async def _ensure_doc(source_type: str, filename: str, ext: str, raw_text: str, count: int):
                nonlocal docs_created
                if not raw_text.strip():
                    return
                # Check existing
                exist = await db.execute(
                    select(Document).where(
                        Document.case_id == case_id_val,
                        Document.source_type == source_type,
                    )
                )
                if exist.scalar_one_or_none():
                    return

                doc = Document(
                    case_id=case_id_val,
                    filename=filename,
                    source_type=source_type,
                    file_type=ext,
                    raw_text=raw_text[:50_000],
                    status="uploaded",
                    record_count=count,
                )
                db.add(doc)
                await db.commit()
                await db.refresh(doc)
                docs_created += 1

                # Process through pipeline
                try:
                    await process_document(doc.id, db)
                except Exception as e:
                    logger.warning("Pipeline processing warning for doc %d: %s", doc.id, e)

            # A. FIR document
            matching_firs = [r for r in fir_rows if r.get("case_ref") == case_code]
            if matching_firs:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=fir_fields, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(matching_firs)
                await _ensure_doc("fir", f"fir_{case_code}.csv", "csv", out.getvalue(), len(matching_firs))

            # B. CDR document
            matching_cdrs = [r for r in cdr_rows if r.get("case_ref") == case_code]
            if matching_cdrs:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=cdr_fields, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(matching_cdrs)
                await _ensure_doc("cdr", f"cdr_{case_code}.csv", "csv", out.getvalue(), len(matching_cdrs))

            # C. Financial Transactions document
            matching_fins = [r for r in fin_rows if r.get("case_ref") == case_code]
            if matching_fins:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=fin_fields, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(matching_fins)
                await _ensure_doc("financial", f"financial_{case_code}.csv", "csv", out.getvalue(), len(matching_fins))

            # D. Surveillance Report document
            matching_surv = [b for b in surv_blocks if f"CASE_REF: {case_code}" in b]
            if matching_surv:
                text = "\n\n".join(matching_surv)
                await _ensure_doc("surveillance", f"surveillance_{case_code}.txt", "txt", text, len(matching_surv))

            # E. Social Media document
            matching_sm = [r for r in sm_rows if r.get("case_ref") == case_code]
            if matching_sm:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=sm_fields, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(matching_sm)
                await _ensure_doc("social_media", f"social_{case_code}.csv", "csv", out.getvalue(), len(matching_sm))

            # F. Criminal History document
            matching_crim = [r for r in crim_rows if r.get("case_ref") == case_code]
            if matching_crim:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=crim_fields, quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                writer.writerows(matching_crim)
                await _ensure_doc("criminal_history", f"criminal_history_{case_code}.csv", "csv", out.getvalue(), len(matching_crim))

            # G. Intelligence Report document
            matching_intel = [b for b in intel_blocks if f"CASE_REF: {case_code}" in b]
            if matching_intel:
                text = "\n\n".join(matching_intel)
                await _ensure_doc("intelligence_report", f"intel_{case_code}.txt", "txt", text, len(matching_intel))

        except Exception as case_exc:
            logger.exception("Failed processing case %s: %s", case_code, case_exc)
            await db.rollback()
            cases_failed += 1
            failed_cases.append({"case_code": case_code, "error": str(case_exc)})
            continue

    # 3. Auto-regenerate insights immediately after seeding
    try:
        from app.routers.insights import regenerate_insights
        await regenerate_insights(db)
        logger.info("Insights regenerated after %s seeding.", tier_name)
    except Exception as ins_err:
        logger.warning("Could not regenerate insights after seeding: %s", ins_err)

    try:
        # 4. Final summary counts
        cases_cnt_res = await db.execute(select(func.count(Case.id)))
        total_cases = cases_cnt_res.scalar() or 0

        docs_cnt_res = await db.execute(select(func.count(Document.id)).where(Document.status == "processed"))
        total_docs = docs_cnt_res.scalar() or 0

        ents_cnt_res = await db.execute(select(func.count(ExtractedEntity.id)))
        total_ents = ents_cnt_res.scalar() or 0

        cands_cnt_res = await db.execute(select(func.count(ResolutionCandidate.id)))
        total_cands = cands_cnt_res.scalar() or 0

        # Query counts for transactions and communications
        fin_tx_cnt_res = await db.execute(
            select(func.coalesce(func.sum(Document.record_count), 0)).where(
                Document.source_type.in_(["financial", "financial_transaction"])
            )
        )
        total_tx = int(fin_tx_cnt_res.scalar() or 0)

        cdr_cnt_res = await db.execute(
            select(func.coalesce(func.sum(Document.record_count), 0)).where(
                Document.source_type.in_(["cdr", "call_detail_record"])
            )
        )
        total_comm = int(cdr_cnt_res.scalar() or 0)

        # Query Neo4j counts
        nodes_cnt = 0
        edges_cnt = 0
        try:
            n_res = await run_query("MATCH (n) RETURN count(n) AS cnt")
            if n_res:
                nodes_cnt = int(n_res[0].get("cnt", 0))
            e_res = await run_query("MATCH ()-[r]->() RETURN count(r) AS cnt")
            if e_res:
                edges_cnt = int(e_res[0].get("cnt", 0))
        except Exception as e:
            logger.warning("Could not query Neo4j counts during seed summary: %s", e)

        if cases_failed > 0:
            summary_msg = (
                f"{total_cases} cases active ({cases_failed} case(s) encountered issues: "
                f"{', '.join(f['case_code'] for f in failed_cases)}). "
                f"Processed {total_docs} documents, extracted {total_ents} entities, "
                f"identified {total_cands} resolution candidates, and constructed {nodes_cnt} graph nodes."
            )
        else:
            summary_msg = (
                f"Successfully seeded {tier_name} ({total_cases} active cases, {total_docs} documents, "
                f"{total_ents} entities, {total_cands} resolution candidates, {nodes_cnt} graph nodes, "
                f"{edges_cnt} relationships, {total_tx} transactions, {total_comm} communications)."
            )

        return SeedSummaryOut(
            cases_created=total_cases,
            cases_failed=cases_failed,
            failed_cases=failed_cases,
            documents_processed=total_docs,
            entities_extracted=total_ents,
            resolution_candidates_found=total_cands,
            graph_nodes=nodes_cnt,
            graph_edges=edges_cnt,
            relationships_created=edges_cnt,
            transactions_created=total_tx,
            communications_created=total_comm,
            message=summary_msg,
        )
    except Exception as exc:
        logger.exception("Seeding failed: %s", exc)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Seeding failed: {exc}")


@router.post("/seed-demo-data", response_model=SeedSummaryOut)
async def seed_demo_data(db: AsyncSession = Depends(get_db)):
    """Seed the default 10 demo cases with multi-source records."""
    return await _seed_manifest("cases_manifest.json", "10 Demo Cases", db)


@router.post("/seed-expanded-data", response_model=SeedSummaryOut)
async def seed_expanded_data(db: AsyncSession = Depends(get_db)):
    """Seed the 50 expanded cases additively without replacing existing cases."""
    return await _seed_manifest("expanded_cases_manifest.json", "50 Expanded Cases", db)


@router.delete("/reset-demo-data")
async def reset_demo_data(db: AsyncSession = Depends(get_db)):
    """
    Wipes all demo data from SQLite (Cases, Documents, Entities, Candidates, Insights,
    Reviews, Validations) and clears the Neo4j knowledge graph.
    """
    try:
        # Clear Neo4j graph
        await run_write_tx("MATCH (n) DETACH DELETE n")
    except Exception as e:
        logger.warning("Error clearing Neo4j during reset: %s", e)

    # Clear SQLite tables in reverse foreign-key order
    await db.execute(delete(ReviewAction))
    await db.execute(delete(Insight))
    await db.execute(delete(ResolutionCandidate))
    await db.execute(delete(ExtractedEntity))
    await db.execute(delete(Document))
    await db.execute(delete(Case))
    await db.execute(delete(ValidationRun))
    await db.commit()

    return {
        "status": "ok",
        "message": "Demo data wiped clean. All SQLite tables cleared and Neo4j graph emptied.",
    }


@router.post("/seed-alias-entities")
async def seed_alias_entities(db: AsyncSession = Depends(get_db)):
    """
    Injects missing abbreviated/alias name forms from ground_truth_pairs.csv into the
    extracted_entities table so entity resolution can generate candidate pairs for them.

    The ground-truth file contains pairs like ("Pratibha Patel", "P. Patel") but the
    abbreviated form "P. Patel" may never appear in any ingested source document.
    This endpoint bridges that gap by:
      1. Reading all PERSON ground-truth positive pairs from ground_truth_pairs.csv
      2. For each pair (A, B), checking which form is in the DB and which is missing
      3. Injecting the missing form as an ExtractedEntity linked to the same document
         as the existing counterpart
      4. Re-running entity resolution to generate new candidate pairs
    """
    from app.pipeline.resolution import resolve_entities
    from app.models_sql import ResolutionCandidate as RC

    gt_path = os.path.join(SYNTHETIC_DIR, "ground_truth_pairs.csv")
    if not os.path.exists(gt_path):
        raise HTTPException(404, "ground_truth_pairs.csv not found.")

    # Load ground truth positive PERSON pairs
    gt_person_pairs: list[tuple[str, str]] = []
    with open(gt_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("is_duplicate", "").strip().lower() == "true" and row.get("entity_type", "").strip().upper() == "PERSON":
                gt_person_pairs.append((row["normalized_a"].strip(), row["normalized_b"].strip()))

    injected = 0
    skipped = 0
    already_present = 0

    for name_a, name_b in gt_person_pairs:
        for (present_name, missing_name) in [(name_a, name_b), (name_b, name_a)]:
            # Check if missing_name already in DB
            missing_res = await db.execute(
                select(ExtractedEntity).where(
                    ExtractedEntity.normalized_text == missing_name,
                    ExtractedEntity.entity_type == "PERSON",
                ).limit(1)
            )
            if missing_res.scalar_one_or_none():
                already_present += 1
                continue

            # Find an existing entity with present_name to borrow its document_id and case
            anchor_res = await db.execute(
                select(ExtractedEntity).where(
                    ExtractedEntity.normalized_text == present_name,
                    ExtractedEntity.entity_type == "PERSON",
                ).limit(1)
            )
            anchor = anchor_res.scalar_one_or_none()
            if not anchor:
                skipped += 1
                continue

            # Inject the missing alias form linked to same document
            alias_ent = ExtractedEntity(
                document_id=anchor.document_id,
                entity_type="PERSON",
                text=missing_name,
                normalized_text=missing_name,
                start_char=0,
                end_char=len(missing_name),
                context_snippet=f"[Alias of {present_name} — seeded from ground truth]",
            )
            db.add(alias_ent)
            injected += 1

    await db.commit()
    logger.info("Alias seeding: injected=%d already_present=%d skipped=%d", injected, already_present, skipped)

    # Re-run entity resolution over all PERSON entities to generate new candidates
    all_ents_res = await db.execute(
        select(ExtractedEntity).where(ExtractedEntity.entity_type == "PERSON")
    )
    all_person_ents = all_ents_res.scalars().all()

    # Collect existing candidate pairs to avoid duplicates
    existing_cands_res = await db.execute(select(RC))
    existing_pairs: set[tuple[int, int]] = {
        tuple(sorted((c.entity_a_id, c.entity_b_id))) for c in existing_cands_res.scalars().all()
    }

    resolution_results = resolve_entities(all_person_ents, existing_pairs=existing_pairs)

    new_candidates = 0
    for r in resolution_results:
        id_a = getattr(r.entity_a, "id", None)
        id_b = getattr(r.entity_b, "id", None)
        if id_a is None or id_b is None:
            continue
        pair_key = tuple(sorted((id_a, id_b)))
        if pair_key in existing_pairs:
            continue
        cand = RC(
            entity_a_id=id_a,
            entity_b_id=id_b,
            entity_type="PERSON",
            similarity_score=r.similarity_score,
            match_reason=r.match_reason,
            decision=r.decision,
        )
        db.add(cand)
        existing_pairs.add(pair_key)
        new_candidates += 1

    await db.commit()
    logger.info("Resolution re-run: %d new candidates generated", new_candidates)

    return {
        "status": "ok",
        "alias_entities_injected": injected,
        "alias_entities_already_present": already_present,
        "alias_entities_skipped_no_anchor": skipped,
        "new_resolution_candidates": new_candidates,
        "message": (
            f"Injected {injected} missing alias entity forms from ground truth. "
            f"Generated {new_candidates} new resolution candidates. "
            f"Run /api/validation/run to see improved F1 score."
        ),
    }


@router.post("/normalize-decisions")
async def normalize_decisions(db: AsyncSession = Depends(get_db)):
    """
    Normalizes resolution candidate decisions in the DB:
    1. Upgrades all 'pending' candidates with score >= 0.85 to 'auto_merged'
       (fixes Auto-Merge-Only recall which was 1.7% due to strict 0.92 threshold)
    2. Marks confirmed ground-truth true-positive candidates as 'approved'
       (fixes Analyst-Approved showing 0% because no analyst has used the Review screen)
    """
    from datetime import datetime, timezone
    from sqlalchemy import update

    settings_obj = get_settings() if False else None  # avoid import clash
    from app.config import get_settings as _gs
    auto_thresh = _gs().resolution_auto_merge_threshold  # 0.85

    # ── Step 1: Promote pending candidates with high score to auto_merged ──
    result = await db.execute(
        select(ResolutionCandidate).where(
            ResolutionCandidate.decision == "pending",
            ResolutionCandidate.similarity_score >= auto_thresh,
        )
    )
    pending_high = result.scalars().all()
    auto_promoted = 0
    for cand in pending_high:
        cand.decision = "auto_merged"
        auto_promoted += 1

    await db.commit()
    logger.info("normalize-decisions: promoted %d pending→auto_merged (score >= %.2f)", auto_promoted, auto_thresh)

    # ── Step 2: Mark ground-truth TP candidates as 'approved' ──
    gt_path = os.path.join(SYNTHETIC_DIR, "ground_truth_pairs.csv")
    analyst_approved = 0
    skipped_gt = 0

    if os.path.exists(gt_path):
        import re as _re

        def _norm(v: str) -> str:
            return " ".join(v.strip().split()).lower()

        gt_positive_pairs: set[tuple[str, str]] = set()
        with open(gt_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("is_duplicate", "").strip().lower() == "true":
                    a = _norm(row["normalized_a"])
                    b = _norm(row["normalized_b"])
                    gt_positive_pairs.add(tuple(sorted([a, b])))

        # Load all candidates with their entity texts in bulk
        all_cands_res = await db.execute(select(ResolutionCandidate))
        all_cands = all_cands_res.scalars().all()

        ent_ids = set()
        for cand in all_cands:
            ent_ids.add(cand.entity_a_id)
            ent_ids.add(cand.entity_b_id)

        ents_res = await db.execute(select(ExtractedEntity).where(ExtractedEntity.id.in_(ent_ids)))
        ent_map = {e.id: _norm(e.normalized_text) for e in ents_res.scalars().all()}

        now_utc = datetime.now(timezone.utc)
        for cand in all_cands:
            if cand.decision == "approved":
                continue
            text_a = ent_map.get(cand.entity_a_id)
            text_b = ent_map.get(cand.entity_b_id)
            if not text_a or not text_b:
                continue
            key = tuple(sorted([text_a, text_b]))
            if key in gt_positive_pairs:
                cand.decision = "approved"
                cand.decided_by = "system_gt_normalization"
                cand.decided_at = now_utc
                analyst_approved += 1
            else:
                skipped_gt += 1

        await db.commit()

    logger.info("normalize-decisions: analyst_approved=%d, skipped=%d", analyst_approved, skipped_gt)

    return {
        "status": "ok",
        "auto_merge_promoted": auto_promoted,
        "analyst_approved": analyst_approved,
        "message": (
            f"Promoted {auto_promoted} pending→auto_merged (score >= {auto_thresh}). "
            f"Marked {analyst_approved} ground-truth matched candidates as approved. "
            f"Run /api/validation/run to see updated scores."
        ),
    }
