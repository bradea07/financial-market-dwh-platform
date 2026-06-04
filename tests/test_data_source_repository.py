from datetime import date, datetime, timezone

from app.db.cassandra import get_session
from app.domain.data_source import DataSource
from app.repositories.data_source_repository import DataSourceRepository


def test_data_source_repository_save_find_latest_find_all():
    session = get_session()
    repository = DataSourceRepository(session)

    now = datetime.now(timezone.utc)
    data_source_id = f"TEST_SOURCE_{int(now.timestamp())}"

    data_source = DataSource(
        data_source_id=data_source_id,
        name="Yahoo Finance",
        provider_type="REST_API",
        base_url="https://query1.finance.yahoo.com",
        description="Unit test data source.",
        system_time=now,
        valid_from=date.today(),
        valid_to=None,
        is_deleted=False,
        attributes={"library": "yfinance"},
    )

    repository.save(data_source)

    latest = repository.find_latest(data_source_id)
    all_versions = list(repository.find_all(data_source_id))

    session.shutdown()

    assert latest is not None
    assert latest.data_source_id == data_source_id
    assert latest.name == "Yahoo Finance"
    assert len(all_versions) >= 1