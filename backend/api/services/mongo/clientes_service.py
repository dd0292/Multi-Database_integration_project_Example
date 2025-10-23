from bson import ObjectId
from datetime import datetime
from typing import Optional
from api.schemas.froms import ClienteFormData


class ClienteService:
    def __init__(self, collection):
        self.collection = collection
    
    def create_cliente(self, cliente_data: ClienteFormData) -> dict:
        cliente_dict = cliente_data.model_dump()
        cliente_dict["creado"] = datetime.now()

        result = self.collection.insert_one(cliente_dict)
        created_cliente = self.collection.find_one({"_id": result.inserted_id})
        return self._cliente_helper(created_cliente)
    
    def get_clientes(self, page: int = 1, limit: int = 20) -> dict:
        clientes = []
        skip = (page - 1) * limit
        total = self.collection.count_documents({})
        
        for cliente in self.collection.find().skip(skip).limit(limit):
            clientes.append(self._cliente_helper(cliente))
            
        return {"data": clientes, "total": total}
    
    def get_cliente_by_id(self, cliente_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(cliente_id):
            return None
            
        cliente = self.collection.find_one({"_id": ObjectId(cliente_id)})
        return self._cliente_helper(cliente) if cliente else None
    
    def update_cliente(self, cliente_id: str, cliente_update: ClienteFormData) -> Optional[dict]:
        if not ObjectId.is_valid(cliente_id):
            return None
            
        update_data = cliente_update.model_dump(exclude_unset=True)
        if 'creado' in update_data:
            del update_data['creado']
        
        result = self.collection.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
            
        updated_cliente = self.collection.find_one({"_id": ObjectId(cliente_id)})
        return self._cliente_helper(updated_cliente)
    
    def delete_cliente(self, cliente_id: str) -> bool:
        if not ObjectId.is_valid(cliente_id):
            return False
            
        result = self.collection.delete_one({"_id": ObjectId(cliente_id)})
        return result.deleted_count > 0
    
    def _cliente_helper(self, cliente) -> dict:
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
            "creado": cliente.get("creado", datetime.now()),
            "preferencias": preferencias_array
        }