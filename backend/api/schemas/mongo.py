from pydantic import BaseModel
from datetime import datetime

# Pydantic models
class ClienteCreate(BaseModel):
    nombre: str
    email: str
    genero: str
    pais: str
    creado: datetime

class ClienteResponse(BaseModel):
    id: str
    nombre: str
    email: str
    genero: str
    pais: str
    creado: datetime

