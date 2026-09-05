"""
NeuroNex — SQLAlchemy ORM Models (SQLite / PostgreSQL)
Seven tables as specified in the architecture document.
All timestamps are stored as UTC strings (ISO-8601).
"""
import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey,
    DateTime, Boolean, JSON,
)
from app.db_sql import Base


def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_code = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=_now)


# ---------------------------------------------------------------------------
# Documents (uploaded files, one per upload)
# ---------------------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    filename = Column(String(256), nullable=False)
    # source_type: fir|cdr|financial|surveillance|social_media|criminal_history|intelligence_report
    source_type = Column(String(64), nullable=False, index=True)
    file_type = Column(String(16), nullable=False)  # csv|txt|json|pdf
    raw_text = Column(Text, default="")
    cleaned_text = Column(Text, default="")
    structured_payload = Column(JSON, default=None)  # parsed rows for tabular sources
    # status: uploaded | processing | processed | failed
    status = Column(String(32), default="uploaded", index=True)
    uploaded_at = Column(DateTime, default=_now)
    record_count = Column(Integer, default=0)  # number of InvestigationRecords parsed
    error_message = Column(Text, nullable=True)


# ---------------------------------------------------------------------------
# Extracted Entities (raw NER output, pre-resolution)
# ---------------------------------------------------------------------------
class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    text = Column(String(512), nullable=False)
    entity_type = Column(String(64), nullable=False, index=True)
    normalized_text = Column(String(512), nullable=False)
    start_char = Column(Integer, default=0)
    end_char = Column(Integer, default=0)
    context_snippet = Column(Text, default="")
    # canonical_entity_id: Neo4j node id after resolution
    canonical_entity_id = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime, default=_now)


# ---------------------------------------------------------------------------
# Resolution Candidates (potential duplicate entity pairs)
# ---------------------------------------------------------------------------
class ResolutionCandidate(Base):
    __tablename__ = "resolution_candidates"

    id = Column(Integer, primary_key=True, index=True)
    entity_a_id = Column(Integer, ForeignKey("extracted_entities.id"), nullable=False)
    entity_b_id = Column(Integer, ForeignKey("extracted_entities.id"), nullable=False)
    entity_type = Column(String(64), nullable=False)
    similarity_score = Column(Float, nullable=False)
    match_reason = Column(String(256), nullable=False)
    # decision: pending | auto_merged | approved | rejected
    decision = Column(String(32), default="pending", index=True)
    decided_by = Column(String(128), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now)


# ---------------------------------------------------------------------------
# Insights (generated from analytics + community detection)
# ---------------------------------------------------------------------------
class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    # insight_type: central_entity | community | possible_duplicate | relationship_path
    insight_type = Column(String(64), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    explanation = Column(Text, nullable=False)
    entity_refs = Column(JSON, default=list)   # list of canonical_entity_ids
    source_refs = Column(JSON, default=list)   # list of document_ids
    contributing_source_types = Column(JSON, default=list)
    confidence = Column(Float, default=0.0)
    sample_size = Column(Integer, nullable=True)
    threshold_used = Column(Float, nullable=True)
    comparison_basis = Column(String(256), nullable=True)
    # status: proposed | approved | rejected | flagged
    status = Column(String(32), default="proposed", index=True)
    created_at = Column(DateTime, default=_now)


# ---------------------------------------------------------------------------
# Review Actions (analyst decisions on insights)
# ---------------------------------------------------------------------------
class ReviewAction(Base):
    __tablename__ = "review_actions"

    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey("insights.id"), nullable=False, index=True)
    analyst_id = Column(String(128), nullable=False)
    # decision: approved | rejected | flagged
    decision = Column(String(32), nullable=False)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=_now)


# ---------------------------------------------------------------------------
# Validation Runs (precision / recall / F1 vs ground-truth pairs)
# ---------------------------------------------------------------------------
class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, index=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    true_positives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    notes = Column(Text, default="")
    extra_metrics = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_now)
