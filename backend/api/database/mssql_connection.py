from typing import Generator, Optional, Dict, Callable
import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.pool import QueuePool

from api.config import settings

_engines: Dict[Optional[str], Engine] = {}

def _build_odbc_conn(driver: str, host: str, port: str, database: Optional[str],
                     user: str, password: str, trusted: bool = False) -> str:
    if trusted:
        odbc = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={database or ''};"
            "Trusted_Connection=Yes;"
            "TrustServerCertificate=Yes;"
        )
    else:
        odbc = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={database or ''};"
            f"UID={user};PWD={password};"
            "TrustServerCertificate=Yes;"
        )
    return odbc

def _create_engine_for(db_name: str, trusted: bool) -> Engine:
    driver = getattr(settings, "SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server")
    host = getattr(settings, "SQLSERVER_HOST", "localhost")
    port = getattr(settings, "SQLSERVER_PORT", "1433")
    user = getattr(settings, "SQLSERVER_USER", "sa")
    password = getattr(settings, "SQLSERVER_PASSWORD", "")

    odbc = _build_odbc_conn(driver, host, port, db_name, user, password, trusted)
    params = urllib.parse.quote_plus(odbc)
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={params}",
        fast_executemany=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
    )

def init_engines(app_settings) -> None:
    """Initialize engines at app startup"""
    trusted_flag = str(getattr(app_settings, "MSSQL_TRUSTED", "") or "").lower()
    trusted = trusted_flag in ("1", "true", "yes", "y")

    db_dw = getattr(app_settings, "SQLSERVER_DB_DW", None)
    db_transac = getattr(app_settings, "SQLSERVER_DB_TRANSAC", None)

    for db_name in (db_transac, db_dw):
        if not db_name:
            continue
        if db_name in _engines:
            continue
        _engines[db_name] = _create_engine_for(db_name, trusted)

def get_engine(db_name: Optional[str] = None) -> Engine:
    """Get or create engine for a database"""
    if db_name is None:
        db_name = settings.SQLSERVER_DB_TRANSAC

    if db_name not in _engines:
        trusted_flag = str(getattr(settings, "MSSQL_TRUSTED", "") or "").lower()
        trusted = trusted_flag in ("1", "true", "yes", "y")
        _engines[db_name] = _create_engine_for(db_name, trusted)

    return _engines[db_name]

def get_connection(db_name: Optional[str] = None) -> Connection:
    """Get a connection from the engine"""
    engine = get_engine(db_name)
    return engine.connect()

def dispose_engines() -> None:
    """Dispose all engines at shutdown"""
    for name, eng in list(_engines.items()):
        try:
            eng.dispose()
        except Exception:
            pass
        finally:
            _engines.pop(name, None)

def get_sql_connection_dep(db_name: Optional[str] = None) -> Callable[..., Generator[Connection, None, None]]:
    """
    Returns a dependency generator function bound to a DB name.
    
    Usage:
        transac_dep = get_sql_connection_dep(settings.SQLSERVER_DB_TRANSAC)
        dw_dep = get_sql_connection_dep(settings.SQLSERVER_DB_DW)
        
        @router.get(..., conn=Depends(transac_dep))
        def my_endpoint(conn = Depends(transac_dep)):
            ...
    """
    target_db = db_name or settings.SQLSERVER_DB_TRANSAC

    def _dep() -> Generator[Connection, None, None]:
        conn = get_connection(target_db)
        try:
            yield conn
            # Commit on successful completion
            conn.commit()
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass

    return _dep