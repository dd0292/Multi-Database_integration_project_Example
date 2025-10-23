from api.database.mongo_connection import get_clientes_collection, get_productos_collection, get_ordenes_collection
from api.services.mongo.clientes_service import ClienteService
from api.services.mongo.ordenes_service import OrdenService
from api.services.mongo.productos_service import ProductoService

def get_mongo_clientes_service() -> ClienteService:
    return ClienteService(get_clientes_collection())

def get_mongo_productos_service() -> ProductoService:
    return ProductoService(get_productos_collection())

def get_mongo_ordenes_service() -> OrdenService:
    return OrdenService(get_ordenes_collection())

# MSSQL dependencies

# Supabase dependencies

# Neo4j dependencies

# MySQL dependencies

