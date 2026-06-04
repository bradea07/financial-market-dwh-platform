from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["cassandra"] is True


def test_list_assets_endpoint():
    response = client.get("/assets?offset=0&limit=20")

    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert data["limit"] == 20
    assert data["total"] >= 1


def test_get_asset_endpoint():
    response = client.get("/assets/AAPL")

    assert response.status_code == 200

    data = response.json()
    assert data["asset_id"] == "AAPL"
    assert data["symbol"] == "AAPL"


def test_list_data_sources_endpoint():
    response = client.get("/data-sources?offset=0&limit=20")

    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert data["total"] >= 1


def test_get_data_source_endpoint():
    response = client.get("/data-sources/YFINANCE")

    assert response.status_code == 200

    data = response.json()
    assert data["data_source_id"] == "YFINANCE"


def test_get_time_series_data_endpoint():
    response = client.get(
        "/data",
        params={
            "assetId": "AAPL",
            "dataSourceId": "YFINANCE",
            "startBusinessDate": "2024-01-01",
            "endBusinessDate": "2024-02-01",
            "includeAttributes": "true",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["assetId"] == "AAPL"
    assert data["dataSourceId"] == "YFINANCE"
    assert data["recordsReturned"] >= 1

    first_record = data["records"][0]
    assert "businessDate" in first_record
    assert "valuesDouble" in first_record
    assert "close" in first_record["valuesDouble"]