from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class Asset:
    asset_id: str
    symbol: str
    asset_class: str
    name: str
    region: str
    currency: str
    description: str
    system_time: datetime
    valid_from: date
    valid_to: date | None = None
    is_deleted: bool = False
    attributes: dict[str, str] = field(default_factory=dict)