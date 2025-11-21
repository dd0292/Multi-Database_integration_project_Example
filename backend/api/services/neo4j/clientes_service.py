from datetime import datetime
from typing import Optional, List, Dict, Any
from api.schemas.froms import ClienteFormData

class ClienteNeo4jService:
    def __init__(self, session):
        self.session = session
    
    def create_cliente(self, cliente_data: ClienteFormData) -> Optional[dict]:
        cliente_dict = cliente_data.model_dump()
        cliente_dict["creado"] = datetime.now().isoformat()
        
        query = """
        CREATE (c:Cliente {
            id: randomUUID(),
            nombre: $nombre,
            email: $email,
            genero: $genero,
            pais: $pais,
            creado: $creado
        })
        RETURN c
        """
        
        result = self.session.run(query, cliente_dict)
        record = result.single()
        
        if record:
            cliente_node = record["c"]
            return self._cliente_helper(cliente_node)
        return None
    
    def get_clientes(self, page: int = 1, limit: int = 20) -> dict:
        skip = (page - 1) * limit
        
        # Count query
        count_query = "MATCH (c:Cliente) RETURN count(c) as total"
        count_result = self.session.run(count_query)
        total = count_result.single()["total"]
        
        # Data query
        data_query = """
        MATCH (c:Cliente)
        RETURN c
        ORDER BY c.creado DESC
        SKIP $skip LIMIT $limit
        """
        
        result = self.session.run(data_query, skip=skip, limit=limit)
        clientes = [self._cliente_helper(record["c"]) for record in result]
        
        return {"data": clientes, "total": total}
    
    def get_cliente_by_id(self, cliente_id: str) -> Optional[dict]:
        query = """
        MATCH (c:Cliente {id: $cliente_id})
        RETURN c
        """
        
        result = self.session.run(query, cliente_id=cliente_id)
        record = result.single()
        
        return self._cliente_helper(record["c"]) if record else None
    
    def update_cliente(self, cliente_id: str, cliente_update: ClienteFormData) -> Optional[dict]:
        # First check if cliente exists
        existing_cliente = self.get_cliente_by_id(cliente_id)
        if not existing_cliente:
            return None
        
        update_data = cliente_update.model_dump(exclude_unset=True)
        update_data["actualizado"] = datetime.now().isoformat()
        
        query = """
        MATCH (c:Cliente {id: $cliente_id})
        SET c.nombre = $nombre,
            c.email = $email,
            c.genero = $genero,
            c.pais = $pais,
            c.actualuizado = $actualizado
        RETURN c
        """
        
        result = self.session.run(query, 
                                cliente_id=cliente_id,
                                nombre=update_data["nombre"],
                                email=update_data["email"],
                                genero=update_data["genero"],
                                pais=update_data["pais"],
                                actualizado=update_data["actualizado"]
                                )
        
        record = result.single()
        return self._cliente_helper(record["c"]) if record else None
    
    def delete_cliente(self, cliente_id: str) -> bool:
        # First check if cliente exists
        existing_cliente = self.get_cliente_by_id(cliente_id)
        if not existing_cliente:
            return False
        
        query = """
        MATCH (c:Cliente {id: $cliente_id})
        DELETE c
        """
        
        result = self.session.run(query, cliente_id=cliente_id)
        # For DELETE operations, we can check the summary
        summary = result.consume()
        return summary.counters.nodes_deleted > 0
    
    def _cliente_helper(self, cliente_node) -> dict:
        if not cliente_node:
            return None
            
        # Extract properties from the Neo4j node
        properties = dict(cliente_node.items())
        
        return {
            "id": properties.get("id"),
            "nombre": properties.get("nombre"),
            "email": properties.get("email"),
            "genero": properties.get("genero"),
            "pais": properties.get("pais"),
            "creado": properties.get("creado"),
        }