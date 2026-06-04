from datetime import date, datetime, timezone

from app.db.cassandra import get_session
from app.domain.time_series import TimeSeriesPoint
from app.repositories.time_series_repository import TimeSeriesRepository


def test_time_series_repository_save_find_latest_find_all_and_range():
    session = get_session()
    repository = TimeSeriesRepository(session)

    now = datetime.now(timezone.utc)
    business_date = date.today()

    asset_id = f"TEST_ASSET_{int(now.timestamp())}"
    data_source_id = "TEST_SOURCE_YFINANCE"

    point = TimeSeriesPoint(
        asset_id=asset_id,
        data_source_id=data_source_id,
        business_year=business_date.year,
        business_date=business_date,
        system_time=now,
        values_double={
            "open": 190.0,
            "high": 195.0,
            "low": 188.5,
            "close": 193.2,
            "volume": 1000000.0,
        },
        values_text={"currency": "USD"},
        attributes={"frequency": "daily"},
        is_deleted=False,
        ingested_at=now,
    )

    repository.save(point)

    latest = repository.find_latest((asset_id, data_source_id, business_date.year))
    all_points = list(repository.find_all((asset_id, data_source_id, business_date.year)))

    range_points = repository.find_range_latest_versions(
        asset_id=asset_id,
        data_source_id=data_source_id,
        business_year=business_date.year,
        start_business_date=date(business_date.year, 1, 1),
        end_business_date=date(business_date.year + 1, 1, 1),
    )

    session.shutdown()

    assert latest is not None
    assert latest.asset_id == asset_id
    assert latest.values_double["close"] == 193.2
    assert len(all_points) >= 1
    assert len(range_points) >= 1