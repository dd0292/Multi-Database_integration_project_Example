from fastapi import APIRouter, Depends, HTTPException, status
from api.database.mssql_connection import get_sql_connection_dep
from api.services.mssql.productos_service import ProductoService
from api.schemas.froms import ProductoFormData

router = APIRouter()

@router.get("/")
def list_productos(page: int = 1, limit: int = 20, conn = Depends(get_sql_connection_dep)):
    svc = ProductoService(conn)
    return svc.get_productos(page=page, limit=limit)

@router.get("/{producto_id}")
def get_producto(producto_id: int, conn = Depends(get_sql_connection_dep)):
    svc = ProductoService(conn)
    row = svc.get_producto_by_id(producto_id)
    if not row:
        raise HTTPException(status_code=404, detail="Producto not found")
    return row

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_producto(payload: ProductoFormData, conn = Depends(get_sql_connection_dep)):
    svc = ProductoService(conn)
    created = svc.create_producto(payload)
    return created

@router.put("/{producto_id}")
def update_producto(producto_id: int, payload: ProductoFormData, conn = Depends(get_sql_connection_dep)):
    svc = ProductoService(conn)
    updated = svc.update_producto(producto_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Producto not found or no changes")
    return updated

@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(producto_id: int, conn = Depends(get_sql_connection_dep)):
    svc = ProductoService(conn)
    ok = svc.delete_producto(producto_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Producto not found")
    return None