from api.database.mongo_connection import get_clientes_collection, get_productos_collection, get_ordenes_collection
from api.services.mongo.clientes_service import ClienteService
from api.services.mongo.ordenes_service import OrdenService
from api.services.mongo.productos_service import ProductoService
from api.database.supabase_connection import get_supabase_client
from api.services.supabase.clientes_service import ClienteService as SupabaseClienteService

def get_mongo_clientes_service() -> ClienteService:
    return ClienteService(get_clientes_collection())

def get_mongo_productos_service() -> ProductoService:
    return ProductoService(get_productos_collection())

def get_mongo_ordenes_service() -> OrdenService:
    return OrdenService(get_ordenes_collection())

# MSSQL dependencies

# Supabase dependencies
from api.services.supabase.productos_service import ProductoService as SupabaseProductoService
from api.services.supabase.ordenes_service import OrdenService as SupabaseOrdenService

def get_supabase_productos_service() -> SupabaseProductoService:
    return SupabaseProductoService(get_supabase_client())

def get_supabase_ordenes_service() -> SupabaseOrdenService:
    return SupabaseOrdenService(get_supabase_client())

def get_supabase_clientes_service() -> SupabaseClienteService:
    """Provide a Supabase-backed ClienteService for dependency injection in routers."""
    return SupabaseClienteService(get_supabase_client())

# Neo4j dependencies

# MySQL dependencies

