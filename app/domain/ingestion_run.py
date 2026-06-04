from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class IngestionRun:
    run_id: UUID
    provider_id: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    fetched_records: int = 0
    transformed_records: int = 0
    stored_records: int = 0
    skipped_records: int = 0
    failed_records: int = 0
    error_message: str | None = None