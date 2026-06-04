from cassandra.cluster import Cluster, Session
from cassandra.query import dict_factory

from app.core.config import settings


def get_cluster() -> Cluster:
    return Cluster([settings.cassandra_host], port=settings.cassandra_port)


def get_session() -> Session:
    cluster = get_cluster()
    session = cluster.connect(settings.cassandra_keyspace)
    session.row_factory = dict_factory
    return session


def check_connection() -> bool:
    session = get_session()
    row = session.execute("SELECT release_version FROM system.local").one()
    session.shutdown()
    return row is not None