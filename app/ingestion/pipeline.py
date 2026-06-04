from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import uuid4

from app.db.cassandra import get_session
from app.domain.ingestion_run import IngestionRun
from app.ingestion.providers.yfinance_provider import ProviderAssetRequest, YFinanceProvider
from app.ingestion.transformers import (
    build_asset,
    build_data_source,
    dataframe_to_time_series_points,
)
from app.repositories.asset_repository import AssetRepository
from app.repositories.data_source_repository import DataSourceRepository
from app.repositories.ingestion_run_repository import IngestionRunRepository
from app.repositories.time_series_repository import TimeSeriesRepository


@dataclass(frozen=True)
class IngestionResult:
    provider_id: str
    fetched_records: int
    transformed_records: int
    stored_records: int
    skipped_records: int
    failed_records: int


class YFinanceIngestionPipeline:
    def __init__(self):
        self.provider = YFinanceProvider()

    def run(
        self,
        asset_requests: list[ProviderAssetRequest],
        start_date: date,
        end_date: date,
    ) -> IngestionResult:
        session = get_session()

        asset_repository = AssetRepository(session)
        data_source_repository = DataSourceRepository(session)
        time_series_repository = TimeSeriesRepository(session)
        ingestion_run_repository = IngestionRunRepository(session)

        started_at = datetime.now(timezone.utc)

        fetched_records = 0
        transformed_records = 0
        stored_records = 0
        skipped_records = 0
        failed_records = 0
        error_message = None
        status = "SUCCESS"

        try:
            data_source = build_data_source(system_time=started_at)
            data_source_repository.save(data_source)

            for request in asset_requests:
                asset = build_asset(request=request, system_time=started_at)
                asset_repository.save(asset)

                data = self.provider.fetch_history(
                    request=request,
                    start_date=start_date,
                    end_date=end_date,
                )

                fetched_records += len(data)

                if data.empty:
                    skipped_records += 1
                    continue

                points = dataframe_to_time_series_points(
                    data=data,
                    system_time=started_at,
                    data_source_id=self.provider.data_source_id,
                )

                transformed_records += len(points)

                for point in points:
                    time_series_repository.save(point)
                    stored_records += 1

        except Exception as exc:
            status = "FAILED"
            error_message = str(exc)
            failed_records += 1
            raise

        finally:
            finished_at = datetime.now(timezone.utc)

            ingestion_run = IngestionRun(
                run_id=uuid4(),
                provider_id=self.provider.data_source_id,
                started_at=started_at,
                finished_at=finished_at,
                status=status,
                fetched_records=fetched_records,
                transformed_records=transformed_records,
                stored_records=stored_records,
                skipped_records=skipped_records,
                failed_records=failed_records,
                error_message=error_message,
            )

            ingestion_run_repository.save(ingestion_run)
            session.shutdown()

        return IngestionResult(
            provider_id=self.provider.data_source_id,
            fetched_records=fetched_records,
            transformed_records=transformed_records,
            stored_records=stored_records,
            skipped_records=skipped_records,
            failed_records=failed_records,
        )