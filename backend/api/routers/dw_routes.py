from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from api.config import settings
from api.database.mssql_connection import get_sql_connection_dep

from .dw import dimcliente, dimproducto, dimtiempo, factventas

router = APIRouter()
router.include_router(dimcliente.router, prefix="/dimcliente", tags=["DW DimCliente"])
router.include_router(dimproducto.router, prefix="/dimproducto", tags=["DW DimProducto"])
router.include_router(dimtiempo.router, prefix="/dimtiempo", tags=["DW DimTiempo"])
router.include_router(factventas.router, prefix="/factventas", tags=["DW FactVentas"])

