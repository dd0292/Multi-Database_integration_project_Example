from bson import ObjectId
from datetime import datetime
from typing import List, Optional, Dict
from pymongo.collection import Collection
from api.schemas.froms import OrdenFormData

class OrdenService:
    def __init__(self, collection: Collection):
        self.collection = collection
    
    def create_orden(self, orden_data: OrdenFormData) -> dict:
        """Create a new orden"""
        orden_dict = orden_data.model_dump()
        
        # Add timestamps
        now = datetime.now()
        orden_dict["creado"] = now
        orden_dict["actualizado"] = now
        
        # Calculate total
        total = self._calculate_total(orden_dict["items"])
        orden_dict["total"] = round(total, 2)
        
        result = self.collection.insert_one(orden_dict)
        created_orden = self.collection.find_one({"_id": result.inserted_id})
        return self._orden_helper(created_orden)
    
    def get_ordenes(self, page: int = 1, limit: int = 20) -> dict:
        """Get paginated list of ordenes"""
        ordenes = []
        skip = (page - 1) * limit
        total = self.collection.count_documents({})
        
        for orden in self.collection.find().skip(skip).limit(limit):
            ordenes.append(self._orden_helper(orden))
            
        return {
            "data": ordenes,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    def get_orden_by_id(self, orden_id: str) -> Optional[dict]:
        """Get a single orden by ID"""
        if not ObjectId.is_valid(orden_id):
            return None
            
        orden = self.collection.find_one({"_id": ObjectId(orden_id)})
        return self._orden_helper(orden) if orden else None
    
    def update_orden(self, orden_id: str, orden_update: OrdenFormData) -> Optional[dict]:
        """Update an orden partially"""
        if not ObjectId.is_valid(orden_id):
            return None
            
        # Convert to dict and remove None values for partial update
        update_data = orden_update.model_dump(exclude_unset=True)
        
        # Recalculate total if items are updated
        if "items" in update_data:
            total = self._calculate_total(update_data["items"])
            update_data["total"] = round(total, 2)
        
        # Update timestamp
        update_data["actualizado"] = datetime.now()
        
        # Don't update 'creado' field when patching
        if 'creado' in update_data:
            del update_data['creado']
        
        result = self.collection.update_one(
            {"_id": ObjectId(orden_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
            
        # Return updated document
        updated_orden = self.collection.find_one({"_id": ObjectId(orden_id)})
        return self._orden_helper(updated_orden)
    
    def delete_orden(self, orden_id: str) -> bool:
        """Delete an orden by ID"""
        if not ObjectId.is_valid(orden_id):
            return False
            
        result = self.collection.delete_one({"_id": ObjectId(orden_id)})
        return result.deleted_count > 0
    
    def get_ordenes_by_cliente(self, cliente_id: str, page: int = 1, limit: int = 20) -> dict:
        """Get ordenes by cliente ID"""
        ordenes = []
        skip = (page - 1) * limit
        
        filter_criteria = {"cliente_id": cliente_id}
        total = self.collection.count_documents(filter_criteria)
        
        for orden in self.collection.find(filter_criteria).skip(skip).limit(limit):
            ordenes.append(self._orden_helper(orden))
            
        return {
            "data": ordenes,
            "total": total,
            "page": page,
            "limit": limit,
            "cliente_id": cliente_id
        }
    
    def get_ordenes_by_fecha(self, fecha_inicio: datetime, fecha_fin: datetime, page: int = 1, limit: int = 20) -> dict:
        """Get ordenes by date range"""
        ordenes = []
        skip = (page - 1) * limit
        
        filter_criteria = {
            "fecha": {
                "$gte": fecha_inicio,
                "$lte": fecha_fin
            }
        }
        
        total = self.collection.count_documents(filter_criteria)
        
        for orden in self.collection.find(filter_criteria).skip(skip).limit(limit):
            ordenes.append(self._orden_helper(orden))
            
        return {
            "data": ordenes,
            "total": total,
            "page": page,
            "limit": limit,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        }
    
    def get_ordenes_stats(self) -> dict:
        """Get ordenes statistics"""
        total_ordenes = self.collection.count_documents({})
        
        # Get total revenue
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$total"},
                    "avg_order_value": {"$avg": "$total"},
                    "min_order_value": {"$min": "$total"},
                    "max_order_value": {"$max": "$total"}
                }
            }
        ]
        
        stats = list(self.collection.aggregate(pipeline))
        
        if stats:
            return {
                "total_ordenes": total_ordenes,
                "total_revenue": stats[0].get("total_revenue", 0),
                "avg_order_value": round(stats[0].get("avg_order_value", 0), 2),
                "min_order_value": stats[0].get("min_order_value", 0),
                "max_order_value": stats[0].get("max_order_value", 0)
            }
        else:
            return {
                "total_ordenes": total_ordenes,
                "total_revenue": 0,
                "avg_order_value": 0,
                "min_order_value": 0,
                "max_order_value": 0
            }
    
    def _calculate_total(self, items: List[Dict]) -> float:
        """Calculate total from order items"""
        total = 0
        for item in items:
            precio_final = item["precio_unit"]
            if item.get("descuento_pct"):
                precio_final = item["precio_unit"] * (1 - item["descuento_pct"] / 100)
            total += precio_final * item["cantidad"]
        return total
    
    def _orden_helper(self, orden) -> dict:
        """Helper function to transform MongoDB document to OrdenResponse format"""
        # Recalculate total to ensure consistency
        total = self._calculate_total(orden["items"])
        
        return {
            "id": str(orden["_id"]),
            "cliente_id": orden["cliente_id"],
            "fecha": orden["fecha"],
            "canal": orden["canal"],
            "moneda": orden["moneda"],
            "items": orden["items"],
            "descripcion": orden.get("descripcion"),
            "total": round(total, 2),
            "creado": orden.get("creado", datetime.now()),
            "actualizado": orden.get("actualizado", datetime.now())
        }