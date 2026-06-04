from app.mcp.server import (
    get_asset_details,
    get_price_predictions,
    get_time_series_data,
    get_yearly_summary,
    list_assets,
    list_data_sources,
)


def test_mcp_list_assets_tool():
    result = list_assets(offset=0, limit=20)

    assert "items" in result
    assert result["total"] >= 1


def test_mcp_get_asset_details_tool():
    result = get_asset_details("AAPL")

    assert result["found"] is True
    assert result["asset"]["asset_id"] == "AAPL"


def test_mcp_list_data_sources_tool():
    result = list_data_sources(offset=0, limit=20)

    assert "items" in result
    assert result["total"] >= 1


def test_mcp_get_time_series_data_tool():
    result = get_time_series_data(
        asset_id="AAPL",
        data_source_id="YFINANCE",
        start_business_date="2024-01-01",
        end_business_date="2024-02-01",
        include_attributes=True,
    )

    assert result["records_returned"] >= 1
    assert result["records"][0]["values_double"]["close"] is not None


def test_mcp_get_yearly_summary_tool():
    result = get_yearly_summary(asset_id="AAPL", data_source_id="YFINANCE")

    assert len(result["items"]) >= 1
    assert result["items"][0]["avg_close"] is not None


def test_mcp_get_price_predictions_tool():
    result = get_price_predictions(asset_id="AAPL", data_source_id="YFINANCE", limit=5)

    assert len(result["predictions"]) >= 1
    assert result["predictions"][0]["predicted_close"] is not None