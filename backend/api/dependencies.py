# Mongo dependencies
from fastapi import Depends
from api.database.mongo_connection import get_clientes_collection, get_productos_collection, get_ordenes_collection
from api.services.mongo.ordenes_service import OrdenMongoService
from api.services.mongo.clientes_service import ClienteMongoService
from api.services.mongo.productos_service import ProductoMongoService

def get_mongo_clientes_service() -> ClienteMongoService:
    return ClienteMongoService(get_clientes_collection())

def get_mongo_productos_service() -> ProductoMongoService:
    return ProductoMongoService(get_productos_collection())

def get_mongo_ordenes_service() -> OrdenMongoService:
    return OrdenMongoService(get_ordenes_collection())

# MSSQL dependencies

# Supabase dependencies

# Neo4j dependencies

from api.database.neo4j_connection import get_session
from api.services.neo4j.ordenes_service import OrdenNeo4jService
from api.services.neo4j.clientes_service import ClienteNeo4jService
from api.services.neo4j.productos_service import ProductoNeo4jService

def get_neo4j_clientes_service(session = Depends(get_session)):
    return ClienteNeo4jService(session)

def get_neo4j_productos_service(session = Depends(get_session)):
    return ProductoNeo4jService(session)

def get_neo4j_ordenes_service(session = Depends(get_session)):
    return OrdenNeo4jService(session)

# MySQL dependencies

