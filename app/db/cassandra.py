from cassandra.cluster import Cluster, Session
from cassandra.query import dict_factory


CASSANDRA_HOST = "127.0.0.1"
CASSANDRA_PORT = 9042
KEYSPACE = "financial_dwh"


def get_cluster() -> Cluster:
    return Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)


def get_session() -> Session:
    cluster = get_cluster()
    session = cluster.connect(KEYSPACE)
    session.row_factory = dict_factory
    return session


def check_connection() -> bool:
    session = get_session()
    row = session.execute("SELECT release_version FROM system.local").one()
    session.shutdown()
    return row is not None