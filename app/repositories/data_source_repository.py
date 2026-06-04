from datetime import date, datetime
from typing import Iterable

from cassandra.cluster import Session

from app.domain.data_source import DataSource
from app.repositories.base import WarehouseRepository


class DataSourceRepository(WarehouseRepository[DataSource, str]):
    def __init__(self, session: Session):
        self.session = session

    def save(self, entity: DataSource) -> DataSource:
        query = """
        INSERT INTO data_sources_by_id (
            data_source_id,
            system_time,
            name,
            provider_type,
            base_url,
            description,
            attributes,
            is_deleted,
            valid_from,
            valid_to
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        prepared = self.session.prepare(query)
        self.session.execute(
            prepared,
            (
                entity.data_source_id,
                entity.system_time,
                entity.name,
                entity.provider_type,
                entity.base_url,
                entity.description,
                entity.attributes,
                entity.is_deleted,
                entity.valid_from,
                entity.valid_to,
            ),
        )

        return entity

    def find_latest(self, partition_key: str) -> DataSource | None:
        query = """
        SELECT *
        FROM data_sources_by_id
        WHERE data_source_id = ?
        LIMIT 1
        """

        prepared = self.session.prepare(query)
        row = self.session.execute(prepared, (partition_key,)).one()

        if row is None:
            return None

        return self._row_to_data_source(row)

    def find_all(self, partition_key: str) -> Iterable[DataSource]:
        query = """
        SELECT *
        FROM data_sources_by_id
        WHERE data_source_id = ?
        """

        prepared = self.session.prepare(query)
        rows = self.session.execute(prepared, (partition_key,))

        return [self._row_to_data_source(row) for row in rows]

    def find_as_of(self, data_source_id: str, system_time: datetime) -> DataSource | None:
        query = """
        SELECT *
        FROM data_sources_by_id
        WHERE data_source_id = ?
          AND system_time <= ?
        LIMIT 1
        """

        prepared = self.session.prepare(query)
        row = self.session.execute(prepared, (data_source_id, system_time)).one()

        if row is None:
            return None

        return self._row_to_data_source(row)

    def mark_deleted(
        self,
        data_source_id: str,
        system_time: datetime,
        valid_from: date,
    ) -> DataSource:
        latest = self.find_latest(data_source_id)

        if latest is None:
            raise ValueError(f"Data source not found: {data_source_id}")

        deleted_data_source = DataSource(
            data_source_id=latest.data_source_id,
            name=latest.name,
            provider_type=latest.provider_type,
            base_url=latest.base_url,
            description=latest.description,
            system_time=system_time,
            valid_from=valid_from,
            valid_to=None,
            is_deleted=True,
            attributes=latest.attributes,
        )

        return self.save(deleted_data_source)

    @staticmethod
    def _row_to_data_source(row) -> DataSource:
        return DataSource(
            data_source_id=row["data_source_id"],
            name=row["name"],
            provider_type=row["provider_type"],
            base_url=row["base_url"],
            description=row["description"],
            system_time=row["system_time"],
            valid_from=row["valid_from"],
            valid_to=row["valid_to"],
            is_deleted=row["is_deleted"],
            attributes=dict(row["attributes"] or {}),
        )