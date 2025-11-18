from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.services.mysql.cliente_service import ClienteMySQLService
from api.services.mysql.producto_service import ProductoMySQLService
from api.services.mysql.orden_service import OrdenMySQLService
from api.services.mysql.orden_detalle_service import OrdenDetalleMySQLService

router = APIRouter()

class LoaderPayload(BaseModel):
    table: str
    rows: list[dict]

services = {
    "cliente": ClienteMySQLService(),
    "producto": ProductoMySQLService(),
    "orden": OrdenMySQLService(),
    "orden_detalle": OrdenDetalleMySQLService()
}

@router.post("/loader/upload")
async def upload_to_mysql(payload: LoaderPayload):

    table = payload.table.lower()

    if table not in services:
        raise HTTPException(status_code=400, detail="Tabla no soportada.")

    try:
        inserted = services[table].insert_rows(payload.rows)
        return {"status": "ok", "table": table, "inserted": inserted}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
