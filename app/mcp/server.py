from datetime import date

from mcp.server.fastmcp import FastMCP

from app.db.cassandra import get_session
from app.repositories.asset_repository import AssetRepository
from app.repositories.data_source_repository import DataSourceRepository
from app.repositories.time_series_repository import TimeSeriesRepository


mcp = FastMCP("Financial Markets Data Warehouse")


@mcp.tool()
def list_assets(offset: int = 0, limit: int = 20) -> dict:
    """
    Return a paginated list of financial assets stored in the warehouse.
    """
    if offset < 0:
        raise ValueError("offset must be >= 0")

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

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

        return {
            "offset": offset,
            "limit": limit,
            "total": len(items),
            "items": items[offset: offset + limit],
        }
    finally:
        session.shutdown()


@mcp.tool()
def get_asset_details(asset_id: str) -> dict:
    """
    Return the latest known version of one financial asset.
    """
    session = get_session()

    try:
        repository = AssetRepository(session)
        asset = repository.find_latest(asset_id)

        if asset is None:
            return {
                "found": False,
                "error": f"Asset not found: {asset_id}",
            }

        return {
            "found": True,
            "asset": {
                "asset_id": asset.asset_id,
                "symbol": asset.symbol,
                "asset_class": asset.asset_class,
                "name": asset.name,
                "region": asset.region,
                "currency": asset.currency,
                "description": asset.description,
                "system_time": asset.system_time.isoformat(),
                "valid_from": str(asset.valid_from),
                "valid_to": str(asset.valid_to) if asset.valid_to else None,
                "is_deleted": asset.is_deleted,
                "attributes": asset.attributes,
            },
        }
    finally:
        session.shutdown()


@mcp.tool()
def list_data_sources(offset: int = 0, limit: int = 20) -> dict:
    """
    Return a paginated list of financial data sources.
    """
    if offset < 0:
        raise ValueError("offset must be >= 0")

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

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

        return {
            "offset": offset,
            "limit": limit,
            "total": len(items),
            "items": items[offset: offset + limit],
        }
    finally:
        session.shutdown()


@mcp.tool()
def get_data_source_details(data_source_id: str) -> dict:
    """
    Return the latest known version of one financial data source.
    """
    session = get_session()

    try:
        repository = DataSourceRepository(session)
        data_source = repository.find_latest(data_source_id)

        if data_source is None:
            return {
                "found": False,
                "error": f"Data source not found: {data_source_id}",
            }

        return {
            "found": True,
            "data_source": {
                "data_source_id": data_source.data_source_id,
                "name": data_source.name,
                "provider_type": data_source.provider_type,
                "base_url": data_source.base_url,
                "description": data_source.description,
                "system_time": data_source.system_time.isoformat(),
                "valid_from": str(data_source.valid_from),
                "valid_to": str(data_source.valid_to) if data_source.valid_to else None,
                "is_deleted": data_source.is_deleted,
                "attributes": data_source.attributes,
            },
        }
    finally:
        session.shutdown()


@mcp.tool()
def get_time_series_data(
    asset_id: str,
    data_source_id: str,
    start_business_date: str,
    end_business_date: str,
    include_attributes: bool = False,
) -> dict:
    """
    Return latest-version time-series records for one asset/source in a bounded date interval.
    Dates must use YYYY-MM-DD format. The interval is [start_business_date, end_business_date).
    """
    start_date = date.fromisoformat(start_business_date)
    end_date = date.fromisoformat(end_business_date)

    if end_date <= start_date:
        raise ValueError("end_business_date must be greater than start_business_date")

    if (end_date - start_date).days > 366:
        raise ValueError("date interval too large; maximum accepted interval is 366 days")

    session = get_session()

    try:
        repository = TimeSeriesRepository(session)

        records = []
        current_year = start_date.year
        end_year = end_date.year

        while current_year <= end_year:
            year_start = max(start_date, date(current_year, 1, 1))
            year_end = min(end_date, date(current_year + 1, 1, 1))

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
                "business_date": str(point.business_date),
                "system_time": point.system_time.isoformat(),
                "values_double": point.values_double,
                "values_text": point.values_text,
                "is_deleted": point.is_deleted,
            }

            if include_attributes:
                item["attributes"] = point.attributes

            response_records.append(item)

        return {
            "asset_id": asset_id,
            "data_source_id": data_source_id,
            "start_business_date": start_business_date,
            "end_business_date": end_business_date,
            "records_returned": len(response_records),
            "records": response_records,
        }
    finally:
        session.shutdown()


@mcp.tool()
def get_yearly_summary(asset_id: str, data_source_id: str = "YFINANCE") -> dict:
    """
    Return Spark-generated yearly aggregation results for one asset.
    """
    session = get_session()

    try:
        query = """
        SELECT asset_id, data_source_id, business_year, record_count,
               min_close, max_close, avg_close, avg_volume,
               yearly_return, volatility
        FROM analytics_yearly_summary
        WHERE asset_id = ?
          AND data_source_id = ?
        """

        prepared = session.prepare(query)
        rows = session.execute(prepared, (asset_id, data_source_id))

        items = []

        for row in rows:
            items.append(
                {
                    "asset_id": row["asset_id"],
                    "data_source_id": row["data_source_id"],
                    "business_year": row["business_year"],
                    "record_count": row["record_count"],
                    "min_close": row["min_close"],
                    "max_close": row["max_close"],
                    "avg_close": row["avg_close"],
                    "avg_volume": row["avg_volume"],
                    "yearly_return": row["yearly_return"],
                    "volatility": row["volatility"],
                }
            )

        return {
            "asset_id": asset_id,
            "data_source_id": data_source_id,
            "items": items,
        }
    finally:
        session.shutdown()


@mcp.tool()
def get_price_predictions(
    asset_id: str,
    data_source_id: str = "YFINANCE",
    limit: int = 20,
) -> dict:
    """
    Return Spark ML-generated price predictions for one asset.
    """
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    session = get_session()

    try:
        query = """
        SELECT asset_id, data_source_id, business_date, actual_close,
               predicted_close, prediction_error, model_name
        FROM ml_price_predictions
        WHERE asset_id = ?
          AND data_source_id = ?
        LIMIT ?
        """

        prepared = session.prepare(query)
        rows = session.execute(prepared, (asset_id, data_source_id, limit))

        predictions = []

        for row in rows:
            predictions.append(
                {
                    "asset_id": row["asset_id"],
                    "data_source_id": row["data_source_id"],
                    "business_date": str(row["business_date"]),
                    "actual_close": row["actual_close"],
                    "predicted_close": row["predicted_close"],
                    "prediction_error": row["prediction_error"],
                    "model_name": row["model_name"],
                }
            )

        return {
            "asset_id": asset_id,
            "data_source_id": data_source_id,
            "limit": limit,
            "predictions": predictions,
        }
    finally:
        session.shutdown()


if __name__ == "__main__":
    mcp.run()