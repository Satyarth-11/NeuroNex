"""
NeuroNex — Social Media Intelligence Adapter (SYNTHETIC DATA ONLY)
Parses CSV with columns:
    post_id, platform, handle, display_name, post_text, timestamp,
    mentioned_handles (semicolon-separated)
NER runs on post_text; mention edges are built structurally from mentioned_handles.
"""
from __future__ import annotations
import csv
import io
from app.ingestion.base import BaseAdapter, InvestigationRecord, register_adapter


@register_adapter
class SocialMediaAdapter(BaseAdapter):
    source_type = "social_media"

    def parse(self, file_bytes: bytes) -> list[InvestigationRecord]:
        records: list[InvestigationRecord] = []
        text = file_bytes.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))

        for row in reader:
            post_id = row.get("post_id", "").strip()
            handle = row.get("handle", "").strip()
            display_name = row.get("display_name", "").strip()
            post_text = row.get("post_text", "").strip()
            mentions = row.get("mentioned_handles", "").strip()

            # Rich text for NER: include display name so person entities resolve correctly
            raw_text = (
                f"{display_name} (@{handle}) on {row.get('platform', '')}: "
                f"{post_text} "
                f"[mentions: {mentions}]"
            )

            records.append(
                InvestigationRecord.create(
                    source_type=self.source_type,
                    raw_text=raw_text,
                    raw_fields=dict(row),
                    timestamp=row.get("timestamp"),
                    doc_label=f"Post {post_id} @{handle}",
                )
            )
        return records
