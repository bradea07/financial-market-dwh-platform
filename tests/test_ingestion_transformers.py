from datetime import date, datetime, timezone

import pandas as pd

from app.ingestion.providers.yfinance_provider import ProviderAssetRequest
from app.ingestion.transformers import (
    build_asset,
    build_data_source,
    dataframe_to_time_series_points,
    normalize_business_date,
    safe_float,
)


def test_safe_float_handles_valid_and_invalid_values():
    assert safe_float("10.5") == 10.5
    assert safe_float(12) == 12.0
    assert safe_float(None) is None
    assert safe_float("invalid") is None


def test_normalize_business_date_from_timestamp():
    value = pd.Timestamp("2024-01-02")
    assert normalize_business_date(value) == date(2024, 1, 2)


def test_build_asset_from_provider_request():
    system_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    request = ProviderAssetRequest(
        symbol="AAPL",
        asset_id="AAPL",
        asset_class="stock",
        name="Apple Inc.",
        region="US",
        currency="USD",
        description="Apple stock.",
    )

    asset = build_asset(request=request, system_time=system_time)

    assert asset.asset_id == "AAPL"
    assert asset.symbol == "AAPL"
    assert asset.asset_class == "stock"
    assert asset.attributes["source"] == "YFINANCE"


def test_build_data_source():
    system_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    data_source = build_data_source(system_time=system_time)

    assert data_source.data_source_id == "YFINANCE"
    assert data_source.provider_type == "REST_API"
    assert data_source.attributes["frequency"] == "daily"


def test_dataframe_to_time_series_points():
    system_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    dataframe = pd.DataFrame(
        [
            {
                "Date": pd.Timestamp("2024-01-02"),
                "Open": 100.0,
                "High": 110.0,
                "Low": 95.0,
                "Close": 105.0,
                "Adj Close": 104.0,
                "Volume": 1000000,
                "provider_symbol": "AAPL",
                "asset_id": "AAPL",
            }
        ]
    )

    points = dataframe_to_time_series_points(
        data=dataframe,
        system_time=system_time,
        data_source_id="YFINANCE",
    )

    assert len(points) == 1
    assert points[0].asset_id == "AAPL"
    assert points[0].business_date == date(2024, 1, 2)
    assert points[0].business_year == 2024
    assert points[0].values_double["open"] == 100.0
    assert points[0].values_double["close"] == 105.0