from fastapi import FastAPI

from app.api.routes_assets import router as assets_router
from app.api.routes_data import router as data_router
from app.api.routes_data_sources import router as data_sources_router
from app.db.cassandra import check_connection


app = FastAPI(
    title="Financial Markets Data Warehouse",
    description="Temporal financial markets data warehouse with Cassandra, FastAPI, Spark, and MCP.",
    version="1.0.0",
)


@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "cassandra": check_connection(),
    }


app.include_router(assets_router)
app.include_router(data_sources_router)
app.include_router(data_router)