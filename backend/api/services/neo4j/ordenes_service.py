from datetime import datetime
from typing import Optional, List, Dict, Any
from api.schemas.froms import OrdenFormData

class OrdenNeo4jService:
    def __init__(self, session):
        self.session = session
    
    def create_orden(self, orden_data: OrdenFormData) -> Optional[dict]:
        """Create a new orden with relationships to Cliente and Productos"""
        orden_dict = orden_data.model_dump()
        
        # Calculate total
        total = self._calculate_total(orden_dict["items"])
        
        query = """
        // Create the orden node
        CREATE (o:Orden {
            id: randomUUID(),
            fecha: $fecha,
            canal: $canal,
            moneda: $moneda,
            descripcion: $descripcion,
            total: $total
        })
        
        // Link to cliente (using REALIZO instead of REALIZA)
        WITH o
        MATCH (c:Cliente {id: $cliente_id})
        CREATE (c)-[:REALIZO]->(o)
        
        // Create items and link to productos (with properties on relationship)
        WITH o
        UNWIND $items as item
        MATCH (p:Producto {id: item.producto_id})
        CREATE (o)-[:CONTIENE {
            cantidad: item.cantidad,
            precio_unit: item.precio_unit,
            descuento_pct: item.descuento_pct
        }]->(p)
        
        RETURN o
        """
        
        params = {
            "cliente_id": orden_dict["cliente_id"],
            "fecha": orden_dict["fecha"],
            "canal": orden_dict["canal"],
            "moneda": orden_dict["moneda"],
            "descripcion": orden_dict.get("descripcion"),
            "total": total,
            "items": orden_dict["items"]
        }
        
        result = self.session.run(query, params)
        record = result.single()
        
        if record:
            orden_node = record["o"]
            return self.get_orden_by_id(dict(orden_node.items()).get("id"))
        return None
    
    def get_ordenes(self, page: int = 1, limit: int = 20) -> dict:
        """Get paginated list of ordenes with complete details"""
        skip = (page - 1) * limit
        
        # Count query
        count_query = "MATCH (o:Orden) RETURN count(o) as total"
        count_result = self.session.run(count_query)
        total = count_result.single()["total"]
        
        # Data query with all relationships
        data_query = """
        MATCH (c:Cliente)-[:REALIZO]->(o:Orden)
        OPTIONAL MATCH (o)-[contiene:CONTIENE]->(p:Producto)
        OPTIONAL MATCH (p)-[:PERTENECE_A]->(cat:Categoria)
        RETURN o, c, 
               COLLECT({
                 producto: p,
                 categoria: cat,
                 cantidad: contiene.cantidad,
                 precio_unit: contiene.precio_unit,
                 descuento_pct: contiene.descuento_pct
               }) as items
        ORDER BY o.fecha DESC
        SKIP $skip LIMIT $limit
        """
        
        result = self.session.run(data_query, skip=skip, limit=limit)
        ordenes = [self._build_orden_response(record) for record in result]
        
        return {
            "data": ordenes,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    def get_orden_by_id(self, orden_id: str) -> Optional[dict]:
        """Get a single orden by ID with complete details"""
        query = """
        MATCH (c:Cliente)-[:REALIZO]->(o:Orden {id: $orden_id})
        OPTIONAL MATCH (o)-[contiene:CONTIENE]->(p:Producto)
        OPTIONAL MATCH (p)-[:PERTENECE_A]->(cat:Categoria)
        RETURN o, c, 
               COLLECT({
                 producto: p,
                 categoria: cat,
                 cantidad: contiene.cantidad,
                 precio_unit: contiene.precio_unit,
                 descuento_pct: contiene.descuento_pct
               }) as items
        """
        
        result = self.session.run(query, orden_id=orden_id)
        record = result.single()
        
        return self._build_orden_response(record) if record else None
    
    def update_orden(self, orden_id: str, orden_update: OrdenFormData) -> Optional[dict]:
        """Update an orden and its relationships"""
        existing_orden = self.get_orden_by_id(orden_id)
        if not existing_orden:
            return None
        
        update_data = orden_update.model_dump(exclude_unset=True)
        
        # Recalculate total if items are updated
        if "items" in update_data:
            total = self._calculate_total(update_data["items"])
            update_data["total"] = round(total, 2)
        
        query = """
        // Update orden properties
        MATCH (o:Orden {id: $orden_id})
        SET o.fecha = $fecha,
            o.canal = $canal,
            o.moneda = $moneda,
            o.descripcion = $descripcion,
            o.total = $total
        
        // Update cliente relationship if changed
        WITH o
        MATCH (new_cliente:Cliente {id: $cliente_id})
        MATCH (old_cliente)-[r:REALIZO]->(o)
        DELETE r
        CREATE (new_cliente)-[:REALIZO]->(o)
        
        // Update items - remove old and create new
        WITH o
        OPTIONAL MATCH (o)-[old_items:CONTIENE]->()
        DELETE old_items
        
        WITH o
        UNWIND $items as item
        MATCH (p:Producto {id: item.producto_id})
        CREATE (o)-[:CONTIENE {
            cantidad: item.cantidad,
            precio_unit: item.precio_unit,
            descuento_pct: item.descuento_pct
        }]->(p)
        
        RETURN o
        """
        
        params = {
            "orden_id": orden_id,
            "cliente_id": update_data["cliente_id"],
            "fecha": update_data["fecha"],
            "canal": update_data["canal"],
            "moneda": update_data["moneda"],
            "descripcion": update_data.get("descripcion"),
            "total": update_data.get("total", existing_orden["total"]),
            "items": update_data.get("items", [])
        }
        
        result = self.session.run(query, params)
        record = result.single()
        
        if record:
            return self.get_orden_by_id(orden_id)
        return None
    
    def delete_orden(self, orden_id: str) -> bool:
        """Delete an orden by ID"""
        existing_orden = self.get_orden_by_id(orden_id)
        if not existing_orden:
            return False
        
        query = """
        MATCH (o:Orden {id: $orden_id})
        DETACH DELETE o
        """
        
        result = self.session.run(query, orden_id=orden_id)
        summary = result.consume()
        return summary.counters.nodes_deleted > 0
    
    def get_ordenes_by_cliente(self, cliente_id: str, page: int = 1, limit: int = 20) -> dict:
        """Get ordenes by cliente ID"""
        skip = (page - 1) * limit
        
        count_query = """
        MATCH (c:Cliente {id: $cliente_id})-[:REALIZO]->(o:Orden)
        RETURN count(o) as total
        """
        count_result = self.session.run(count_query, cliente_id=cliente_id)
        total = count_result.single()["total"]
        
        data_query = """
        MATCH (c:Cliente {id: $cliente_id})-[:REALIZO]->(o:Orden)
        OPTIONAL MATCH (o)-[contiene:CONTIENE]->(p:Producto)
        OPTIONAL MATCH (p)-[:PERTENECE_A]->(cat:Categoria)
        RETURN o, c, 
               COLLECT({
                 producto: p,
                 categoria: cat,
                 cantidad: contiene.cantidad,
                 precio_unit: contiene.precio_unit,
                 descuento_pct: contiene.descuento_pct
               }) as items
        ORDER BY o.fecha DESC
        SKIP $skip LIMIT $limit
        """
        
        result = self.session.run(data_query, cliente_id=cliente_id, skip=skip, limit=limit)
        ordenes = [self._build_orden_response(record) for record in result]
        
        return {
            "data": ordenes,
            "total": total,
            "page": page,
            "limit": limit,
            "cliente_id": cliente_id
        }
    
    def get_ordenes_by_fecha(self, fecha_inicio: str, fecha_fin: str, page: int = 1, limit: int = 20) -> dict:
        """Get ordenes by date range"""
        skip = (page - 1) * limit
        
        count_query = """
        MATCH (o:Orden)
        WHERE o.fecha >= $fecha_inicio AND o.fecha <= $fecha_fin
        RETURN count(o) as total
        """
        count_result = self.session.run(count_query, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        total = count_result.single()["total"]
        
        data_query = """
        MATCH (c:Cliente)-[:REALIZO]->(o:Orden)
        WHERE o.fecha >= $fecha_inicio AND o.fecha <= $fecha_fin
        OPTIONAL MATCH (o)-[contiene:CONTIENE]->(p:Producto)
        OPTIONAL MATCH (p)-[:PERTENECE_A]->(cat:Categoria)
        RETURN o, c, 
               COLLECT({
                 producto: p,
                 categoria: cat,
                 cantidad: contiene.cantidad,
                 precio_unit: contiene.precio_unit,
                 descuento_pct: contiene.descuento_pct
               }) as items
        ORDER BY o.fecha DESC
        SKIP $skip LIMIT $limit
        """
        
        result = self.session.run(data_query, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, skip=skip, limit=limit)
        ordenes = [self._build_orden_response(record) for record in result]
        
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
        total_query = "MATCH (o:Orden) RETURN count(o) as total_ordenes"
        total_result = self.session.run(total_query)
        total_ordenes = total_result.single()["total_ordenes"]
        
        stats_query = """
        MATCH (o:Orden)
        RETURN 
            sum(o.total) as total_revenue,
            avg(o.total) as avg_order_value,
            min(o.total) as min_order_value,
            max(o.total) as max_order_value
        """
        
        stats_result = self.session.run(stats_query)
        stats_record = stats_result.single()
        
        if stats_record:
            return {
                "total_ordenes": total_ordenes,
                "total_revenue": stats_record["total_revenue"] or 0,
                "avg_order_value": round(stats_record["avg_order_value"] or 0, 2),
                "min_order_value": stats_record["min_order_value"] or 0,
                "max_order_value": stats_record["max_order_value"] or 0
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
        return round(total, 2)
    
    def _build_orden_response(self, record) -> dict:
        """Build complete orden response from query record"""
        if not record:
            return None
        
        orden_node = record["o"]
        cliente_node = record["c"]
        items_data = record["items"]
        
        orden_props = dict(orden_node.items())
        cliente_props = dict(cliente_node.items())
        
        # Build items with complete product and category info
        items = []
        for item_data in items_data:
            if item_data["producto"]:
                producto_props = dict(item_data["producto"].items())
                categoria_props = dict(item_data["categoria"].items()) if item_data["categoria"] else {}
                
                items.append({
                    "producto_id": producto_props.get("id"),
                    "producto_nombre": producto_props.get("nombre"),
                    "categoria_info": {
                        "id": categoria_props.get("id"),
                        "nombre": categoria_props.get("nombre")
                    } if categoria_props else None,
                    "cantidad": item_data["cantidad"],
                    "precio_unit": item_data["precio_unit"],
                    "descuento_pct": item_data["descuento_pct"],
                    "subtotal": item_data["cantidad"] * item_data["precio_unit"] * (1 - (item_data["descuento_pct"] or 0) / 100)
                })
        
        return {
            "id": orden_props.get("id"),
            "fecha": orden_props.get("fecha"),
            "canal": orden_props.get("canal"),
            "moneda": orden_props.get("moneda"),
            "descripcion": orden_props.get("descripcion"),
            "total": orden_props.get("total"),
            "cliente": {
                "id": cliente_props.get("id"),
                "nombre": cliente_props.get("nombre"),
                "email": cliente_props.get("email"),
                "genero": cliente_props.get("genero"),
                "pais": cliente_props.get("pais"),
                "creado": cliente_props.get("creado")
            },
            "items": items
        }