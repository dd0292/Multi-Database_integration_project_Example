from fastapi import APIRouter

from .sqlserver import clientes, productos, ordenes

router = APIRouter()
router.include_router(clientes.router, prefix="/clientes", tags=["SQLServer Clientes"])
router.include_router(productos.router, prefix="/productos", tags=["SQLServer Productos"])
router.include_router(ordenes.router, prefix="/ordenes", tags=["SQLServer Ordenes"])