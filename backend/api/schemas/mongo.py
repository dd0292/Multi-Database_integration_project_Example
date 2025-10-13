from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Cliente
class PreferenciaItem(BaseModel):
    categoria: str
    texto: str


class ClienteCreate(BaseModel):
    nombre: str
    email: EmailStr
    genero: str
    pais: str
    preferencias: Optional[Dict[str, Any]]
    creado: datetime

class ClienteResponse(BaseModel):
    id: str
    nombre: str
    email: EmailStr
    genero: str
    pais: str
    preferencias: Optional[List[PreferenciaItem]]
    creado: datetime

class ClienteUpdate(BaseModel):
    nombre: Optional[str]
    email: Optional[EmailStr]
    genero: Optional[str]
    preferencias: Optional[Dict[str, Any]]
    pais: Optional[str]

