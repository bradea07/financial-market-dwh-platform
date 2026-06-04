from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.db.cassandra import get_session
from app.repositories.time_series_repository import TimeSeriesRepository


router = APIRouter(prefix="/data", tags=["time-series"])


@router.get("")
def get_time_series_data(
    asset_id: str = Query(alias="assetId"),
    data_source_id: str = Query(alias="dataSourceId"),
    start_business_date: date = Query(alias="startBusinessDate"),
    end_business_date: date = Query(alias="endBusinessDate"),
    include_attributes: bool = Query(default=False, alias="includeAttributes"),
):
    if end_business_date <= start_business_date:
        raise HTTPException(
            status_code=400,
            detail="endBusinessDate must be greater than startBusinessDate",
        )

    session = get_session()

    try:
        repository = TimeSeriesRepository(session)

        records = []
        current_year = start_business_date.year
        end_year = end_business_date.year

        while current_year <= end_year:
            year_start = max(start_business_date, date(current_year, 1, 1))
            year_end = min(end_business_date, date(current_year + 1, 1, 1))

            if year_start < year_end:
                year_records = repository.find_range_latest_versions(
                    asset_id=asset_id,
                    data_source_id=data_source_id,
                    business_year=current_year,
                    start_business_date=year_start,
                    end_business_date=year_end,
                )
                records.extend(year_records)

            current_year += 1

        records = sorted(records, key=lambda item: item.business_date, reverse=True)

        response_records = []

        for point in records:
            item = {
    "businessDate": str(point.business_date),
    "systemTime": point.system_time.isoformat(),
    "valuesDouble": point.values_double,
    "valuesText": point.values_text,
    "isDeleted": point.is_deleted,
}

            if include_attributes:
                item["attributes"] = point.attributes

            response_records.append(item)

        return {
            "assetId": asset_id,
            "dataSourceId": data_source_id,
            "startBusinessDate": start_business_date,
            "endBusinessDate": end_business_date,
            "recordsReturned": len(response_records),
            "records": response_records,
        }
    finally:
        session.shutdown()