from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from api.config import settings
from api.database.mssql_connection import get_sql_connection_dep

router = APIRouter()

# dependency bound to DW DB
dw_conn_dep = get_sql_connection_dep(settings.SQLSERVER_DB_DW)

@router.get("/dimcliente")
def list_dimcliente(page: int = 1, limit: int = 50, conn = Depends(dw_conn_dep)):
    offset = (page - 1) * limit
    q = text("""
    SELECT ClienteID, ClienteKeyNatural, Nombre, Email, Genero, Pais, FechaRegistro, SourceSystem, EsRegistroActual
    FROM dbo.DimCliente
    ORDER BY ClienteID
    OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
    """)
    total_q = text("SELECT COUNT(1) FROM dbo.DimCliente;")
    rows = conn.execute(q, {"offset": offset, "limit": limit}).mappings().all()
    total = conn.execute(total_q).scalar_one()
    return {"data": [dict(r) for r in rows], "total": total}

@router.get("/dimproducto")
def list_dimproducto(page: int = 1, limit: int = 50, conn = Depends(dw_conn_dep)):
    offset = (page - 1) * limit
    q = text("""
    SELECT ProductoID, SKU, Nombre, EsRegistroActual
    FROM dbo.DimProducto
    ORDER BY ProductoID
    OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
    """)
    total_q = text("SELECT COUNT(1) FROM dbo.DimProducto;")
    rows = conn.execute(q, {"offset": offset, "limit": limit}).mappings().all()
    total = conn.execute(total_q).scalar_one()
    return {"data": [dict(r) for r in rows], "total": total}

@router.get("/dimtiempo")
def list_dimtiempo(page: int = 1, limit: int = 50, conn = Depends(dw_conn_dep)):
    offset = (page - 1) * limit
    q = text("""
    SELECT TiempoID, MesAnio
    FROM dbo.DimTiempo
    ORDER BY TiempoID
    OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
    """)
    total_q = text("SELECT COUNT(1) FROM dbo.DimTiempo;")
    rows = conn.execute(q, {"offset": offset, "limit": limit}).mappings().all()
    total = conn.execute(total_q).scalar_one()
    return {"data": [dict(r) for r in rows], "total": total}