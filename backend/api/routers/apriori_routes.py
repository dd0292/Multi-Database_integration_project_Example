from fastapi import APIRouter
from analytics.apriori.apriori_service import obtener_recomendaciones

router = APIRouter()

@router.get("/recomendar")
def recomendar(productos: str, fuente: str):
    lista = productos.split(",")
    return obtener_recomendaciones(lista, fuente)
