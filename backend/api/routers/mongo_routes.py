from fastapi import APIRouter
from .mongo.clientes import router as clientes_router
from .mongo.productos import router as productos_router
from .mongo.ordenes import router as ordenes_router


router = APIRouter()

router.include_router(clientes_router)
router.include_router(productos_router)
router.include_router(ordenes_router)