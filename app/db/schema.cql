CREATE KEYSPACE IF NOT EXISTS financial_dwh
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE financial_dwh;

CREATE TABLE IF NOT EXISTS assets_by_id (
    asset_id text,
    system_time timestamp,
    symbol text,
    asset_class text,
    name text,
    region text,
    currency text,
    description text,
    attributes map<text, text>,
    is_deleted boolean,
    valid_from date,
    valid_to date,
    PRIMARY KEY ((asset_id), system_time)
) WITH CLUSTERING ORDER BY (system_time DESC);

CREATE TABLE IF NOT EXISTS data_sources_by_id (
    data_source_id text,
    system_time timestamp,
    name text,
    provider_type text,
    base_url text,
    description text,
    attributes map<text, text>,
    is_deleted boolean,
    valid_from date,
    valid_to date,
    PRIMARY KEY ((data_source_id), system_time)
) WITH CLUSTERING ORDER BY (system_time DESC);

CREATE TABLE IF NOT EXISTS time_series_by_asset_source_year (
    asset_id text,
    data_source_id text,
    business_year int,
    business_date date,
    system_time timestamp,
    values_double map<text, double>,
    values_text map<text, text>,
    attributes map<text, text>,
    is_deleted boolean,
    ingested_at timestamp,
    PRIMARY KEY ((asset_id, data_source_id, business_year), business_date, system_time)
) WITH CLUSTERING ORDER BY (business_date DESC, system_time DESC);

CREATE TABLE IF NOT EXISTS analytics_yearly_summary (
    asset_id text,
    data_source_id text,
    business_year int,
    generated_at timestamp,
    record_count int,
    min_close double,
    max_close double,
    avg_close double,
    avg_volume double,
    yearly_return double,
    volatility double,
    PRIMARY KEY ((asset_id, data_source_id), business_year, generated_at)
) WITH CLUSTERING ORDER BY (business_year DESC, generated_at DESC);

CREATE TABLE IF NOT EXISTS ml_price_predictions (
    asset_id text,
    data_source_id text,
    business_date date,
    generated_at timestamp,
    actual_close double,
    predicted_close double,
    prediction_error double,
    model_name text,
    features map<text, double>,
    PRIMARY KEY ((asset_id, data_source_id), business_date, generated_at)
) WITH CLUSTERING ORDER BY (business_date DESC, generated_at DESC);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id uuid,
    provider_id text,
    started_at timestamp,
    finished_at timestamp,
    status text,
    fetched_records int,
    transformed_records int,
    stored_records int,
    skipped_records int,
    failed_records int,
    error_message text,
    PRIMARY KEY ((provider_id), started_at, run_id)
) WITH CLUSTERING ORDER BY (started_at DESC);