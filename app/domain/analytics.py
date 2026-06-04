from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True)
class YearlySummary:
    asset_id: str
    data_source_id: str
    business_year: int
    generated_at: datetime
    record_count: int
    min_close: float
    max_close: float
    avg_close: float
    avg_volume: float
    yearly_return: float
    volatility: float


@dataclass(frozen=True)
class PricePrediction:
    asset_id: str
    data_source_id: str
    business_date: date
    generated_at: datetime
    actual_close: float
    predicted_close: float
    prediction_error: float
    model_name: str
    features: dict[str, float] = field(default_factory=dict)