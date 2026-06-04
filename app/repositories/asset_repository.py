from datetime import date, datetime
from typing import Iterable

from cassandra.cluster import Session

from app.domain.asset import Asset
from app.repositories.base import WarehouseRepository


class AssetRepository(WarehouseRepository[Asset, str]):
    def __init__(self, session: Session):
        self.session = session

    def save(self, entity: Asset) -> Asset:
        query = """
        INSERT INTO assets_by_id (
            asset_id,
            system_time,
            symbol,
            asset_class,
            name,
            region,
            currency,
            description,
            attributes,
            is_deleted,
            valid_from,
            valid_to
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        prepared = self.session.prepare(query)
        self.session.execute(
            prepared,
            (
                entity.asset_id,
                entity.system_time,
                entity.symbol,
                entity.asset_class,
                entity.name,
                entity.region,
                entity.currency,
                entity.description,
                entity.attributes,
                entity.is_deleted,
                entity.valid_from,
                entity.valid_to,
            ),
        )

        return entity

    def find_latest(self, partition_key: str) -> Asset | None:
        query = """
        SELECT *
        FROM assets_by_id
        WHERE asset_id = ?
        LIMIT 1
        """

        prepared = self.session.prepare(query)
        row = self.session.execute(prepared, (partition_key,)).one()

        if row is None:
            return None

        return self._row_to_asset(row)

    def find_all(self, partition_key: str) -> Iterable[Asset]:
        query = """
        SELECT *
        FROM assets_by_id
        WHERE asset_id = ?
        """

        prepared = self.session.prepare(query)
        rows = self.session.execute(prepared, (partition_key,))

        return [self._row_to_asset(row) for row in rows]

    def find_as_of(self, asset_id: str, system_time: datetime) -> Asset | None:
        query = """
        SELECT *
        FROM assets_by_id
        WHERE asset_id = ?
          AND system_time <= ?
        LIMIT 1
        """

        prepared = self.session.prepare(query)
        row = self.session.execute(prepared, (asset_id, system_time)).one()

        if row is None:
            return None

        return self._row_to_asset(row)

    def mark_deleted(self, asset_id: str, system_time: datetime, valid_from: date) -> Asset:
        latest = self.find_latest(asset_id)

        if latest is None:
            raise ValueError(f"Asset not found: {asset_id}")

        deleted_asset = Asset(
            asset_id=latest.asset_id,
            symbol=latest.symbol,
            asset_class=latest.asset_class,
            name=latest.name,
            region=latest.region,
            currency=latest.currency,
            description=latest.description,
            system_time=system_time,
            valid_from=valid_from,
            valid_to=None,
            is_deleted=True,
            attributes=latest.attributes,
        )

        return self.save(deleted_asset)

    @staticmethod
    def _row_to_asset(row) -> Asset:
        return Asset(
            asset_id=row["asset_id"],
            symbol=row["symbol"],
            asset_class=row["asset_class"],
            name=row["name"],
            region=row["region"],
            currency=row["currency"],
            description=row["description"],
            system_time=row["system_time"],
            valid_from=row["valid_from"],
            valid_to=row["valid_to"],
            is_deleted=row["is_deleted"],
            attributes=dict(row["attributes"] or {}),
        )