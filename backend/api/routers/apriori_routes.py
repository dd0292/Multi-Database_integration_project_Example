from fastapi import APIRouter
from backend.analytics.apriori.apriori_service import obtener_recomendaciones

router = APIRouter()

@router.get("/recomendar")
def recomendar(productos: str, fuente: str):
    lista = productos.split(",")
    productos_int = [int(x) for x in lista]
    return obtener_recomendaciones(productos_int, fuente)
