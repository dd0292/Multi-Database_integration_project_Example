from fastapi import APIRouter

from .mssql import clientes as clientes_router
from .mssql import productos as productos_router
from .mssql import ordenes as ordenes_router

router = APIRouter()
router.include_router(clientes_router.router, prefix="/clientes", tags=["Transactional Clientes"])
router.include_router(productos_router.router, prefix="/productos", tags=["Transactional Productos"])
router.include_router(ordenes_router.router, prefix="/ordenes", tags=["Transactional Ordenes"])