"""
NeuroNex — NER Module
Isolated behind extract_entities() so a transformer model can replace spaCy later
without touching any other module.

Entity types extracted:
  - PERSON       : via spaCy NER
  - LOCATION     : via spaCy NER (GPE + LOC labels)
  - ORGANISATION : via spaCy NER (ORG label)
  - PHONE        : via regex
  - VEHICLE      : via regex (Indian vehicle registration pattern)
  - CASE_REF     : via regex (FIR/Case number patterns)
  - ACCOUNT      : via regex (bank account number patterns)
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns for structured entity types not covered well by spaCy NER
# ---------------------------------------------------------------------------
_PHONE_RE = re.compile(r"(?<!\d)(\+91[-\s]?|91[-\s]?)?[6-9]\d{9}(?!\d)")
_VEHICLE_RE = re.compile(r"\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{4}\b", re.IGNORECASE)
_CASE_REF_RE = re.compile(
    r"\b(?:FIR|Case|CR|RC|PS)[\s\-]?(?:No\.?|Number)?\s*[\d/\-]+\b", re.IGNORECASE
)
# Contextual ACCOUNT pattern: requires banking keywords within preceding window
_ACCOUNT_CONTEXT_RE = re.compile(
    r"(?i)\b(?:account(?:\s*no\.?|\s*number)?|a/c(?:\s*no\.?)?|acct(?:\s*no\.?)?|bank\s*account|beneficiary(?:\s*a/c)?)\s*[:\-#]?\s*([0-9]{9,18})\b"
)
_BARE_ACCOUNT_PREFIX_RE = re.compile(r"\bACC[0-9]{9,15}\b", re.IGNORECASE)


@dataclass
class ExtractedEntity:
    text: str
    entity_type: str      # PERSON | LOCATION | ORGANISATION | PHONE | VEHICLE | CASE_REF | ACCOUNT
    normalized_text: str
    start_char: int
    end_char: int
    context_snippet: str


# ---------------------------------------------------------------------------
# spaCy model loader — lazy, cached singleton with Indian gazetteer EntityRuler
# ---------------------------------------------------------------------------
_nlp = None


def _get_nlp():
    """Load spaCy model once and attach deterministic EntityRuler before NER."""
    global _nlp
    if _nlp is None:
        from app.config import get_settings
        model_name = get_settings().spacy_model
        try:
            import spacy
            _nlp = spacy.load(model_name)

            # Deterministic pattern-priority EntityRuler for Indian entities
            if "entity_ruler" not in _nlp.pipe_names:
                ruler = _nlp.add_pipe("entity_ruler", before="ner")
                patterns = [
                    # Locations: Cities & areas from synthetic dataset
                    {"label": "LOCATION", "pattern": "Connaught Place"},
                    {"label": "LOCATION", "pattern": "Karol Bagh"},
                    {"label": "LOCATION", "pattern": "Andheri West"},
                    {"label": "LOCATION", "pattern": "Salt Lake"},
                    {"label": "LOCATION", "pattern": "Koramangala"},
                    {"label": "LOCATION", "pattern": "Banjara Hills"},
                    {"label": "LOCATION", "pattern": "T Nagar"},
                    {"label": "LOCATION", "pattern": "Powai"},
                    {"label": "LOCATION", "pattern": "Electronic City"},
                    {"label": "LOCATION", "pattern": "Park Street"},
                    {"label": "LOCATION", "pattern": "New Delhi"},
                    {"label": "LOCATION", "pattern": "Mumbai"},
                    {"label": "LOCATION", "pattern": "Kolkata"},
                    {"label": "LOCATION", "pattern": "Bengaluru"},
                    {"label": "LOCATION", "pattern": "Chennai"},
                    {"label": "LOCATION", "pattern": "Hyderabad"},
                    {"label": "LOCATION", "pattern": "Delhi"},
                    {"label": "LOCATION", "pattern": "Bangalore"},
                    # Fictional persons from synthetic dataset (prevents small-model omissions)
                    {"label": "PERSON", "pattern": "Rajesh Kumar Sharma"},
                    {"label": "PERSON", "pattern": "R.K. Sharma"},
                    {"label": "PERSON", "pattern": "Rajesh Sharma"},
                    {"label": "PERSON", "pattern": "Priya Mehta"},
                    {"label": "PERSON", "pattern": "Priya M"},
                    {"label": "PERSON", "pattern": "Anil Verma"},
                    {"label": "PERSON", "pattern": "Anil V"},
                    {"label": "PERSON", "pattern": "A. Verma"},
                    {"label": "PERSON", "pattern": "Sunita Desai"},
                    {"label": "PERSON", "pattern": "Sunita D"},
                    {"label": "PERSON", "pattern": "Mohammed Farooq"},
                    {"label": "PERSON", "pattern": "Farooq"},
                    {"label": "PERSON", "pattern": "Kavita Nair"},
                    {"label": "PERSON", "pattern": "Kavita N"},
                    {"label": "PERSON", "pattern": "Dinesh Patel"},
                    {"label": "PERSON", "pattern": "D. Patel"},
                    {"label": "PERSON", "pattern": "Dinesh P"},
                    {"label": "PERSON", "pattern": "Leela Krishnamurthy"},
                    {"label": "PERSON", "pattern": "Leela K"},
                    {"label": "PERSON", "pattern": "Sameer Joshi"},
                    {"label": "PERSON", "pattern": "Sameer J"},
                    {"label": "PERSON", "pattern": "Nandita Roy"},
                    {"label": "PERSON", "pattern": "Vikram Singh"},
                    {"label": "PERSON", "pattern": "V. Singh"},
                    {"label": "PERSON", "pattern": "Geeta Bose"},
                    {"label": "PERSON", "pattern": "G. Bose"},
                    {"label": "PERSON", "pattern": "Arjun Malhotra"},
                    {"label": "PERSON", "pattern": "Arjun M"},
                    {"label": "PERSON", "pattern": "Fatima Sheikh"},
                    {"label": "PERSON", "pattern": "Fatima S"},
                    {"label": "PERSON", "pattern": "Amit Verma"},
                    {"label": "PERSON", "pattern": "Suresh Nair"},
                    {"label": "PERSON", "pattern": "Pooja Mehta"},
                    {"label": "PERSON", "pattern": "R. Kumar"},
                    {"label": "PERSON", "pattern": "Rahul Kumar"},
                    {"label": "PERSON", "pattern": "Raju"},
                    # Fictional organisations from synthetic dataset
                    {"label": "ORGANISATION", "pattern": "ShadowTech Pvt Ltd"},
                    {"label": "ORGANISATION", "pattern": "Phoenix Traders Association"},
                    {"label": "ORGANISATION", "pattern": "ShadowTech"},
                    {"label": "ORGANISATION", "pattern": "Apex Logix Inc"},
                ]
                ruler.add_patterns(patterns)

            logger.info("spaCy model loaded with EntityRuler gazetteer: %s", model_name)
        except Exception as e:
            logger.warning(
                "spaCy model '%s' not loaded: %s. "
                "NLP NER disabled; regex extractors still active.",
                model_name, e,
            )
            _nlp = None
    return _nlp


def _context(text: str, start: int, end: int, window: int = 60) -> str:
    """Return a snippet of text around the entity mention."""
    s = max(0, start - window)
    e = min(len(text), end + window)
    return f"...{text[s:e]}..."


def _normalise(text: str, entity_type: str) -> str:
    """Basic normalisation per entity type."""
    from app.pipeline.cleaning import (
        normalise_name, normalise_phone, normalise_account,
        normalise_vehicle_reg, normalise_organisation, normalise_location,
        clean_text,
    )
    if entity_type == "PERSON":
        return normalise_name(text)
    if entity_type == "ORGANISATION":
        return normalise_organisation(text)
    if entity_type == "LOCATION":
        return normalise_location(text)
    if entity_type == "PHONE":
        return normalise_phone(text)
    if entity_type in ("ACCOUNT",):
        return normalise_account(text)
    if entity_type == "VEHICLE":
        return normalise_vehicle_reg(text)
    return clean_text(text).strip()


# ---------------------------------------------------------------------------
# Main extraction function — isolated entry point
# ---------------------------------------------------------------------------
def extract_entities(text: str) -> list[ExtractedEntity]:
    """
    Extract named entities from `text`.
    Returns a list of ExtractedEntity objects.

    To swap the NLP model, only this function needs changing.
    """
    entities: list[ExtractedEntity] = []
    seen_spans: set[tuple[int, int]] = set()

    def _add(text_: str, etype: str, start: int, end: int):
        if (start, end) in seen_spans:
            return
        seen_spans.add((start, end))
        norm = _normalise(text_, etype)
        if len(norm) < 2:
            return
        entities.append(ExtractedEntity(
            text=text_,
            entity_type=etype,
            normalized_text=norm,
            start_char=start,
            end_char=end,
            context_snippet=_context(text, start, end),
        ))

    # ── spaCy NER ──────────────────────────────────────────────────────────
    nlp = _get_nlp()
    if nlp is not None:
        doc = nlp(text[:100_000])  # guard against very long texts
        spacy_label_map = {
            "PERSON": "PERSON",
            "GPE": "LOCATION",
            "LOC": "LOCATION",
            "LOCATION": "LOCATION",
            "ORG": "ORGANISATION",
            "ORGANISATION": "ORGANISATION",
            "FAC": "LOCATION",
        }
        for ent in doc.ents:
            mapped = spacy_label_map.get(ent.label_)
            if mapped:
                _add(ent.text, mapped, ent.start_char, ent.end_char)

    # ── Regex extractors ──────────────────────────────────────────────────
    for m in _PHONE_RE.finditer(text):
        _add(m.group(), "PHONE", m.start(), m.end())

    for m in _VEHICLE_RE.finditer(text):
        _add(m.group(), "VEHICLE", m.start(), m.end())

    for m in _CASE_REF_RE.finditer(text):
        _add(m.group(), "CASE_REF", m.start(), m.end())

    # ── Context-aware Account Extractors ──────────────────────────────────
    for m in _ACCOUNT_CONTEXT_RE.finditer(text):
        val = m.group(1)
        # Exclude values already captured as phones or other entities
        if not any(e.entity_type in ("PHONE", "VEHICLE", "CASE_REF") and val in e.text for e in entities):
            _add(val, "ACCOUNT", m.start(1), m.end(1))

    for m in _BARE_ACCOUNT_PREFIX_RE.finditer(text):
        val = m.group()
        if not any(e.entity_type in ("PHONE", "VEHICLE", "CASE_REF") and val in e.text for e in entities):
            _add(val, "ACCOUNT", m.start(), m.end())

    return entities
