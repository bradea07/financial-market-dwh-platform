from datetime import datetime, timezone
from pathlib import Path
import csv

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    count,
    first,
    last,
    max as spark_max,
    min as spark_min,
    stddev,
)

from app.analytics.export_timeseries_csv import export_time_series_to_csv
from app.db.cassandra import get_session


OUTPUT_DIR = Path("data/spark_outputs/yearly_summary")


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("FinancialDwhYearlyAggregation")
        .master("local[*]")
        .getOrCreate()
    )


def save_summary_to_cassandra(summary_rows) -> None:
    session = get_session()

    query = """
    INSERT INTO analytics_yearly_summary (
        asset_id,
        data_source_id,
        business_year,
        generated_at,
        record_count,
        min_close,
        max_close,
        avg_close,
        avg_volume,
        yearly_return,
        volatility
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    prepared = session.prepare(query)
    generated_at = datetime.now(timezone.utc)

    try:
        for row in summary_rows:
            session.execute(
                prepared,
                (
                    row["asset_id"],
                    row["data_source_id"],
                    int(row["business_year"]),
                    generated_at,
                    int(row["record_count"]),
                    float(row["min_close"]) if row["min_close"] is not None else None,
                    float(row["max_close"]) if row["max_close"] is not None else None,
                    float(row["avg_close"]) if row["avg_close"] is not None else None,
                    float(row["avg_volume"]) if row["avg_volume"] is not None else None,
                    float(row["yearly_return"]) if row["yearly_return"] is not None else None,
                    float(row["volatility"]) if row["volatility"] is not None else None,
                ),
            )
    finally:
        session.shutdown()


def write_summary_csv(rows) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "yearly_summary.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "asset_id",
                "data_source_id",
                "business_year",
                "record_count",
                "min_close",
                "max_close",
                "avg_close",
                "avg_volume",
                "yearly_return",
                "volatility",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_file


def run_yearly_aggregation() -> None:
    csv_path = export_time_series_to_csv()

    spark = create_spark_session()

    try:
        df = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(str(csv_path))
        )

        clean_df = (
            df
            .filter(col("is_deleted") == False)
            .filter(col("close").isNotNull())
            .filter(col("asset_id").isin("AAPL", "MSFT", "TSLA"))
            .orderBy("asset_id", "data_source_id", "business_year", "business_date")
        )

        summary_df = (
            clean_df
            .groupBy("asset_id", "data_source_id", "business_year")
            .agg(
                count("*").alias("record_count"),
                spark_min("close").alias("min_close"),
                spark_max("close").alias("max_close"),
                avg("close").alias("avg_close"),
                avg("volume").alias("avg_volume"),
                first("close").alias("first_close"),
                last("close").alias("last_close"),
                stddev("close").alias("volatility"),
            )
            .withColumn(
                "yearly_return",
                ((col("last_close") - col("first_close")) / col("first_close")) * 100,
            )
            .select(
                "asset_id",
                "data_source_id",
                "business_year",
                "record_count",
                "min_close",
                "max_close",
                "avg_close",
                "avg_volume",
                "yearly_return",
                "volatility",
            )
        )

        rows = [row.asDict() for row in summary_df.collect()]

        output_file = write_summary_csv(rows)
        save_summary_to_cassandra(rows)

        print("Spark yearly aggregation completed.")
        print(f"Rows persisted to Cassandra: {len(rows)}")
        print(f"CSV output: {output_file}")
        summary_df.show(truncate=False)

    finally:
        spark.stop()


if __name__ == "__main__":
    run_yearly_aggregation()