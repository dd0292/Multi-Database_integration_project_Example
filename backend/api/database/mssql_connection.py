import urllib.parse
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, Connection

from api.config import settings

_engine: Optional[Engine] = None

def init_engine(app_settings) -> Engine:
    global _engine
    if _engine is not None:
        return _engine

    host = getattr(app_settings, "SQLSERVER_HOST", "localhost")
    port = getattr(app_settings, "SQLSERVER_PORT", "1433")
    user = getattr(app_settings, "SQLSERVER_USER", "sa")
    password = getattr(app_settings, "SQLSERVER_PASSWORD", "")
    driver = getattr(app_settings, "SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server")
    # Optional default database - if empty, connection will allow cross-database queries via fully-qualified names
    database = getattr(app_settings, "SQLSERVER_DB", None)

    odbc_conn = (
        f"DRIVER={{{driver}}};"
        f"SERVER={host},{port};"
        f"UID={user};PWD={password};"
        "TrustServerCertificate=Yes;"
    )
    if database:
        odbc_conn += f"DATABASE={database};"

    params = urllib.parse.quote_plus(odbc_conn)
    _engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)
    return _engine

def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("SQL engine not initialized. Call init_engine(settings) on startup.")
    return _engine

def get_connection() -> Connection:
    return get_engine().connect()

def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None

# FastAPI dependency
def get_sql_connection_dep() -> Generator[Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()