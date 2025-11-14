from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from types import SimpleNamespace
from api.database.mssql_connection import get_sql_connection_dep
from api.services.mssql.productos_service import ProductoService
from api.services.mssql.bulk_upload_service import BulkUploadService
from api.config import settings

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

@router.get("/by-sku/{sku}")
def get_producto_by_sku(sku: str, conn = Depends(transac_dep)):
    """Get producto by SKU"""
    svc = ProductoService(conn)
    row = svc.get_producto_by_sku(sku)
    if not row:
        raise HTTPException(status_code=404, detail=f"Producto with SKU '{sku}' not found")
    return row

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_producto(payload: dict = Body(...), conn = Depends(transac_dep)):
    """
    Accept flexible JSON payload. Map 'codigo' or 'sku' to internal attribute.
    """
    data = dict(payload)
    
    # Normalize: prefer 'sku' but accept 'codigo'
    if "sku" not in data and "codigo" in data:
        data["sku"] = data.pop("codigo")
    
    # Ensure required fields
    required = ("sku", "nombre", "categoria")
    missing = [f for f in required if f not in data or data.get(f) is None]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing fields: {', '.join(missing)}")
    
    # Build object with sku attribute for the service
    prod_obj = SimpleNamespace(
        sku=data.get("sku"),
        nombre=data.get("nombre"),
        categoria=data.get("categoria")
    )
    
    svc = ProductoService(conn)
    created = svc.create_producto(prod_obj)
    return created

@router.put("/{producto_id}")
def update_producto(producto_id: int, payload: dict = Body(...), conn = Depends(transac_dep)):
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
    """Bulk upload productos from CSV/JSON/Excel file"""
    allowed = ('.csv', '.json', '.xlsx', '.xls', '.parquet')
    if not file.filename.lower().endswith(allowed):
        raise HTTPException(status_code=400, detail=f"File must be: {', '.join(allowed)}")
    
    content = file.file.read()
    svc = BulkUploadService(conn)
    result = svc.bulk_upload_productos(content, file.filename)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result