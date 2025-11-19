from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File
import json

from api.database.mssql_connection import get_sql_connection_dep
from api.services.mssql.ordenes_service import OrdenService
from api.services.mssql.ordenes_bulk_service import OrdenBulkService
from api.config import settings

router = APIRouter()
transac_dep = get_sql_connection_dep(settings.SQLSERVER_DB_TRANSAC)

@router.get("/")
def list_ordenes(page: int = 1, limit: int = 20, conn = Depends(transac_dep)):
    svc = OrdenService(conn)
    return svc.get_ordenes(page=page, limit=limit)

@router.get("/{orden_id}")
def get_orden(orden_id: int, conn = Depends(transac_dep)):
    svc = OrdenService(conn)
    row = svc.get_orden_by_id(orden_id)
    if not row:
        raise HTTPException(status_code=404, detail="Orden not found")
    return row

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_orden(payload: dict = Body(...), conn = Depends(transac_dep)):
    svc = OrdenService(conn)
    try:
        created = svc.create_orden(payload)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # let unexpected errors propagate (server 500) but keep this short
        raise
    return created

@router.put("/{orden_id}")
def update_orden(orden_id: int, payload: dict = Body(...), conn = Depends(transac_dep)):
    svc = OrdenService(conn)
    try:
        updated = svc.update_orden(orden_id, payload)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    return updated

@router.delete("/{orden_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_orden(orden_id: int, conn = Depends(transac_dep)):
    svc = OrdenService(conn)
    ok = svc.delete_orden(orden_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Orden not found")
    return None

@router.post("/bulk/upload", status_code=status.HTTP_200_OK)
def bulk_upload_ordenes(file: UploadFile = File(...), conn = Depends(transac_dep)):
    """
    Bulk upload ordenes from JSON file.
    File should contain array of order objects.
    """
    try:
        content = file.file.read()
        ordenes = json.loads(content)
        
        if not isinstance(ordenes, list):
            raise HTTPException(status_code=400, detail="JSON must be an array of orders")
        
        svc = OrdenBulkService(conn)
        result = svc.bulk_upload_ordenes(ordenes)
        
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")