# Make ingestion a package; import all adapters to trigger @register_adapter decorators
from app.ingestion import (  # noqa: F401
    fir_adapter,
    cdr_adapter,
    financial_adapter,
    surveillance_adapter,
    social_media_adapter,
    criminal_history_adapter,
    intelligence_report_adapter,
)
