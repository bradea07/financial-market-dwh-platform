# Financial Market Data Warehouse Platform

## Overview

This project is a financial market data warehouse platform designed to collect, store, process, analyze, and expose historical financial market data. The platform follows a complete data warehouse flow, starting from an external financial data provider and ending with multiple consumer layers such as a REST API, Apache Spark analytics workflows, Spark machine learning predictions, and MCP tools for LLM or agentic AI clients.

The project is meant to show how financial time-series data can be ingested from a real external source, normalized into an internal model, stored in a temporal NoSQL warehouse, accessed through a clean Data Access Layer, and then reused by different consumers. The system is not just a simple API over a database. It demonstrates a full pipeline where raw market data becomes structured warehouse data, then analytical results, then machine learning predictions, and finally structured tools that can be used by an AI assistant.

The project currently works with historical daily market data for Apple, Microsoft, and Tesla. These assets are identified as AAPL, MSFT, and TSLA. The data is collected from the Yahoo Finance Chart API, transformed into the internal domain model, and stored in Apache Cassandra.

## Project Goal

The goal of this project is to build a realistic data warehouse platform for financial market data. The platform should make it possible to answer questions such as what assets exist in the warehouse, what data sources were used, what historical prices are stored for a given asset, what yearly statistics can be computed from the data, and what price predictions can be generated from historical records.

The project also focuses on correct software architecture. The ingestion pipeline, REST API, Spark workflows, and MCP tools do not duplicate database logic directly. Instead, they use a repository-based Data Access Layer. This makes the system easier to maintain and closer to an industry-style architecture.

Another important goal is to support temporal data. Financial records are not treated as simple rows that are overwritten. Each record contains both a business date and a system time. The business date represents the market date for which the value is valid, while the system time represents when the warehouse stored that version of the record. This makes the platform able to keep track of different versions of the same logical data point.

## Main Features

The platform includes external financial data ingestion from the Yahoo Finance Chart API. The ingestion module extracts raw market data, transforms it into internal domain objects, and stores it in Cassandra through repository classes. During ingestion, the platform also stores statistics about the run, such as how many records were fetched, transformed, stored, skipped, or failed.

The storage layer is implemented with Apache Cassandra. Cassandra was chosen because the project requires a NoSQL database and because financial time-series data fits naturally with Cassandra's partitioning and clustering model. The schema is designed around assets, data sources, time-series records, analytics summaries, machine learning predictions, and ingestion run metadata.

The project exposes a REST API using FastAPI. The API provides endpoints for listing assets, retrieving asset details, listing data sources, retrieving data source details, and reading time-series data for a bounded interval. The time-series endpoint returns the latest version of each record and orders records from newest to oldest by business date.

Apache Spark is used for the analytics layer. One Spark workflow computes yearly aggregation metrics such as record count, minimum close price, maximum close price, average close price, average volume, yearly return, and volatility. The results are stored back into Cassandra and also written to a local CSV file for inspection.

Spark MLlib is used for the prediction workflow. A Linear Regression model is trained using features such as open price, high price, low price, volume, and previous close price. The model predicts the close price, stores the predictions in Cassandra, and writes a local CSV output. The workflow also prints evaluation metrics such as RMSE and R2.

The MCP layer exposes warehouse capabilities as read-only tools for LLM or agentic AI consumers. Instead of allowing an AI client to access the database directly, the MCP server provides controlled tools such as listing assets, retrieving asset details, fetching time-series data, reading Spark yearly summaries, and reading Spark ML predictions.

## Technology Stack

The project uses Python 3.11 as the main programming language. FastAPI is used for the REST API layer, while Apache Cassandra 5.0 is used as the NoSQL database. Docker and Docker Compose are used to run Cassandra locally. PySpark and Spark MLlib are used for analytics and prediction workflows. Pandas is used for intermediate data transformation and CSV handling. The MCP Python SDK is used for the LLM consumer layer, and Pytest is used for automated testing.

## Architecture

The project follows a layered architecture. The external financial provider is the starting point of the system. The ingestion pipeline extracts data from that provider, transforms it into the internal warehouse model, and loads it through the Data Access Layer. The Data Access Layer writes to Apache Cassandra. After the data is stored, it can be consumed by the REST API, Spark analytics workflows, Spark ML workflows, and MCP tools.

The architecture can be summarized as follows:

```text
External Financial Provider
        ↓
Ingestion Pipeline
        ↓
Data Access Layer
        ↓
Apache Cassandra
        ↓
REST API / Spark Analytics / Spark ML / MCP Tools
```

The important architectural decision is that Cassandra access is centralized through repository classes where possible. This prevents the project from becoming a collection of unrelated scripts and makes the storage behavior easier to understand and test.

## Project Structure

```text
financial-market-dwh-platform/

app/
  api/
    routes\_assets.py
    routes\_data.py
    routes\_data\_sources.py

  analytics/
    export\_timeseries\_csv.py
    spark\_aggregation.py
    spark\_prediction.py

  core/
    config.py

  db/
    cassandra.py
    init\_schema.py
    schema.cql

  domain/
    analytics.py
    asset.py
    data\_source.py
    ingestion\_run.py
    time\_series.py

  ingestion/
    providers/
      yfinance\_provider.py
    pipeline.py
    run\_ingestion.py
    transformers.py

  mcp/
    server.py

  repositories/
    asset\_repository.py
    base.py
    data\_source\_repository.py
    ingestion\_run\_repository.py
    time\_series\_repository.py

  main.py

tests/
data/
docker-compose.yml
requirements.txt
.env.example
README.md
```

The `app/domain` folder contains the internal data models. The `app/repositories` folder contains the Data Access Layer. The `app/ingestion` folder contains the provider, transformations, and ingestion pipeline. The `app/api` folder contains the REST API routes. The `app/analytics` folder contains Spark-related workflows. The `app/mcp` folder contains the MCP server and tools.

## Data Model

The warehouse is built around three main entities: financial assets, data sources, and time-series points. These entities represent the core information needed by the platform.

A financial asset represents a market instrument. In this project, examples include AAPL, MSFT, and TSLA. Each asset contains an asset ID, symbol, asset class, name, region, currency, description, custom attributes, system time, and validity information.

A data source represents the external provider that supplied the data. In this project, the main data source is `YFINANCE`, which uses the Yahoo Finance Chart API. The data source stores metadata such as name, provider type, base URL, description, attributes, system time, and validity information.

A time-series point represents one daily market record for one asset and one data source. Each point contains the asset ID, data source ID, business year, business date, system time, price values, volume, provider metadata, and ingestion time.

## Temporal Warehouse Design

The project uses a temporal model based on `business\_date` and `system\_time`. The `business\_date` describes when the financial value is valid in the real market. The `system\_time` describes when that value was stored in the warehouse.

This distinction matters because financial data can be corrected, reloaded, or versioned. Instead of overwriting the previous value directly, the warehouse can store a new version with a newer system time. When the platform retrieves data, it can return the latest version of each logical record.

The main time-series table is partitioned by asset ID, data source ID, and business year. This keeps reads bounded and avoids scanning unnecessary data. The records are clustered by business date and system time in descending order, which makes latest-version reads efficient.

## Cassandra Tables

The Cassandra schema contains six main tables: `assets\_by\_id`, `data\_sources\_by\_id`, `time\_series\_by\_asset\_source\_year`, `analytics\_yearly\_summary`, `ml\_price\_predictions`, and `ingestion\_runs`.

The `assets\_by\_id` table stores versioned asset metadata. The `data\_sources\_by\_id` table stores versioned data source metadata. The `time\_series\_by\_asset\_source\_year` table stores historical daily financial records. The `analytics\_yearly\_summary` table stores Spark aggregation results. The `ml\_price\_predictions` table stores Spark ML prediction results. The `ingestion\_runs` table stores metadata about ingestion executions.

This schema separates raw warehouse data from analytical outputs. Time-series data is stored in its own table, while Spark results and machine learning predictions are stored in dedicated tables. This makes it easier to inspect and consume each part of the pipeline.

## Data Access Layer

The project includes a repository-based Data Access Layer. The main repository classes are `AssetRepository`, `DataSourceRepository`, `TimeSeriesRepository`, and `IngestionRunRepository`.

These repositories expose methods such as `save`, `find\_latest`, `find\_all`, `find\_as\_of`, and `mark\_deleted`, depending on the entity. The purpose of this layer is to keep Cassandra access logic separate from the rest of the application. This means that API routes, ingestion code, and MCP tools do not need to know the details of every Cassandra query.

The repository layer is also tested with Pytest. The tests verify that entities can be saved and read back correctly from Cassandra.

## Setup Instructions

First, clone the repository and enter the project folder.

```powershell
git clone https://github.com/bradea07/financial-market-dwh-platform.git
cd financial-market-dwh-platform
```

Create a Python virtual environment.

```powershell
py -3.11 -m venv .venv
```

Activate the virtual environment.

```powershell
.\\.venv\\Scripts\\Activate.ps1
```

Install the required dependencies.

```powershell
pip install -r requirements.txt
```

Start Cassandra with Docker Compose.

```powershell
docker compose up -d
```

Check that Cassandra is running.

```powershell
docker ps
```

The expected container name is `financial-dwh-cassandra`.

Initialize the Cassandra schema.

```powershell
python -m app.db.init\_schema
```

The expected output is:

```text
Cassandra schema initialized successfully.
```

## Running the Ingestion Pipeline

The ingestion pipeline downloads real historical financial data from the Yahoo Finance Chart API. It transforms the raw provider response into internal domain models and stores the data in Cassandra through the repository layer.

Run the ingestion pipeline with:

```powershell
python -m app.ingestion.run\_ingestion
```

A successful run should produce output similar to this:

```text
Ingestion completed.
Provider: YFINANCE
Fetched records: 753
Transformed records: 753
Stored records: 753
Skipped records: 0
Failed records: 0
```

The ingestion flow follows the pattern Extract, Transform, and Load. The extract step calls the external provider. The transform step converts the provider format into internal objects. The load step persists assets, data sources, time-series points, and ingestion run metadata into Cassandra.

## Running the REST API

Start the API server with:

```powershell
uvicorn app.main:app --reload
```

Open Swagger UI in the browser:

```text
http://127.0.0.1:8000/docs
```

The REST API exposes endpoints for health checks, assets, data sources, and time-series data. The health endpoint checks whether the API is running and whether Cassandra is reachable. The assets endpoints allow users to list assets and inspect a specific asset. The data source endpoints allow users to list available providers and inspect provider metadata. The time-series endpoint returns daily market records for one asset and one source in a bounded business-date interval.

The main endpoints are:

```text
GET /health
GET /assets
GET /assets/{asset\_id}
GET /data-sources
GET /data-sources/{data\_source\_id}
GET /data
```

A typical time-series request looks like this:

```text
GET /data?assetId=AAPL\&dataSourceId=YFINANCE\&startBusinessDate=2024-01-01\&endBusinessDate=2024-02-01\&includeAttributes=true
```

The interval is half-open, meaning that the start date is included and the end date is excluded. The response returns the latest known version of each record and orders the records by newest business date first.

## Spark Aggregation Workflow

The project includes a Spark aggregation workflow. This workflow exports the latest time-series records from Cassandra, loads them into Spark, computes yearly metrics, stores the results back into Cassandra, and writes a local CSV file for inspection.

Run the aggregation workflow with:

```powershell
python -m app.analytics.spark\_aggregation
```

The workflow computes yearly metrics such as record count, minimum close price, maximum close price, average close price, average volume, yearly return, and volatility.

A successful run should produce output similar to this:

```text
Spark yearly aggregation completed.
Rows persisted to Cassandra: 3
```

Example aggregation results include AAPL, MSFT, and TSLA for the 2024 business year. The results are stored in the `analytics\_yearly\_summary` Cassandra table and also written locally to `data/spark\_outputs/yearly\_summary/yearly\_summary.csv`.

## Spark Machine Learning Workflow

The project also includes a Spark ML prediction workflow. This workflow creates a machine learning dataset from historical market records, trains a Spark Linear Regression model, predicts close prices, stores the predictions in Cassandra, and writes a local CSV output.

Run the prediction workflow with:

```powershell
python -m app.analytics.spark\_prediction
```

The model uses open price, high price, low price, volume, and previous close price as input features. The prediction target is the close price.

A successful run should produce output similar to this:

```text
Spark price prediction completed.
Rows persisted to Cassandra: 195
RMSE: 2.6161
R2: 0.9993
```

The results are stored in the `ml\_price\_predictions` Cassandra table. Each prediction contains the asset ID, data source ID, business date, actual close price, predicted close price, prediction error, model name, and feature values.

## MCP Consumer Layer

The project includes an MCP server for LLM and agentic AI consumers. The MCP server is read-only and exposes controlled tools over the warehouse. This is safer and more predictable than allowing an AI client to access the database directly.

Run the MCP server with:

```powershell
python -m app.mcp.server
```

The implemented MCP tools are `list\_assets`, `get\_asset\_details`, `list\_data\_sources`, `get\_data\_source\_details`, `get\_time\_series\_data`, `get\_yearly\_summary`, and `get\_price\_predictions`.

These tools return structured data instead of free-form text. This makes them easier for an LLM client to use and also keeps the platform behavior deterministic. An LLM client can use these tools to discover assets, inspect metadata, fetch bounded time-series records, retrieve Spark aggregation results, and retrieve Spark ML predictions.

## Testing

The project includes automated tests for the main layers of the platform. The tests cover the Data Access Layer, ingestion transformations, REST API endpoints, Spark output files, and MCP tools.

Run all tests with:

```powershell
pytest tests -q
```

The current test result is:

```text
22 passed, 1 warning
```

The warning comes from the Cassandra Python driver using `asyncore`, which is deprecated in newer Python versions. It does not affect the functionality of the project.

## Full End-to-End Run

To run the full platform from zero, use the following sequence:

```powershell
docker compose up -d
python -m app.db.init\_schema
python -m app.ingestion.run\_ingestion
python -m app.analytics.spark\_aggregation
python -m app.analytics.spark\_prediction
pytest tests -q
uvicorn app.main:app --reload
```

After starting the API server, open Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

From Swagger, the warehouse can be explored through the REST endpoints.

## Notes About Spark on Windows

When running Spark locally on Windows, warnings about `winutils.exe`, `HADOOP\_HOME`, or native Hadoop libraries may appear. These warnings are common when Spark is used locally on Windows. In this project, the Spark workflows still run correctly. The scripts avoid relying on Spark's Hadoop-based local writer where necessary and store analytical results back into Cassandra.

## Current Status

The project currently includes a working Cassandra warehouse, temporal schema, repository-based Data Access Layer, external financial data ingestion, REST API consumption layer, Spark aggregation workflow, Spark ML prediction workflow, MCP consumer tools, and automated tests.

The current test result is:

```text
22 passed
```

Overall, the platform demonstrates a complete financial market data warehouse workflow from ingestion to storage, API access, analytics, prediction, and MCP-based LLM access.

## Demo Video

The full demo video is available here:

https://drive.google.com/file/d/1rEcgbCD6gaIryCuHquz6yWsKpn1lMEJy/view?usp=sharing

If Google Drive preview is unavailable, the video can be downloaded from the same link.