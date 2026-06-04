import csv
from pathlib import Path

from app.db.cassandra import get_session


EXPORT_DIR = Path("data/exports")
EXPORT_FILE = EXPORT_DIR / "time_series_latest.csv"


def export_time_series_to_csv() -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    session = get_session()

    try:
        rows = session.execute(
            """
            SELECT asset_id, data_source_id, business_year, business_date, system_time,
                   values_double, values_text, is_deleted
            FROM time_series_by_asset_source_year
            """
        )

        latest_by_key = {}

        for row in rows:
            key = (
                row["asset_id"],
                row["data_source_id"],
                row["business_date"],
            )

            if key not in latest_by_key:
                latest_by_key[key] = row

        with EXPORT_FILE.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "asset_id",
                    "data_source_id",
                    "business_year",
                    "business_date",
                    "system_time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "adjusted_close",
                    "volume",
                    "currency",
                    "is_deleted",
                ],
            )

            writer.writeheader()

            for row in latest_by_key.values():
                values_double = dict(row["values_double"] or {})
                values_text = dict(row["values_text"] or {})

                writer.writerow(
                    {
                        "asset_id": row["asset_id"],
                        "data_source_id": row["data_source_id"],
                        "business_year": row["business_year"],
                        "business_date": str(row["business_date"]),
                        "system_time": row["system_time"].isoformat(),
                        "open": values_double.get("open"),
                        "high": values_double.get("high"),
                        "low": values_double.get("low"),
                        "close": values_double.get("close"),
                        "adjusted_close": values_double.get("adjusted_close"),
                        "volume": values_double.get("volume"),
                        "currency": values_text.get("currency", "USD"),
                        "is_deleted": row["is_deleted"],
                    }
                )

    finally:
        session.shutdown()

    print(f"Exported time-series data to {EXPORT_FILE}")
    return EXPORT_FILE


if __name__ == "__main__":
    export_time_series_to_csv()