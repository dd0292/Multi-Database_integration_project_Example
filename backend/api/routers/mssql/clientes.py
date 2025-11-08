from fastapi import APIRouter, Depends, HTTPException, status
from api.database.mssql_connection import get_sql_connection_dep
from api.services.mssql.clientes_service import ClienteService
from api.schemas.froms import ClienteFormData

router = APIRouter()

@router.get("/")
def list_clientes(page: int = 1, limit: int = 20, conn = Depends(get_sql_connection_dep)):
    svc = ClienteService(conn)
    return svc.get_clientes(page=page, limit=limit)

@router.get("/{cliente_id}")
def get_cliente(cliente_id: int, conn = Depends(get_sql_connection_dep)):
    svc = ClienteService(conn)
    row = svc.get_cliente_by_id(cliente_id)
    if not row:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return row

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_cliente(payload: ClienteFormData, conn = Depends(get_sql_connection_dep)):
    svc = ClienteService(conn)
    created = svc.create_cliente(payload)
    return created

@router.put("/{cliente_id}")
def update_cliente(cliente_id: int, payload: ClienteFormData, conn = Depends(get_sql_connection_dep)):
    svc = ClienteService(conn)
    updated = svc.update_cliente(cliente_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Cliente not found or no changes")
    return updated

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(cliente_id: int, conn = Depends(get_sql_connection_dep)):
    svc = ClienteService(conn)
    ok = svc.delete_cliente(cliente_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return None