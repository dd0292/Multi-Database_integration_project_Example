from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class Preferencia(BaseModel):
    categoria: str = Field(..., min_length=1, description="Categoría de la preferencia")
    texto: str = Field(..., description="Texto o valores de la preferencia")

class ClienteFormData(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del cliente")
    email: EmailStr = Field(..., description="Email válido del cliente")
    genero: str = Field(..., min_length=1, description="Género del cliente")
    pais: str = Field(..., min_length=1, description="País del cliente")
    preferencias: Optional[Dict[str, Any]] = Field(None,description="Lista opcional de preferencias del cliente")

class ProductoFormData(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del producto")
    categoria: str = Field(..., min_length=1, description="Categoría principal del producto")
    codigo: str = Field(..., min_length=1, description="Código único del producto")
    categoriasAdicionales: Optional[Dict[str, str]] = Field(None,description="Categorías adicionales como clave-valor")

# OrdenItem Model
class OrdenItem(BaseModel):
    producto_id: str = Field(..., description="ID del producto")
    cantidad: int = Field(..., ge=1, description="Cantidad del producto")
    precio_unit: float = Field(..., ge=0, description="Precio unitario del producto")
    descuento_pct: Optional[float] = Field(None, ge=0, le=100, description="Porcentaje de descuento (0-100)")

# OrdenFormData Model
class OrdenFormData(BaseModel):
    cliente_id: str = Field(..., description="ID del cliente")
    fecha: str = Field(..., description="Fecha de la orden")
    canal: str = Field(..., description="Canal de venta")
    moneda: str = Field(..., description="Tipo de moneda")
    items: List[OrdenItem] = Field(..., min_items=1, description="Lista de items de la orden")
    descripcion: Optional[str] = Field(None, description="Descripción adicional de la orden")