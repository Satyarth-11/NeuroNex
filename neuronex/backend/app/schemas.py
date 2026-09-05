"""
NeuroNex — Pydantic schemas for API request/response validation.
"""
from __future__ import annotations
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
class CaseCreate(BaseModel):
    case_code: str
    title: str
    description: str = ""


class CaseOut(BaseModel):
    id: int
    case_code: str
    title: str
    description: str
    created_at: datetime
    document_count: int = 0
    entity_count: int = 0
    relationship_count: int = 0

    model_config = {"from_attributes": True}


class TopConnectedEntity(BaseModel):
    id: str
    name: str
    entity_type: str
    degree: int


class CaseDetailOut(BaseModel):
    id: int
    case_code: str
    title: str
    description: str
    created_at: datetime
    document_count: int = 0
    entity_count: int = 0
    relationship_count: int = 0
    community_count: int = 0
    insight_count: int = 0
    canonical_entity_ids: list[str] = Field(default_factory=list)
    documents: list[DocumentOut] = Field(default_factory=list)
    top_connected_entities: list[TopConnectedEntity] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------
class DocumentOut(BaseModel):
    id: int
    case_id: Optional[int] = None
    filename: str
    source_type: str
    file_type: str
    status: str
    uploaded_at: datetime
    record_count: int
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentDetailOut(BaseModel):
    id: int
    case_id: Optional[int] = None
    case_code: Optional[str] = None
    case_title: Optional[str] = None
    filename: str
    source_type: str
    file_type: str
    status: str
    uploaded_at: datetime
    record_count: int = 0
    raw_text: Optional[str] = ""
    cleaned_text: Optional[str] = ""
    error_message: Optional[str] = None
    extracted_entities: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProcessResult(BaseModel):
    document_id: int
    records_parsed: int
    entities_extracted: int
    resolution_candidates: int
    graph_nodes_upserted: int
    graph_edges_upserted: int
    status: str


# ---------------------------------------------------------------------------
# Extracted Entities
# ---------------------------------------------------------------------------
class EntityOut(BaseModel):
    id: int
    document_id: int
    text: str
    entity_type: str
    normalized_text: str
    context_snippet: str
    canonical_entity_id: Optional[str] = None
    created_at: datetime
    mention_count: int = 1
    source_document_count: int = 1
    source_type_count: int = 1
    related_case_count: int = 0
    resolution_status: str = "unresolved"

    model_config = {"from_attributes": True}


class EntityTraceOut(BaseModel):
    canonical_entity_id: str
    entity_type: str
    name: str
    mentions: list[dict]
    source_documents: list[dict]
    source_types: list[str]
    graph_node: Optional[dict] = None
    related_cases: list[dict] = Field(default_factory=list)
    related_entities: list[dict] = Field(default_factory=list)


class EntitySummaryOut(BaseModel):
    total: int
    by_type: dict[str, int]
    by_case: int
    cases_count: int


# ---------------------------------------------------------------------------
# Resolution Candidates
# ---------------------------------------------------------------------------
class ResolutionCandidateOut(BaseModel):
    id: int
    entity_a_id: int
    entity_b_id: int
    entity_type: str
    similarity_score: float
    match_reason: str
    decision: str
    decided_by: Optional[str]
    decided_at: Optional[datetime]
    created_at: datetime
    entity_a_text: Optional[str] = None
    entity_b_text: Optional[str] = None
    entity_a_doc: Optional[str] = None
    entity_b_doc: Optional[str] = None
    entity_a_case: Optional[str] = None
    entity_b_case: Optional[str] = None

    model_config = {"from_attributes": True}


class ResolutionDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    analyst_id: str = "analyst_01"


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
class GraphOut(BaseModel):
    nodes: list[dict]
    edges: list[dict]


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
class CentralityOut(BaseModel):
    node_id: str
    name: str
    entity_type: str
    degree_centrality: float
    betweenness_centrality: float
    source_types: list[str]


class NetworkStatsOut(BaseModel):
    node_count: int
    edge_count: int
    density: float
    top_entities: list[CentralityOut]


# ---------------------------------------------------------------------------
# Communities
# ---------------------------------------------------------------------------
class CommunityMember(BaseModel):
    node_id: str
    name: str
    entity_type: str


class CommunityOut(BaseModel):
    community_id: int
    members: list[CommunityMember]
    member_count: int
    internal_edge_density: float
    source_types: list[str]
    summary: str


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------
class InsightOut(BaseModel):
    id: int
    insight_type: str
    title: str
    explanation: str
    entity_refs: list[Any]
    source_refs: list[Any]
    contributing_source_types: list[str]
    confidence: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------
class ReviewDecision(BaseModel):
    analyst_id: str = "analyst_01"
    decision: str = Field(..., pattern="^(approved|rejected|flagged)$")
    notes: str = ""


class ReviewActionOut(BaseModel):
    id: int
    insight_id: int
    analyst_id: str
    decision: str
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
class ValidationRunOut(BaseModel):
    id: Optional[int] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    notes: str = ""
    extra_metrics: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None

    # Multi-task validation structure
    entity_resolution: Optional[dict[str, Any]] = None
    ner_extraction: Optional[dict[str, Any]] = None
    pattern_detection: Optional[dict[str, Any]] = None
    ml_priority_model: Optional[dict[str, Any]] = None
    dataset_note: Optional[str] = (
        "Prototype validation on synthetic ground-truth dataset. "
        "Not representative of real-world law-enforcement accuracy."
    )
    run_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Sources Summary
# ---------------------------------------------------------------------------
class SourceSummaryItem(BaseModel):
    source_type: str
    document_count: int
    record_count: int


# ---------------------------------------------------------------------------
# Admin / Demo Seeding
# ---------------------------------------------------------------------------
class SeedSummaryOut(BaseModel):
    cases_created: int
    cases_failed: int = 0
    failed_cases: list[dict[str, Any]] = Field(default_factory=list)
    documents_processed: int
    entities_extracted: int
    resolution_candidates_found: int
    graph_nodes: int
    graph_edges: int
    relationships_created: Optional[int] = None
    transactions_created: Optional[int] = None
    communications_created: Optional[int] = None
    message: str
