from dataclasses import dataclass
from datetime import date, datetime, time, timezone

import pandas as pd
import requests


@dataclass(frozen=True)
class ProviderAssetRequest:
    symbol: str
    asset_id: str
    asset_class: str
    name: str
    region: str
    currency: str
    description: str


class YFinanceProvider:
    data_source_id = "YFINANCE"
    name = "Yahoo Finance Chart API"
    provider_type = "REST_API"
    base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

    def fetch_history(
        self,
        request: ProviderAssetRequest,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        start_timestamp = self._date_to_unix_timestamp(start_date)
        end_timestamp = self._date_to_unix_timestamp(end_date)

        url = (
            f"{self.base_url}/{request.symbol}"
            f"?period1={start_timestamp}"
            f"&period2={end_timestamp}"
            f"&interval=1d"
            f"&events=history"
        )

        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()

        payload = response.json()
        result = payload.get("chart", {}).get("result")

        if not result:
            return pd.DataFrame()

        chart = result[0]
        timestamps = chart.get("timestamp", [])
        quote = chart.get("indicators", {}).get("quote", [{}])[0]
        adjclose = chart.get("indicators", {}).get("adjclose", [{}])[0]

        if not timestamps:
            return pd.DataFrame()

        rows = []

        for index, timestamp in enumerate(timestamps):
            row = {
                "Date": datetime.fromtimestamp(timestamp, tz=timezone.utc).date(),
                "Open": self._get_indexed_value(quote.get("open"), index),
                "High": self._get_indexed_value(quote.get("high"), index),
                "Low": self._get_indexed_value(quote.get("low"), index),
                "Close": self._get_indexed_value(quote.get("close"), index),
                "Adj Close": self._get_indexed_value(adjclose.get("adjclose"), index),
                "Volume": self._get_indexed_value(quote.get("volume"), index),
                "provider_symbol": request.symbol,
                "asset_id": request.asset_id,
                "provider_backend": "yahoo_chart_api",
            }
            rows.append(row)

        data = pd.DataFrame(rows)
        data = data.dropna(subset=["Open", "High", "Low", "Close"])

        return data

    @staticmethod
    def _date_to_unix_timestamp(value: date) -> int:
        dt = datetime.combine(value, time.min, tzinfo=timezone.utc)
        return int(dt.timestamp())

    @staticmethod
    def _get_indexed_value(values, index: int):
        if values is None or index >= len(values):
            return None

        return values[index]