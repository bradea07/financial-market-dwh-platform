from pathlib import Path
import csv


def test_yearly_summary_output_exists_and_has_rows():
    path = Path("data/spark_outputs/yearly_summary/yearly_summary.csv")

    assert path.exists()

    with path.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) >= 3
    assert {"AAPL", "MSFT", "TSLA"}.issubset({row["asset_id"] for row in rows})
    assert "avg_close" in rows[0]
    assert "yearly_return" in rows[0]
    assert "volatility" in rows[0]


def test_price_predictions_output_exists_and_has_rows():
    path = Path("data/spark_outputs/price_predictions/price_predictions.csv")

    assert path.exists()

    with path.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) >= 1
    assert "actual_close" in rows[0]
    assert "predicted_close" in rows[0]
    assert "prediction_error" in rows[0]