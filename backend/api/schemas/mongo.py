from typing import List, Optional, Dict, Any
from api.schemas.froms import OrdenItem
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Cliente
class PreferenciaItem(BaseModel):
    categoria: str
    texto: str

class ClienteResponse(BaseModel):
    id: str
    nombre: str
    email: EmailStr
    genero: str
    pais: str
    preferencias: Optional[List[PreferenciaItem]]
    creado: datetime

# Producto
class ProductoResponse(BaseModel):
    id: str 
    codigo_mongo: str 
    nombre: str
    categoria: str 
    equivalencias: Optional[dict] 

# Orden
class OrdenResponse(BaseModel):
    id: str 
    cliente_id: str 
    fecha: str 
    canal: str 
    moneda: str
    items: List[OrdenItem] 
    descripcion: Optional[str] 
    total: float
    creado: datetime
    actualizado: datetime