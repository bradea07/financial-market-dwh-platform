from fastapi import APIRouter, HTTPException, Query

from app.db.cassandra import get_session
from app.repositories.asset_repository import AssetRepository


router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("")
def list_assets(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    session = get_session()

    try:
        rows = session.execute(
            """
            SELECT asset_id, symbol, asset_class, name, region, currency
            FROM assets_by_id
            """
        )

        latest_by_asset = {}

        for row in rows:
            asset_id = row["asset_id"]

            if asset_id not in latest_by_asset:
                latest_by_asset[asset_id] = {
                    "asset_id": row["asset_id"],
                    "symbol": row["symbol"],
                    "asset_class": row["asset_class"],
                    "name": row["name"],
                    "region": row["region"],
                    "currency": row["currency"],
                }

        items = sorted(latest_by_asset.values(), key=lambda item: item["asset_id"])
        page = items[offset : offset + limit]

        return {
            "offset": offset,
            "limit": limit,
            "total": len(items),
            "items": page,
        }
    finally:
        session.shutdown()


@router.get("/{asset_id}")
def get_asset(asset_id: str):
    session = get_session()

    try:
        repository = AssetRepository(session)
        asset = repository.find_latest(asset_id)

        if asset is None:
            raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")

        return {
            "asset_id": asset.asset_id,
            "symbol": asset.symbol,
            "asset_class": asset.asset_class,
            "name": asset.name,
            "region": asset.region,
            "currency": asset.currency,
            "description": asset.description,
            "system_time": asset.system_time,
            "valid_from": asset.valid_from,
            "valid_to": asset.valid_to,
            "is_deleted": asset.is_deleted,
            "attributes": asset.attributes,
        }
    finally:
        session.shutdown()