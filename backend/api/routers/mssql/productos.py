from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from api.database.mssql_connection import get_sql_connection_dep
from api.services.mssql.productos_service import ProductoService
from api.services.mssql.bulk_upload_service import BulkUploadService
from api.config import settings
from api.schemas.froms import ProductoFormData

router = APIRouter()
transac_dep = get_sql_connection_dep(settings.SQLSERVER_DB_TRANSAC)

@router.get("/")
def list_productos(page: int = 1, limit: int = 20, conn = Depends(transac_dep)):
    svc = ProductoService(conn)
    return svc.get_productos(page=page, limit=limit)

@router.get("/{producto_id}")
def get_producto(producto_id: int, conn = Depends(transac_dep)):
    svc = ProductoService(conn)
    row = svc.get_producto_by_id(producto_id)
    if not row:
        raise HTTPException(status_code=404, detail="Producto not found")
    return row

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_producto(payload: ProductoFormData, conn = Depends(transac_dep)):
    svc = ProductoService(conn)
    created = svc.create_producto(payload)
    return created

@router.put("/{producto_id}")
def update_producto(producto_id: int, payload: ProductoFormData, conn = Depends(transac_dep)):
    svc = ProductoService(conn)
    updated = svc.update_producto(producto_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Producto not found or no changes")
    return updated

@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(producto_id: int, conn = Depends(transac_dep)):
    svc = ProductoService(conn)
    ok = svc.delete_producto(producto_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Producto not found")
    return None

@router.post("/bulk/upload", status_code=status.HTTP_200_OK)
def bulk_upload_productos(file: UploadFile = File(...), conn = Depends(transac_dep)):
    """
    Bulk upload productos from CSV file.
    Expected CSV columns: SKU, Nombre, Categoria
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = file.file.read()
    svc = BulkUploadService(conn)
    result = svc.bulk_upload_productos(content)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result