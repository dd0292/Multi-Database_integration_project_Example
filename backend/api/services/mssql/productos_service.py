from typing import Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.engine import Connection
from api.schemas.froms import ProductoFormData

class ProductoService:
    def __init__(self, conn: Connection):
        self.conn = conn

    def create_producto(self, producto_data: ProductoFormData) -> Dict[str, Any]:
        check_q = text("SELECT ProductoId, Activo FROM Ventas_Transactional.dbo.Producto WHERE SKU = :sku;")
        existing = self.conn.execute(check_q, {"sku": producto_data.sku}).mappings().first()
        if existing:
            if existing["Activo"]:
                return self.get_producto_by_id(existing["ProductoId"])
            with self.conn.begin():
                upd = text("""
                    UPDATE Ventas_Transactional.dbo.Producto
                    SET Activo = 1, Nombre = :nombre, Categoria = :categoria
                    WHERE ProductoId = :id;
                """)
                self.conn.execute(upd, {
                    "nombre": producto_data.nombre,
                    "categoria": producto_data.categoria,
                    "id": existing["ProductoId"]
                })
            return self.get_producto_by_id(existing["ProductoId"])

        q = text("""
        INSERT INTO Ventas_Transactional.dbo.Producto (SKU, Nombre, Categoria)
        OUTPUT INSERTED.ProductoId
        VALUES (:sku, :nombre, :categoria);
        """)
        params = {
            "sku": producto_data.sku,
            "nombre": producto_data.nombre,
            "categoria": producto_data.categoria
        }
        with self.conn.begin():
            res = self.conn.execute(q, params)
            inserted = res.mappings().first()
            try:
                res.close()
            except Exception:
                pass

        if not inserted:
            raise RuntimeError("Insert did not return an inserted id")

        producto_id = inserted["ProductoId"]
        return self.get_producto_by_id(producto_id)

    def get_productos(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        offset = (page - 1) * limit
        q = text("""
        SELECT ProductoId, SKU, Nombre, Categoria
        FROM Ventas_Transactional.dbo.Producto
        WHERE Activo = 1
        ORDER BY ProductoId
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
        """)
        total_q = text("SELECT COUNT(1) AS total FROM Ventas_Transactional.dbo.Producto WHERE Activo = 1;")
        res = self.conn.execute(q, {"offset": offset, "limit": limit})
        rows = [dict(r) for r in res.mappings().all()]
        total = self.conn.execute(total_q).scalar_one()
        return {"data": rows, "total": total}

    def get_producto_by_id(self, producto_id: int) -> Optional[Dict[str, Any]]:
        q = text("""
        SELECT ProductoId, SKU, Nombre, Categoria
        FROM Ventas_Transactional.dbo.Producto
        WHERE ProductoId = :id AND Activo = 1;
        """)
        res = self.conn.execute(q, {"id": producto_id})
        row = res.mappings().first()
        return dict(row) if row else None

    def update_producto(self, producto_id: int, producto_update) -> Optional[Dict[str, Any]]:
        update_data = producto_update.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_producto_by_id(producto_id)
        set_parts = []
        params = {"id": producto_id}
        for i, (k, v) in enumerate(update_data.items()):
            set_parts.append(f"{k} = :p{i}")
            params[f"p{i}"] = v
        set_clause = ", ".join(set_parts)
        q = text(f"UPDATE Ventas_Transactional.dbo.Producto SET {set_clause} WHERE ProductoId = :id;")
        with self.conn.begin():
            self.conn.execute(q, params)
        return self.get_producto_by_id(producto_id)

    def delete_producto(self, producto_id: int) -> bool:
        q = text("UPDATE Ventas_Transactional.dbo.Producto SET Activo = 0 WHERE ProductoId = :id;")
        with self.conn.begin():
            res = self.conn.execute(q, {"id": producto_id})
        return res.rowcount > 0