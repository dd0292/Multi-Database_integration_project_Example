from datetime import datetime
from typing import Optional, Dict, List, Any
from api.schemas.froms import ProductoFormData

class ProductoNeo4jService:
    def __init__(self, session):
        self.session = session

    # ----------------------------------------------------
    # CREATE PRODUCTO
    # ----------------------------------------------------
    def create_producto(self, producto_data: ProductoFormData) -> Optional[dict]:
        """Create a new producto with categoria relationship"""
        producto_dict = producto_data.model_dump()
        producto_dict["creado"] = datetime.now().isoformat()

        # Extract equivalencias
        equivalencias = producto_dict.pop("equivalencias", {})
        codigo_alt = equivalencias.get("codigo_alt", "")
        codigo_mongo = equivalencias.get("codigo_mongo", "")

        query = """
        // Create or find categoria
        MERGE (cat:Categoria {nombre: $categoria})
        ON CREATE SET cat.id = randomUUID()

        // Create producto (no categoria property)
        CREATE (p:Producto {
            id: randomUUID(),
            nombre: $nombre,
            sku: $sku,
            creado: $creado,
            actualizado: null,
            codigo_alt: $codigo_alt,
            codigo_mongo: $codigo_mongo
        })

        // Relationship
        CREATE (p)-[:PERTENECE_A]->(cat)

        RETURN p, cat
        """

        params = {
            "nombre": producto_dict["nombre"],
            "categoria": producto_dict["categoria"],
            "sku": producto_dict["codigo"],
            "creado": producto_dict["creado"],
            "codigo_alt": codigo_alt,
            "codigo_mongo": codigo_mongo
        }

        result = self.session.run(query, params)
        record = result.single()

        if record:
            producto_node = record["p"]
            categoria_node = record["cat"]
            producto = self._producto_helper(producto_node)
            producto["categoria_info"] = {
                "id": categoria_node.get("id"),
                "nombre": categoria_node.get("nombre")
            }
            return producto

        return None

    # ----------------------------------------------------
    # GET PRODUCTOS
    # ----------------------------------------------------
    def get_productos(self, page: int = 1, limit: int = 20) -> dict:
        skip = (page - 1) * limit

        count_result = self.session.run("MATCH (p:Producto) RETURN count(p) AS total")
        total = count_result.single()["total"]

        query = """
        MATCH (p:Producto)-[:PERTENECE_A]->(c:Categoria)
        RETURN p, c
        ORDER BY p.nombre
        SKIP $skip LIMIT $limit
        """

        result = self.session.run(query, skip=skip, limit=limit)

        productos = []
        for record in result:
            producto = self._producto_helper(record["p"])
            categoria = dict(record["c"].items())
            producto["categoria_info"] = {
                "id": categoria.get("id"),
                "nombre": categoria.get("nombre")
            }
            productos.append(producto)

        return {
            "data": productos,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }

    # ----------------------------------------------------
    # GET BY ID
    # ----------------------------------------------------
    def get_producto_by_id(self, producto_id: str) -> Optional[dict]:
        query = """
        MATCH (p:Producto {id: $producto_id})-[:PERTENECE_A]->(c:Categoria)
        RETURN p, c
        """

        record = self.session.run(query, producto_id=producto_id).single()
        if not record:
            return None

        producto = self._producto_helper(record["p"])
        categoria = dict(record["c"].items())
        producto["categoria_info"] = {
            "id": categoria.get("id"),
            "nombre": categoria.get("nombre")
        }
        return producto

    # ----------------------------------------------------
    # UPDATE PRODUCTO
    # ----------------------------------------------------
    def update_producto(self, producto_id: str, producto_update: ProductoFormData) -> Optional[dict]:
        existing = self.get_producto_by_id(producto_id)
        if not existing:
            return None

        update_data = producto_update.model_dump()
        equivalencias = update_data.pop("equivalencias", {})
        codigo_alt = equivalencias.get("codigo_alt", "")
        codigo_mongo = equivalencias.get("codigo_mongo", "")

        query = """
        MATCH (p:Producto {id: $producto_id})
        SET p.nombre = $nombre,
            p.sku = $sku,
            p.codigo_alt = $codigo_alt,
            p.codigo_mongo = $codigo_mongo,
            p.actualizado = $actualizado

        WITH p
        MATCH (p)-[r:PERTENECE_A]->(old_cat:Categoria)
        DELETE r

        WITH p
        MERGE (new_cat:Categoria {nombre: $categoria})
        ON CREATE SET new_cat.id = randomUUID()
        CREATE (p)-[:PERTENECE_A]->(new_cat)

        RETURN p, new_cat
        """

        params = {
            "producto_id": producto_id,
            "nombre": update_data["nombre"],
            "sku": update_data["codigo"],
            "categoria": update_data["categoria"],
            "codigo_alt": codigo_alt,
            "codigo_mongo": codigo_mongo,
            "actualizado": datetime.now().isoformat()
        }

        record = self.session.run(query, params).single()
        if not record:
            return None

        producto = self._producto_helper(record["p"])
        categoria = dict(record["new_cat"].items())
        producto["categoria_info"] = {
            "id": categoria.get("id"),
            "nombre": categoria.get("nombre")
        }
        return producto

    # ----------------------------------------------------
    # DELETE PRODUCTO
    # ----------------------------------------------------
    def delete_producto(self, producto_id: str) -> bool:
        query = "MATCH (p:Producto {id: $producto_id}) DETACH DELETE p"
        summary = self.session.run(query, producto_id=producto_id).consume()
        return summary.counters.nodes_deleted > 0

    # ----------------------------------------------------
    # HELPERS
    # ----------------------------------------------------
    def _producto_helper(self, producto_node) -> dict:
        props = dict(producto_node.items())
        return {
            "id": props.get("id"),
            "nombre": props.get("nombre"),
            "sku": props.get("sku"),
            "codigo_alt": props.get("codigo_alt"),
            "codigo_mongo": props.get("codigo_mongo"),
            "creado": props.get("creado"),
            "actualizado": props.get("actualizado")
        }
