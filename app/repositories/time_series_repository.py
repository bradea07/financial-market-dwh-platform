from datetime import date, datetime
from typing import Iterable

from cassandra.cluster import Session

from app.domain.time_series import TimeSeriesPoint
from app.repositories.base import WarehouseRepository


TimeSeriesKey = tuple[str, str, int]


class TimeSeriesRepository(WarehouseRepository[TimeSeriesPoint, TimeSeriesKey]):
    def __init__(self, session: Session):
        self.session = session

    def save(self, entity: TimeSeriesPoint) -> TimeSeriesPoint:
        query = """
        INSERT INTO time_series_by_asset_source_year (
            asset_id,
            data_source_id,
            business_year,
            business_date,
            system_time,
            values_double,
            values_text,
            attributes,
            is_deleted,
            ingested_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        prepared = self.session.prepare(query)
        self.session.execute(
            prepared,
            (
                entity.asset_id,
                entity.data_source_id,
                entity.business_year,
                entity.business_date,
                entity.system_time,
                entity.values_double,
                entity.values_text,
                entity.attributes,
                entity.is_deleted,
                entity.ingested_at,
            ),
        )

        return entity

    def find_latest(self, partition_key: TimeSeriesKey) -> TimeSeriesPoint | None:
        asset_id, data_source_id, business_year = partition_key

        query = """
        SELECT *
        FROM time_series_by_asset_source_year
        WHERE asset_id = ?
          AND data_source_id = ?
          AND business_year = ?
        LIMIT 1
        """

        prepared = self.session.prepare(query)
        row = self.session.execute(
            prepared,
            (asset_id, data_source_id, business_year),
        ).one()

        if row is None:
            return None

        return self._row_to_time_series_point(row)

    def find_all(self, partition_key: TimeSeriesKey) -> Iterable[TimeSeriesPoint]:
        asset_id, data_source_id, business_year = partition_key

        query = """
        SELECT *
        FROM time_series_by_asset_source_year
        WHERE asset_id = ?
          AND data_source_id = ?
          AND business_year = ?
        """

        prepared = self.session.prepare(query)
        rows = self.session.execute(
            prepared,
            (asset_id, data_source_id, business_year),
        )

        return [self._row_to_time_series_point(row) for row in rows]

    def find_range_latest_versions(
        self,
        asset_id: str,
        data_source_id: str,
        business_year: int,
        start_business_date: date,
        end_business_date: date,
    ) -> list[TimeSeriesPoint]:
        query = """
        SELECT *
        FROM time_series_by_asset_source_year
        WHERE asset_id = ?
          AND data_source_id = ?
          AND business_year = ?
          AND business_date >= ?
          AND business_date < ?
        """

        prepared = self.session.prepare(query)
        rows = self.session.execute(
            prepared,
            (
                asset_id,
                data_source_id,
                business_year,
                start_business_date,
                end_business_date,
            ),
        )

        latest_by_business_date: dict[date, TimeSeriesPoint] = {}

        for row in rows:
            point = self._row_to_time_series_point(row)

            if point.business_date not in latest_by_business_date:
                latest_by_business_date[point.business_date] = point

        return list(latest_by_business_date.values())

    def mark_deleted(
        self,
        asset_id: str,
        data_source_id: str,
        business_date: date,
        system_time: datetime,
    ) -> TimeSeriesPoint:
        deleted_point = TimeSeriesPoint(
            asset_id=asset_id,
            data_source_id=data_source_id,
            business_year=business_date.year,
            business_date=business_date,
            system_time=system_time,
            values_double={},
            values_text={},
            attributes={"deleted": "true"},
            is_deleted=True,
            ingested_at=system_time,
        )

        return self.save(deleted_point)

    @staticmethod
    def _row_to_time_series_point(row) -> TimeSeriesPoint:
        return TimeSeriesPoint(
            asset_id=row["asset_id"],
            data_source_id=row["data_source_id"],
            business_year=row["business_year"],
            business_date=row["business_date"],
            system_time=row["system_time"],
            values_double=dict(row["values_double"] or {}),
            values_text=dict(row["values_text"] or {}),
            attributes=dict(row["attributes"] or {}),
            is_deleted=row["is_deleted"],
            ingested_at=row["ingested_at"],
        )