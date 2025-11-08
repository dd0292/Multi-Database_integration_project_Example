from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Connection
from api.schemas.froms import OrdenFormData

class OrdenService:
    def __init__(self, conn: Connection):
        self.conn = conn

    def create_orden(self, orden_data: OrdenFormData) -> Dict[str, Any]:
        q = text("""
        INSERT INTO Ventas_Transactional.dbo.Orden (ClienteId, Fecha, Canal, Moneda, Total)
        OUTPUT INSERTED.OrdenId
        VALUES (:cliente_id, :fecha, :canal, :moneda, :total);
        """)
        params = {
            "cliente_id": orden_data.cliente_id,
            "fecha": orden_data.fecha,
            "canal": orden_data.canal,
            "moneda": orden_data.moneda,
            "total": orden_data.total
        }
        res = self.conn.execute(q, params)
        inserted = res.mappings().first()
        orden_id = inserted["OrdenId"]
        return self.get_orden_by_id(orden_id)

    def get_ordenes(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        offset = (page - 1) * limit
        q = text("""
        SELECT OrdenId, ClienteId, Fecha, Canal, Moneda, Total
        FROM Ventas_Transactional.dbo.Orden
        ORDER BY OrdenId
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
        """)
        total_q = text("SELECT COUNT(1) AS total FROM Ventas_Transactional.dbo.Orden;")
        res = self.conn.execute(q, {"offset": offset, "limit": limit})
        rows = [dict(r) for r in res.mappings().all()]
        total = self.conn.execute(total_q).scalar_one()
        return {"data": rows, "total": total}

    def get_orden_by_id(self, orden_id: int) -> Optional[Dict[str, Any]]:
        q = text("""
        SELECT OrdenId, ClienteId, Fecha, Canal, Moneda, Total
        FROM Ventas_Transactional.dbo.Orden
        WHERE OrdenId = :id;
        """)
        res = self.conn.execute(q, {"id": orden_id})
        row = res.mappings().first()
        return dict(row) if row else None

    def update_orden(self, orden_id: int, orden_update: OrdenFormData) -> Optional[Dict[str, Any]]:
        update_data = orden_update.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_orden_by_id(orden_id)
        set_parts = []
        params = {"id": orden_id}
        for i, (k, v) in enumerate(update_data.items()):
            set_parts.append(f"{k} = :p{i}")
            params[f"p{i}"] = v
        set_clause = ", ".join(set_parts)
        q = text(f"UPDATE Ventas_Transactional.dbo.Orden SET {set_clause} WHERE OrdenId = :id;")
        self.conn.execute(q, params)
        return self.get_orden_by_id(orden_id)

    def delete_orden(self, orden_id: int) -> bool:
        q = text("DELETE FROM Ventas_Transactional.dbo.Orden WHERE OrdenId = :id;")
        res = self.conn.execute(q, {"id": orden_id})
        return res.rowcount > 0