from fastapi import APIRouter
from .neo4j.clientes import router as clientes_router
from .neo4j.productos import router as productos_router
from .neo4j.ordenes import router as ordenes_router

router = APIRouter()

router.include_router(clientes_router)
router.include_router(productos_router)
router.include_router(ordenes_router)