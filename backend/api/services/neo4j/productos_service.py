from datetime import datetime
from typing import Optional, Dict, List, Any
from api.schemas.froms import ProductoFormData

class ProductoNeo4jService:
    def __init__(self, session):
        self.session = session
    
    def create_producto(self, producto_data: ProductoFormData) -> Optional[dict]:
        """Create a new producto with categoria relationship"""
        producto_dict = producto_data.model_dump()
        
        # Extract and transform equivalencias to sku and codigo_alt
        equivalencias = producto_dict.pop("equivalencias", {})
        sku = equivalencias.get("sku", "")
        codigo_alt = equivalencias.get("codigo_alt", "")
        codigo_mongo = producto_dict.get("codigo", "")
        
        query = """
        // Create or find categoria
        MERGE (cat:Categoria {nombre: $categoria})
        ON CREATE SET cat.id = randomUUID()
        
        // Create producto
        CREATE (p:Producto {
            id: randomUUID(),
            nombre: $nombre,
            categoria: $categoria,
            sku: $sku,
            codigo_alt: $codigo_alt,
            codigo_mongo: $codigo_mongo
        })
        
        // Create relationship to categoria
        CREATE (p)-[:PERTENECE_A]->(cat)
        
        RETURN p, cat
        """
        
        params = {
            "nombre": producto_dict["nombre"],
            "categoria": producto_dict["categoria"],
            "sku": sku,
            "codigo_alt": codigo_alt,
            "codigo_mongo": codigo_mongo
        }
        
        result = self.session.run(query, params)
        record = result.single()
        
        if record:
            producto_node = record["p"]
            return self._producto_helper(producto_node)
        return None
    
    def get_productos(self, page: int = 1, limit: int = 20) -> dict:
        """Get paginated list of productos with their categorias"""
        skip = (page - 1) * limit
        
        # Count query
        count_query = "MATCH (p:Producto) RETURN count(p) as total"
        count_result = self.session.run(count_query)
        total = count_result.single()["total"]
        
        # Data query with categoria
        data_query = """
        MATCH (p:Producto)-[:PERTENECE_A]->(c:Categoria)
        RETURN p, c
        ORDER BY p.nombre
        SKIP $skip LIMIT $limit
        """
        
        result = self.session.run(data_query, skip=skip, limit=limit)
        productos = []
        
        for record in result:
            producto_node = record["p"]
            categoria_node = record["c"]
            producto = self._producto_helper(producto_node)
            producto["categoria_info"] = {
                "id": dict(categoria_node.items()).get("id"),
                "nombre": dict(categoria_node.items()).get("nombre")
            }
            productos.append(producto)
        
        return {
            "data": productos,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    def get_producto_by_id(self, producto_id: str) -> Optional[dict]:
        """Get a single producto by ID with categoria"""
        query = """
        MATCH (p:Producto {id: $producto_id})-[:PERTENECE_A]->(c:Categoria)
        RETURN p, c
        """
        
        result = self.session.run(query, producto_id=producto_id)
        record = result.single()
        
        if not record:
            return None
        
        producto_node = record["p"]
        categoria_node = record["c"]
        producto = self._producto_helper(producto_node)
        producto["categoria_info"] = {
            "id": dict(categoria_node.items()).get("id"),
            "nombre": dict(categoria_node.items()).get("nombre")
        }
        
        return producto
    
    def update_producto(self, producto_id: str, producto_update: ProductoFormData) -> Optional[dict]:
        """Update a producto and its categoria relationship"""
        existing_producto = self.get_producto_by_id(producto_id)
        if not existing_producto:
            return None
        
        update_data = producto_update.model_dump(exclude_unset=True)
        equivalencias = update_data.pop("equivalencias", {})
        sku = equivalencias.get("sku", "")
        codigo_alt = equivalencias.get("codigo_alt", "")
        
        query = """
        // Update producto properties
        MATCH (p:Producto {id: $producto_id})
        SET p.nombre = $nombre,
            p.categoria = $categoria,
            p.sku = $sku,
            p.codigo_alt = $codigo_alt,
            p.codigo_mongo = $codigo_mongo
        
        // Handle categoria relationship
        WITH p
        MATCH (p)-[rel:PERTENECE_A]->(old_cat:Categoria)
        DELETE rel
        
        WITH p
        MERGE (new_cat:Categoria {nombre: $categoria})
        ON CREATE SET new_cat.id = randomUUID()
        CREATE (p)-[:PERTENECE_A]->(new_cat)
        
        RETURN p, new_cat
        """
        
        params = {
            "producto_id": producto_id,
            "nombre": update_data["nombre"],
            "categoria": update_data["categoria"],
            "sku": sku,
            "codigo_alt": codigo_alt,
            "codigo_mongo": update_data["codigo"]
        }
        
        result = self.session.run(query, params)
        record = result.single()
        
        if record:
            producto_node = record["p"]
            categoria_node = record["new_cat"]
            producto = self._producto_helper(producto_node)
            producto["categoria_info"] = {
                "id": dict(categoria_node.items()).get("id"),
                "nombre": dict(categoria_node.items()).get("nombre")
            }
            return producto
        return None
    
    def delete_producto(self, producto_id: str) -> bool:
        """Delete a producto by ID"""
        existing_producto = self.get_producto_by_id(producto_id)
        if not existing_producto:
            return False
        
        query = """
        MATCH (p:Producto {id: $producto_id})
        DETACH DELETE p
        """
        
        result = self.session.run(query, producto_id=producto_id)
        summary = result.consume()
        return summary.counters.nodes_deleted > 0
    
    def search_productos(self, query: str, page: int = 1, limit: int = 20) -> dict:
        """Search productos by name, category, or codigo"""
        skip = (page - 1) * limit
        
        search_query = """
        MATCH (p:Producto)-[:PERTENECE_A]->(c:Categoria)
        WHERE p.nombre CONTAINS $query 
           OR p.categoria CONTAINS $query
           OR p.sku CONTAINS $query
           OR p.codigo_alt CONTAINS $query
           OR p.codigo_mongo CONTAINS $query
        RETURN p, c
        ORDER BY p.nombre
        SKIP $skip LIMIT $limit
        """
        
        count_query = """
        MATCH (p:Producto)
        WHERE p.nombre CONTAINS $query 
           OR p.categoria CONTAINS $query
           OR p.sku CONTAINS $query
           OR p.codigo_alt CONTAINS $query
           OR p.codigo_mongo CONTAINS $query
        RETURN count(p) as total
        """
        
        count_result = self.session.run(count_query, query=query)
        total = count_result.single()["total"]
        
        result = self.session.run(search_query, query=query, skip=skip, limit=limit)
        productos = []
        
        for record in result:
            producto_node = record["p"]
            categoria_node = record["c"]
            producto = self._producto_helper(producto_node)
            producto["categoria_info"] = {
                "id": dict(categoria_node.items()).get("id"),
                "nombre": dict(categoria_node.items()).get("nombre")
            }
            productos.append(producto)
        
        return {
            "data": productos,
            "total": total,
            "page": page,
            "limit": limit,
            "query": query
        }
    
    def get_productos_by_categoria(self, categoria: str, page: int = 1, limit: int = 20) -> dict:
        """Get productos by category name"""
        skip = (page - 1) * limit
        
        count_query = """
        MATCH (p:Producto)-[:PERTENECE_A]->(c:Categoria {nombre: $categoria})
        RETURN count(p) as total
        """
        count_result = self.session.run(count_query, categoria=categoria)
        total = count_result.single()["total"]
        
        data_query = """
        MATCH (p:Producto)-[:PERTENECE_A]->(c:Categoria {nombre: $categoria})
        RETURN p, c
        ORDER BY p.nombre
        SKIP $skip LIMIT $limit
        """
        
        result = self.session.run(data_query, categoria=categoria, skip=skip, limit=limit)
        productos = []
        
        for record in result:
            producto_node = record["p"]
            categoria_node = record["c"]
            producto = self._producto_helper(producto_node)
            producto["categoria_info"] = {
                "id": dict(categoria_node.items()).get("id"),
                "nombre": dict(categoria_node.items()).get("nombre")
            }
            productos.append(producto)
        
        return {
            "data": productos,
            "total": total,
            "page": page,
            "limit": limit,
            "categoria": categoria
        }
    
    def create_equivalencia(self, producto_id1: str, producto_id2: str) -> bool:
        """Create EQUIVALE_A relationship between two productos"""
        query = """
        MATCH (p1:Producto {id: $producto_id1}), (p2:Producto {id: $producto_id2})
        WHERE p1 <> p2
        MERGE (p1)-[:EQUIVALE_A]->(p2)
        RETURN p1, p2
        """
        
        result = self.session.run(query, producto_id1=producto_id1, producto_id2=producto_id2)
        return result.single() is not None
    
    def get_equivalentes(self, producto_id: str) -> List[dict]:
        """Get all equivalent productos"""
        query = """
        MATCH (p:Producto {id: $producto_id})-[:EQUIVALE_A]->(equiv:Producto)
        RETURN equiv
        """
        
        result = self.session.run(query, producto_id=producto_id)
        return [self._producto_helper(record["equiv"]) for record in result]
    
    def _producto_helper(self, producto_node) -> dict:
        """Helper function to transform Neo4j node to response format"""
        if not producto_node:
            return None
            
        properties = dict(producto_node.items())
        
        return {
            "id": properties.get("id"),
            "nombre": properties.get("nombre"),
            "categoria": properties.get("categoria"),
            "sku": properties.get("sku"),
            "codigo_alt": properties.get("codigo_alt"),
            "codigo_mongo": properties.get("codigo_mongo")
        }