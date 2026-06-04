from datetime import datetime, timezone
from pathlib import Path
import csv

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag
from pyspark.sql.window import Window

from app.analytics.export_timeseries_csv import export_time_series_to_csv
from app.db.cassandra import get_session


OUTPUT_DIR = Path("data/spark_outputs/price_predictions")


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("FinancialDwhPricePrediction")
        .master("local[*]")
        .getOrCreate()
    )


def save_predictions_to_cassandra(prediction_rows) -> None:
    session = get_session()

    query = """
    INSERT INTO ml_price_predictions (
        asset_id,
        data_source_id,
        business_date,
        generated_at,
        actual_close,
        predicted_close,
        prediction_error,
        model_name,
        features
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    prepared = session.prepare(query)
    generated_at = datetime.now(timezone.utc)

    try:
        for row in prediction_rows:
            actual_close = float(row["close"])
            predicted_close = float(row["prediction"])

            session.execute(
                prepared,
                (
                    row["asset_id"],
                    row["data_source_id"],
                    row["business_date"],
                    generated_at,
                    actual_close,
                    predicted_close,
                    abs(actual_close - predicted_close),
                    "Spark LinearRegression",
                    {
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "volume": float(row["volume"]),
                        "previous_close": float(row["previous_close"]),
                    },
                ),
            )
    finally:
        session.shutdown()


def write_predictions_csv(rows) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "price_predictions.csv"

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "asset_id",
                "data_source_id",
                "business_date",
                "open",
                "high",
                "low",
                "volume",
                "previous_close",
                "actual_close",
                "predicted_close",
                "prediction_error",
            ],
        )

        writer.writeheader()

        for row in rows:
            actual_close = float(row["close"])
            predicted_close = float(row["prediction"])

            writer.writerow(
                {
                    "asset_id": row["asset_id"],
                    "data_source_id": row["data_source_id"],
                    "business_date": row["business_date"],
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "volume": row["volume"],
                    "previous_close": row["previous_close"],
                    "actual_close": actual_close,
                    "predicted_close": predicted_close,
                    "prediction_error": abs(actual_close - predicted_close),
                }
            )

    return output_file


def run_price_prediction() -> None:
    csv_path = export_time_series_to_csv()

    spark = create_spark_session()

    try:
        df = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(str(csv_path))
        )

        base_df = (
            df
            .filter(col("is_deleted") == False)
            .filter(col("asset_id").isin("AAPL", "MSFT", "TSLA"))
            .filter(col("close").isNotNull())
            .filter(col("open").isNotNull())
            .filter(col("high").isNotNull())
            .filter(col("low").isNotNull())
            .filter(col("volume").isNotNull())
            .orderBy("asset_id", "business_date")
        )

        window = Window.partitionBy("asset_id", "data_source_id").orderBy("business_date")

        ml_df = (
            base_df
            .withColumn("previous_close", lag("close").over(window))
            .filter(col("previous_close").isNotNull())
        )

        assembler = VectorAssembler(
            inputCols=["open", "high", "low", "volume", "previous_close"],
            outputCol="features",
        )

        assembled_df = assembler.transform(ml_df)

        train_df, test_df = assembled_df.randomSplit([0.7, 0.3], seed=42)

        model = (
            LinearRegression(
                featuresCol="features",
                labelCol="close",
                predictionCol="prediction",
                maxIter=20,
                regParam=0.1,
            )
            .fit(train_df)
        )

        predictions_df = (
            model
            .transform(test_df)
            .select(
                "asset_id",
                "data_source_id",
                "business_date",
                "open",
                "high",
                "low",
                "volume",
                "previous_close",
                "close",
                "prediction",
            )
            .orderBy("asset_id", "business_date")
        )

        rows = [row.asDict() for row in predictions_df.collect()]

        output_file = write_predictions_csv(rows)
        save_predictions_to_cassandra(rows)

        print("Spark price prediction completed.")
        print(f"Rows persisted to Cassandra: {len(rows)}")
        print(f"CSV output: {output_file}")
        print(f"RMSE: {model.summary.rootMeanSquaredError}")
        print(f"R2: {model.summary.r2}")

        predictions_df.show(20, truncate=False)

    finally:
        spark.stop()


if __name__ == "__main__":
    run_price_prediction()