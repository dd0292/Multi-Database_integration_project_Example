from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime, date


# ==================== CLIENTE ====================
class ClienteFormData(BaseModel):
    """Form data for creating/updating a cliente in Supabase.
    
    Note: Supabase cliente table has columns:
    - cliente_id (UUID, PK)
    - nombre (TEXT)
    - email (TEXT, UNIQUE)
    - genero (CHAR(1)) - 'M' or 'F'
    - pais (TEXT)
    - fecha_registro (DATE)
    """
    nombre: str
    email: EmailStr
    genero: str  # 'M' or 'F'
    pais: str


class ClienteResponse(BaseModel):
    """Response model for a cliente from Supabase."""
    cliente_id: str
    nombre: str
    email: str
    genero: str
    pais: str
    fecha_registro: Optional[date] = None


# ==================== PRODUCTO ====================
class ProductoFormData(BaseModel):
    """Form data for creating/updating a producto in Supabase.
    
    Note: Supabase producto table has columns:
    - producto_id (UUID, PK)
    - sku (TEXT, UNIQUE, nullable)
    - nombre (TEXT)
    - categoria (TEXT)
    """
    nombre: str
    categoria: str
    sku: Optional[str] = None


class ProductoResponse(BaseModel):
    """Response model for a producto from Supabase."""
    producto_id: str
    nombre: str
    categoria: str
    sku: Optional[str] = None


# ==================== ORDEN ====================
class OrdenItemData(BaseModel):
    """Item within an orden."""
    producto_id: str
    cantidad: int
    precio_unit: float


class OrdenFormData(BaseModel):
    """Form data for creating/updating an orden in Supabase.
    
    Note: Supabase orden table has columns:
    - orden_id (UUID, PK)
    - cliente_id (UUID, FK)
    - fecha (TIMESTAMPTZ)
    - canal (TEXT) - 'WEB', 'APP', or 'PARTNER'
    - moneda (CHAR(3)) - 'USD', 'CRC', etc.
    - total (NUMERIC(18,2))
    """
    cliente_id: str
    canal: str  # 'WEB', 'APP', 'PARTNER'
    moneda: str  # 'USD', 'CRC', etc.
    total: float
    fecha: Optional[str] = None
    items: Optional[list[OrdenItemData]] = None


class OrdenResponse(BaseModel):
    """Response model for an orden from Supabase."""
    orden_id: str
    cliente_id: str
    fecha: Optional[datetime] = None
    canal: str
    moneda: str
    total: float
    items: Optional[list[OrdenItemData]] = None
