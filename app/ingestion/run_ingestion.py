from datetime import date, timedelta

from app.ingestion.pipeline import YFinanceIngestionPipeline
from app.ingestion.providers.yfinance_provider import ProviderAssetRequest


ASSETS = [
    ProviderAssetRequest(
        symbol="AAPL",
        asset_id="AAPL",
        asset_class="stock",
        name="Apple Inc.",
        region="US",
        currency="USD",
        description="Apple Inc. common stock.",
    ),
    ProviderAssetRequest(
        symbol="MSFT",
        asset_id="MSFT",
        asset_class="stock",
        name="Microsoft Corporation",
        region="US",
        currency="USD",
        description="Microsoft Corporation common stock.",
    ),
    ProviderAssetRequest(
        symbol="TSLA",
        asset_id="TSLA",
        asset_class="stock",
        name="Tesla Inc.",
        region="US",
        currency="USD",
        description="Tesla Inc. common stock.",
    ),
    
]


def main() -> None:
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)

    pipeline = YFinanceIngestionPipeline()
    result = pipeline.run(
        asset_requests=ASSETS,
        start_date=start_date,
        end_date=end_date,
    )

    print("Ingestion completed.")
    print(f"Provider: {result.provider_id}")
    print(f"Fetched records: {result.fetched_records}")
    print(f"Transformed records: {result.transformed_records}")
    print(f"Stored records: {result.stored_records}")
    print(f"Skipped records: {result.skipped_records}")
    print(f"Failed records: {result.failed_records}")


if __name__ == "__main__":
    main()