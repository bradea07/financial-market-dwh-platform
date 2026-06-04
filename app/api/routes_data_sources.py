from fastapi import APIRouter, HTTPException, Query

from app.db.cassandra import get_session
from app.repositories.data_source_repository import DataSourceRepository


router = APIRouter(prefix="/data-sources", tags=["data-sources"])


@router.get("")
def list_data_sources(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    session = get_session()

    try:
        rows = session.execute(
            """
            SELECT data_source_id, name, provider_type, base_url
            FROM data_sources_by_id
            """
        )

        latest_by_source = {}

        for row in rows:
            data_source_id = row["data_source_id"]

            if data_source_id not in latest_by_source:
                latest_by_source[data_source_id] = {
                    "data_source_id": row["data_source_id"],
                    "name": row["name"],
                    "provider_type": row["provider_type"],
                    "base_url": row["base_url"],
                }

        items = sorted(latest_by_source.values(), key=lambda item: item["data_source_id"])
        page = items[offset : offset + limit]

        return {
            "offset": offset,
            "limit": limit,
            "total": len(items),
            "items": page,
        }
    finally:
        session.shutdown()


@router.get("/{data_source_id}")
def get_data_source(data_source_id: str):
    session = get_session()

    try:
        repository = DataSourceRepository(session)
        data_source = repository.find_latest(data_source_id)

        if data_source is None:
            raise HTTPException(
                status_code=404,
                detail=f"Data source not found: {data_source_id}",
            )

        return {
            "data_source_id": data_source.data_source_id,
            "name": data_source.name,
            "provider_type": data_source.provider_type,
            "base_url": data_source.base_url,
            "description": data_source.description,
            "system_time": data_source.system_time,
            "valid_from": data_source.valid_from,
            "valid_to": data_source.valid_to,
            "is_deleted": data_source.is_deleted,
            "attributes": data_source.attributes,
        }
    finally:
        session.shutdown()