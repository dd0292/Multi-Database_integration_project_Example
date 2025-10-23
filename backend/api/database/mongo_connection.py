import pymongo
from api.config import settings

class MongoDBConnection:
    _client = None
    _db = None
    
    @classmethod
    def get_client(cls):
        if cls._client is None:
            try:
                cls._client = pymongo.MongoClient(settings.MONGO_URI)
                cls._client.admin.command('ping')
                print("MongoDB connection successful")
            except Exception as e:
                print(f"MongoDB connection failed: {e}")
                raise
        return cls._client
    
    @classmethod
    def get_db(cls):
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[settings.MONGO_DB]
        return cls._db

def get_clientes_collection():
    return MongoDBConnection.get_db().clientes

def get_productos_collection():
    return MongoDBConnection.get_db().productos

def get_ordenes_collection():
    return MongoDBConnection.get_db().ordenes