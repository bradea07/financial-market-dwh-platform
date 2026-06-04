from typing import Iterable

from cassandra.cluster import Session

from app.domain.ingestion_run import IngestionRun
from app.repositories.base import WarehouseRepository


class IngestionRunRepository(WarehouseRepository[IngestionRun, str]):
    def __init__(self, session: Session):
        self.session = session

    def save(self, entity: IngestionRun) -> IngestionRun:
        query = """
        INSERT INTO ingestion_runs (
            run_id,
            provider_id,
            started_at,
            finished_at,
            status,
            fetched_records,
            transformed_records,
            stored_records,
            skipped_records,
            failed_records,
            error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        prepared = self.session.prepare(query)
        self.session.execute(
            prepared,
            (
                entity.run_id,
                entity.provider_id,
                entity.started_at,
                entity.finished_at,
                entity.status,
                entity.fetched_records,
                entity.transformed_records,
                entity.stored_records,
                entity.skipped_records,
                entity.failed_records,
                entity.error_message,
            ),
        )

        return entity

    def find_latest(self, partition_key: str) -> IngestionRun | None:
        query = """
        SELECT *
        FROM ingestion_runs
        WHERE provider_id = ?
        LIMIT 1
        """

        prepared = self.session.prepare(query)
        row = self.session.execute(prepared, (partition_key,)).one()

        if row is None:
            return None

        return self._row_to_ingestion_run(row)

    def find_all(self, partition_key: str) -> Iterable[IngestionRun]:
        query = """
        SELECT *
        FROM ingestion_runs
        WHERE provider_id = ?
        """

        prepared = self.session.prepare(query)
        rows = self.session.execute(prepared, (partition_key,))

        return [self._row_to_ingestion_run(row) for row in rows]

    @staticmethod
    def _row_to_ingestion_run(row) -> IngestionRun:
        return IngestionRun(
            run_id=row["run_id"],
            provider_id=row["provider_id"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            status=row["status"],
            fetched_records=row["fetched_records"],
            transformed_records=row["transformed_records"],
            stored_records=row["stored_records"],
            skipped_records=row["skipped_records"],
            failed_records=row["failed_records"],
            error_message=row["error_message"],
        )