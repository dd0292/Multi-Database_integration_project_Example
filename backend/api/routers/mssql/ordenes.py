from fastapi import APIRouter, Depends, HTTPException, status

from api.database.mssql_connection import get_sql_connection_dep
from api.services.mssql.ordenes_service import OrdenService
from api.schemas.froms import OrdenFormData

router = APIRouter()

@router.get("/")
def list_ordenes(page: int = 1, limit: int = 20, conn = Depends(get_sql_connection_dep)):
    svc = OrdenService(conn)
    return svc.get_ordenes(page=page, limit=limit)

@router.get("/{orden_id}")
def get_orden(orden_id: int, conn = Depends(get_sql_connection_dep)):
    svc = OrdenService(conn)
    row = svc.get_orden_by_id(orden_id)
    if not row:
        raise HTTPException(status_code=404, detail="Orden not found")
    return row

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_orden(payload: OrdenFormData, conn = Depends(get_sql_connection_dep)):
    svc = OrdenService(conn)
    created = svc.create_orden(payload)
    return created

@router.put("/{orden_id}")
def update_orden(orden_id: int, payload: OrdenFormData, conn = Depends(get_sql_connection_dep)):
    svc = OrdenService(conn)
    updated = svc.update_orden(orden_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Orden not found or no changes")
    return updated

@router.delete("/{orden_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_orden(orden_id: int, conn = Depends(get_sql_connection_dep)):
    svc = OrdenService(conn)
    ok = svc.delete_orden(orden_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Orden not found")
    return None