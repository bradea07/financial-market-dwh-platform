from datetime import date, datetime, timezone
from math import isnan
from typing import Any

import pandas as pd

from app.domain.asset import Asset
from app.domain.data_source import DataSource
from app.domain.time_series import TimeSeriesPoint
from app.ingestion.providers.yfinance_provider import ProviderAssetRequest, YFinanceProvider


def safe_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    if isnan(numeric_value):
        return None

    return numeric_value


def normalize_business_date(value: Any) -> date:
    if isinstance(value, pd.Timestamp):
        return value.date()

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return pd.to_datetime(value).date()


def build_asset(
    request: ProviderAssetRequest,
    system_time: datetime,
) -> Asset:
    return Asset(
        asset_id=request.asset_id,
        symbol=request.symbol,
        asset_class=request.asset_class,
        name=request.name,
        region=request.region,
        currency=request.currency,
        description=request.description,
        system_time=system_time,
        valid_from=system_time.date(),
        valid_to=None,
        is_deleted=False,
        attributes={
            "provider_symbol": request.symbol,
            "source": YFinanceProvider.data_source_id,
        },
    )


def build_data_source(system_time: datetime) -> DataSource:
    return DataSource(
        data_source_id=YFinanceProvider.data_source_id,
        name=YFinanceProvider.name,
        provider_type=YFinanceProvider.provider_type,
        base_url=YFinanceProvider.base_url,
        description="Yahoo Finance market data accessed through the yfinance Python library.",
        system_time=system_time,
        valid_from=system_time.date(),
        valid_to=None,
        is_deleted=False,
        attributes={
            "library": "yfinance",
            "frequency": "daily",
            "data_shape": "OHLCV",
        },
    )


def row_to_time_series_point(
    row: pd.Series,
    system_time: datetime,
    data_source_id: str,
) -> TimeSeriesPoint:
    business_date = normalize_business_date(row["Date"])

    values_double = {}

    column_mapping = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adjusted_close",
        "Volume": "volume",
        "Dividends": "dividends",
        "Stock Splits": "stock_splits",
    }

    for source_column, target_name in column_mapping.items():
        if source_column in row:
            value = safe_float(row[source_column])
            if value is not None:
                values_double[target_name] = value

    return TimeSeriesPoint(
        asset_id=str(row["asset_id"]),
        data_source_id=data_source_id,
        business_year=business_date.year,
        business_date=business_date,
        system_time=system_time,
        values_double=values_double,
        values_text={
            "provider_symbol": str(row["provider_symbol"]),
        },
        attributes={
            "frequency": "daily",
            "provider": data_source_id,
        },
        is_deleted=False,
        ingested_at=system_time,
    )


def dataframe_to_time_series_points(
    data: pd.DataFrame,
    system_time: datetime | None = None,
    data_source_id: str = YFinanceProvider.data_source_id,
) -> list[TimeSeriesPoint]:
    if system_time is None:
        system_time = datetime.now(timezone.utc)

    points = []

    for _, row in data.iterrows():
        points.append(
            row_to_time_series_point(
                row=row,
                system_time=system_time,
                data_source_id=data_source_id,
            )
        )

    return points