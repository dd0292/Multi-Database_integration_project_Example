from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from api.config import settings
from api.database.mssql_connection import get_sql_connection_dep
from api.services.mssql.dw_service import DWService

router = APIRouter()
dw_conn_dep = get_sql_connection_dep(settings.SQLSERVER_DB_DW)

@router.get("/")
def list_dimtiempos(page: int = 1, limit: int = 50, conn = Depends(dw_conn_dep)):
    svc = DWService(conn)
    return svc.get_dimtiempos(page=page, limit=limit)

@router.get("/{tiempo_id}")
def get_dimtiempo(tiempo_id: int, conn = Depends(dw_conn_dep)):
    svc = DWService(conn)
    row = svc.get_dimtiempo_by_id(tiempo_id)
    if not row:
        raise HTTPException(status_code=404, detail="DimTiempo not found")
    return row

@router.post("/bulk/upload")
def bulk_upload_dimtiempo(file: UploadFile = File(...), conn = Depends(dw_conn_dep)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be CSV")
    content = file.file.read()
    svc = DWService(conn)
    result = svc.bulk_upload_dimtiempo(content)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result