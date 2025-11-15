from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional, Dict, Any

class ClienteResponse(BaseModel):
    id: str 
    nombre: str 
    email: str
    genero: str 
    pais: str
    creado: datetime

class CategoriaInfoResponse(BaseModel):
    id: str
    nombre: str 

class ProductoResponse(BaseModel):
    id: str 
    nombre: str 
    categoria: str
    sku: Optional[str] 
    codigo_alt: Optional[str] 
    codigo_mongo: Optional[str] 
    categoria_info: Optional[CategoriaInfoResponse] 

class OrdenItemResponse(BaseModel):
    producto_id: str 
    producto_nombre: str 
    categoria: str
    categoria_info: Optional[CategoriaInfoResponse] 
    cantidad: int 
    precio_unit: float 
    descuento_pct: Optional[float] 
    subtotal: float

class OrdenResponse(BaseModel):
    id: str
    fecha: str 
    canal: str
    moneda: str 
    descripcion: Optional[str]
    total: float 
    cliente: ClienteResponse
    items: List[OrdenItemResponse]