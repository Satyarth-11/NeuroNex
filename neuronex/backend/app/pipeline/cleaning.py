"""
NeuroNex — Data Cleaning & Normalisation Pipeline
Normalises text before NER, and normalises structured fields (phone numbers,
names, account numbers) before entity resolution.
"""
from __future__ import annotations
import re
import unicodedata
from app.ingestion.base import InvestigationRecord


# ---------------------------------------------------------------------------
# Phone normalisation — strip spaces/dashes, ensure +91 prefix for Indian numbers
# ---------------------------------------------------------------------------
_FORMAT_CHARS_RE = re.compile(r"[\s\-\(\)\.]")


def normalise_phone(phone: str) -> str:
    """Strip formatting; prepend +91 for ANY recognizable 10-digit Indian mobile."""
    cleaned = _FORMAT_CHARS_RE.sub("", phone).strip()
    cleaned = re.sub(r"^\+?91", "", cleaned)  # strip any existing 91/+91 prefix
    if re.match(r"^[6-9]\d{9}$", cleaned):
        return f"+91{cleaned}"
    return cleaned  # not a recognized Indian mobile shape — return as-is


# ---------------------------------------------------------------------------
# Name, Organisation & Location normalisation — strip titles, trailing punctuation
# ---------------------------------------------------------------------------
_TITLES = re.compile(
    r"\b(Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Shri\.?|Smt\.?|Sri\.?|Er\.?|Prof\.?)\b",
    re.IGNORECASE,
)


def normalise_name(name: str) -> str:
    """Remove honorifics, collapse whitespace, strip trailing punctuation, title-case."""
    name = _TITLES.sub("", name)
    name = " ".join(name.split())
    name = re.sub(r"[.\s]+$", "", name)
    return name.strip().title()


def normalise_organisation(org: str) -> str:
    """Clean organisation name, collapse whitespace, strip trailing punctuation."""
    org = " ".join(org.split())
    org = re.sub(r"[.\s]+$", "", org)
    return org.strip()


def normalise_location(loc: str) -> str:
    """Clean location name, collapse whitespace, strip trailing punctuation."""
    loc = " ".join(loc.split())
    loc = re.sub(r"[.\s]+$", "", loc)
    return loc.strip()


# ---------------------------------------------------------------------------
# Account number normalisation — strip spaces and dashes
# ---------------------------------------------------------------------------
def normalise_account(account: str) -> str:
    return re.sub(r"[\s\-]", "", account).upper()


# ---------------------------------------------------------------------------
# General text cleaning — unicode normalisation, strip noise
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """
    1. Normalise unicode to NFC
    2. Replace non-breaking spaces / control chars with regular space
    3. Collapse multiple spaces/newlines
    4. Strip leading/trailing whitespace
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\xa0]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Vehicle registration normalisation (Indian format: MH01AB1234 etc.)
# ---------------------------------------------------------------------------
def normalise_vehicle_reg(reg: str) -> str:
    return re.sub(r"[\s\-]", "", reg).upper()


# ---------------------------------------------------------------------------
# Main entry point: clean an InvestigationRecord in-place (returns new record)
# ---------------------------------------------------------------------------
def clean_record(record: InvestigationRecord) -> InvestigationRecord:
    """Return a cleaned copy of the record."""
    cleaned_text = clean_text(record.raw_text)

    # Normalise phone numbers found in raw_fields
    raw_fields = dict(record.raw_fields)
    for key in ("caller_number", "callee_number", "phone", "mobile"):
        if key in raw_fields:
            raw_fields[key] = normalise_phone(raw_fields[key])

    # Normalise account numbers
    for key in ("sender_account", "receiver_account", "account"):
        if key in raw_fields:
            raw_fields[key] = normalise_account(raw_fields[key])

    # Normalise vehicle registrations
    for key in ("vehicle_reg", "vehicle_number", "registration"):
        if key in raw_fields:
            raw_fields[key] = normalise_vehicle_reg(raw_fields[key])

    # Return new record with cleaned data
    from dataclasses import replace
    return replace(record, raw_text=cleaned_text, raw_fields=raw_fields)
