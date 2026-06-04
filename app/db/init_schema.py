from pathlib import Path

from cassandra.cluster import Cluster

from app.core.config import settings


SCHEMA_FILE = Path(__file__).parent / "schema.cql"


def split_cql_statements(schema_text: str) -> list[str]:
    statements = []

    for raw_statement in schema_text.split(";"):
        statement = raw_statement.strip()

        if statement:
            statements.append(statement)

    return statements


def initialize_schema() -> None:
    schema_text = SCHEMA_FILE.read_text(encoding="utf-8")
    statements = split_cql_statements(schema_text)

    cluster = Cluster([settings.cassandra_host], port=settings.cassandra_port)
    session = cluster.connect()

    try:
        for statement in statements:
            session.execute(statement)
    finally:
        session.shutdown()
        cluster.shutdown()

    print("Cassandra schema initialized successfully.")


if __name__ == "__main__":
    initialize_schema()