from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class DataSource:
    data_source_id: str
    name: str
    provider_type: str
    base_url: str
    description: str
    system_time: datetime
    valid_from: date
    valid_to: date | None = None
    is_deleted: bool = False
    attributes: dict[str, str] = field(default_factory=dict)