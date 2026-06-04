from datetime import date, datetime, timezone

from app.db.cassandra import get_session
from app.domain.asset import Asset
from app.repositories.asset_repository import AssetRepository


def test_asset_repository_save_find_latest_find_all():
    session = get_session()
    repository = AssetRepository(session)

    now = datetime.now(timezone.utc)
    asset_id = f"TEST_ASSET_{int(now.timestamp())}"

    asset = Asset(
        asset_id=asset_id,
        symbol="AAPL",
        asset_class="stock",
        name="Apple Inc.",
        region="US",
        currency="USD",
        description="Unit test asset.",
        system_time=now,
        valid_from=date.today(),
        valid_to=None,
        is_deleted=False,
        attributes={"exchange": "NASDAQ"},
    )

    repository.save(asset)

    latest = repository.find_latest(asset_id)
    all_versions = list(repository.find_all(asset_id))

    session.shutdown()

    assert latest is not None
    assert latest.asset_id == asset_id
    assert latest.symbol == "AAPL"
    assert len(all_versions) >= 1