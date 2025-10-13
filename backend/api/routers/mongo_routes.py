from api.schemas.mongo import ClienteCreate, ClienteResponse, ClienteUpdate
from fastapi import APIRouter, HTTPException, status
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
from typing import List
import pymongo
import os

load_dotenv()
router = APIRouter()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "sales_mongo") 

#---------------------------------------------------------------------------------
# Connection
#---------------------------------------------------------------------------------

try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    print(f"Connected to MongoDB Atlas: {MONGO_DB}")      
    clientes_collection = db.clientes    
    client.admin.command('ping')
    print("MongoDB connection successful")
    
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    raise

def cliente_helper(cliente) -> dict:
    preferencias_array = []
    if cliente.get("preferencias"):
        for categoria, valores in cliente["preferencias"].items():
            if isinstance(valores, list):
                texto = ",".join(valores)
            else:
                texto = str(valores)
            preferencias_array.append({
                "categoria": categoria,
                "texto": texto
            })
    
    return {
        "id": str(cliente["_id"]),
        "nombre": cliente["nombre"],
        "email": cliente["email"],
        "genero": cliente["genero"],
        "pais": cliente["pais"],
        "creado": cliente["creado"],
        "preferencias": preferencias_array
    }
#---------------------------------------------------------------------------------
# Clientes
#---------------------------------------------------------------------------------

@router.post("/clientes", response_model=ClienteResponse)
def create_cliente(cliente: ClienteCreate):
    try:
        cliente_dict = cliente.dict()
        result = clientes_collection.insert_one(cliente_dict)
        created_cliente = clientes_collection.find_one({"_id": result.inserted_id})
        return cliente_helper(created_cliente)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating cliente: {str(e)}")

@router.get("/clientes")
def get_clientes(page: int = 1, limit: int = 20):
    try:
        clientes = []
        skip = (page - 1) * limit
        total = clientes_collection.count_documents({})
        for cliente in clientes_collection.find().skip(skip).limit(limit):
            clientes.append(cliente_helper(cliente))         
        return {
            "data": clientes,
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching clientes: {str(e)}"
        )

@router.get("/clientes/{cliente_id}", response_model=ClienteResponse)
def get_cliente(cliente_id: str):
    try:
        if not ObjectId.is_valid(cliente_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")
            
        cliente = clientes_collection.find_one({"_id": ObjectId(cliente_id)})
        if cliente:
            return cliente_helper(cliente)
        else:
            raise HTTPException(status_code=404, detail="Cliente not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching cliente: {str(e)}"
        )

@router.patch("/clientes/{cliente_id}", response_model=ClienteResponse)
def update_cliente(cliente_id: str, cliente_update: ClienteUpdate):
    try:
        if not ObjectId.is_valid(cliente_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")
            
        # Remove id from update data
        update_data = cliente_update.dict()
        
        result = clientes_collection.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Cliente not found")
            
        # Return updated document
        updated_cliente = clientes_collection.find_one({"_id": ObjectId(cliente_id)})
        return cliente_helper(updated_cliente)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating cliente: {str(e)}"
        )

@router.delete("/clientes/{cliente_id}")
def delete_cliente(cliente_id: str):
    try:
        if not ObjectId.is_valid(cliente_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")
            
        result = clientes_collection.delete_one({"_id": ObjectId(cliente_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Cliente not found")
            
        return {"message": "Cliente deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting cliente: {str(e)}"
        )

#---------------------------------------------------------------------------------
# Productos
#---------------------------------------------------------------------------------



#---------------------------------------------------------------------------------
# Ordenes
#---------------------------------------------------------------------------------
