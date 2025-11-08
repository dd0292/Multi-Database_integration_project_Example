from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Connection
from api.schemas.froms import ClienteFormData

class ClienteService:
    def __init__(self, conn: Connection):
        self.conn = conn

    def create_cliente(self, cliente_data: ClienteFormData) -> Dict[str, Any]:
        q = text("""
        INSERT INTO Ventas_Transactional.dbo.Cliente (Nombre, Email, Genero, Pais)
        OUTPUT INSERTED.ClienteId
        VALUES (:nombre, :email, :genero, :pais);
        """)
        params = {
            "nombre": cliente_data.nombre,
            "email": cliente_data.email,
            "genero": cliente_data.genero,
            "pais": cliente_data.pais
        }
        res = self.conn.execute(q, params)
        inserted = res.mappings().first()
        cliente_id = inserted["ClienteId"]
        row = self.get_cliente_by_id(cliente_id)
        return row

    def get_clientes(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        offset = (page - 1) * limit
        q = text("""
        SELECT ClienteId, Nombre, Email, Genero, Pais, FechaRegistro
        FROM Ventas_Transactional.dbo.Cliente
        ORDER BY ClienteId
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
        """)
        total_q = text("SELECT COUNT(1) AS total FROM Ventas_Transactional.dbo.Cliente;")
        res = self.conn.execute(q, {"offset": offset, "limit": limit})
        rows = [dict(r) for r in res.mappings().all()]
        total = self.conn.execute(total_q).scalar_one()
        return {"data": rows, "total": total}

    def get_cliente_by_id(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        q = text("""
        SELECT ClienteId, Nombre, Email, Genero, Pais, FechaRegistro
        FROM Ventas_Transactional.dbo.Cliente
        WHERE ClienteId = :id;
        """)
        res = self.conn.execute(q, {"id": cliente_id})
        row = res.mappings().first()
        return dict(row) if row else None

    def update_cliente(self, cliente_id: int, cliente_update: ClienteFormData) -> Optional[Dict[str, Any]]:
        # build dynamic SET from provided fields
        update_data = cliente_update.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_cliente_by_id(cliente_id)
        set_parts = []
        params = {"id": cliente_id}
        for i, (k, v) in enumerate(update_data.items()):
            set_parts.append(f"{k} = :p{i}")
            params[f"p{i}"] = v
        set_clause = ", ".join(set_parts)
        q = text(f"UPDATE Ventas_Transactional.dbo.Cliente SET {set_clause} WHERE ClienteId = :id;")
        res = self.conn.execute(q, params)
        # check existence
        return self.get_cliente_by_id(cliente_id)

    def delete_cliente(self, cliente_id: int) -> bool:
        q = text("DELETE FROM Ventas_Transactional.dbo.Cliente WHERE ClienteId = :id;")
        res = self.conn.execute(q, {"id": cliente_id})
        return res.rowcount > 0