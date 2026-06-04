from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class TimeSeriesPoint:
    asset_id: str
    data_source_id: str
    business_year: int
    business_date: date
    system_time: datetime
    values_double: dict[str, float] = field(default_factory=dict)
    values_text: dict[str, str] = field(default_factory=dict)
    attributes: dict[str, str] = field(default_factory=dict)
    is_deleted: bool = False
    ingested_at: datetime | None = None