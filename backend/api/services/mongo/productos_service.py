from bson import ObjectId
from datetime import datetime
from typing import Optional
from pymongo.collection import Collection
from api.schemas.froms import ProductoFormData


class ProductoService:
    def __init__(self, collection: Collection):
        self.collection = collection
    
    def create_producto(self, producto_data: ProductoFormData) -> dict:
        """Create a new producto"""
        producto_dict = producto_data.model_dump()
        producto_dict["creado"] = datetime.now()
        
        # Handle categoriasAdicionales transformation
        categorias_adicionales = producto_dict.pop("equivalencias", None)
        if categorias_adicionales:
            producto_dict["equivalencias"] = categorias_adicionales
        
        result = self.collection.insert_one(producto_dict)
        created_producto = self.collection.find_one({"_id": result.inserted_id})
        return self._producto_helper(created_producto)
    
    def get_productos(self, page: int = 1, limit: int = 20) -> dict:
        """Get paginated list of productos"""
        productos = []
        skip = (page - 1) * limit
        total = self.collection.count_documents({})
        
        for producto in self.collection.find().skip(skip).limit(limit):
            productos.append(self._producto_helper(producto))
            
        return {
            "data": productos,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit  # Calculate total pages
        }
    
    def get_producto_by_id(self, producto_id: str) -> Optional[dict]:
        """Get a single producto by ID"""
        if not ObjectId.is_valid(producto_id):
            return None
            
        producto = self.collection.find_one({"_id": ObjectId(producto_id)})
        return self._producto_helper(producto) if producto else None
    
    def update_producto(self, producto_id: str, producto_update: ProductoFormData) -> Optional[dict]:
        """Update a producto partially"""
        if not ObjectId.is_valid(producto_id):
            return None
            
        # Convert to dict and remove None values for partial update
        update_data = producto_update.dict(exclude_unset=True)
        
        # Handle categoriasAdicionales transformation
        categorias_adicionales = update_data.pop("categoriasAdicionales", None)
        if categorias_adicionales is not None:  # Include even if empty dict
            update_data["categorias_adicionales"] = categorias_adicionales
        
        # Don't allow updating created timestamp
        if 'creado' in update_data:
            del update_data['creado']
        
        result = self.collection.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
            
        # Return updated document
        updated_producto = self.collection.find_one({"_id": ObjectId(producto_id)})
        return self._producto_helper(updated_producto)
    
    def delete_producto(self, producto_id: str) -> bool:
        """Delete a producto by ID"""
        if not ObjectId.is_valid(producto_id):
            return False
            
        result = self.collection.delete_one({"_id": ObjectId(producto_id)})
        return result.deleted_count > 0
    
    def search_productos(self, query: str, page: int = 1, limit: int = 20) -> dict:
        """Search productos by name or category"""
        productos = []
        skip = (page - 1) * limit
        
        search_filter = {
            "$or": [
                {"nombre": {"$regex": query, "$options": "i"}},
                {"categoria": {"$regex": query, "$options": "i"}}
            ]
        }
        
        total = self.collection.count_documents(search_filter)
        
        for producto in self.collection.find(search_filter).skip(skip).limit(limit):
            productos.append(self._producto_helper(producto))
            
        return {
            "data": productos,
            "total": total,
            "page": page,
            "limit": limit,
            "query": query
        }
    
    def get_productos_by_categoria(self, categoria: str, page: int = 1, limit: int = 20) -> dict:
        """Get productos by category"""
        productos = []
        skip = (page - 1) * limit
        
        filter_criteria = {"categoria": categoria}
        total = self.collection.count_documents(filter_criteria)
        
        for producto in self.collection.find(filter_criteria).skip(skip).limit(limit):
            productos.append(self._producto_helper(producto))
            
        return {
            "data": productos,
            "total": total,
            "page": page,
            "limit": limit,
            "categoria": categoria
        }
    
    def _producto_helper(self, producto) -> dict:
        """Helper function to transform MongoDB document to ProductoResponse format"""
        return {
            "id": str(producto["_id"]),
            "codigo_mongo": producto.get("codigo", ""),
            "nombre": producto["nombre"],
            "categoria": producto["categoria"],
            "equivalencias": {
                "sku": producto["equivalencias"].get("sku"),
                "codigo_alt": producto["equivalencias"].get("codigo_alt")
            } if producto["categoria"] else None
        }