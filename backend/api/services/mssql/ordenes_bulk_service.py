from typing import List, Dict, Any, Tuple
from sqlalchemy import text
from sqlalchemy.engine import Connection
from datetime import datetime

class OrdenBulkService:
    def __init__(self, conn: Connection):
        self.conn = conn

    def _cliente_exists(self, cliente_id: int) -> bool:
        q = text("SELECT 1 FROM Ventas_Transactional.dbo.Cliente WHERE ClienteId = :id AND Activo = 1;")
        res = self.conn.execute(q, {"id": cliente_id})
        return res.scalar_one_or_none() is not None

    def _get_cliente_id_by_email(self, email: str) -> int | None:
        """Resolve cliente_id from email address"""
        q = text("SELECT ClienteId FROM Ventas_Transactional.dbo.Cliente WHERE Email = :email AND Activo = 1;")
        res = self.conn.execute(q, {"email": email})
        row = res.scalar_one_or_none()
        return row if row else None

    def _producto_exists(self, producto_id: int) -> bool:
        q = text("SELECT 1 FROM Ventas_Transactional.dbo.Producto WHERE ProductoId = :id AND Activo = 1;")
        res = self.conn.execute(q, {"id": producto_id})
        return res.scalar_one_or_none() is not None

    def bulk_upload_ordenes(self, ordenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk upload multiple orders with their items (OrdenDetalle).
        Expected format for each order:
        {
          "cliente_id": 1,  // OR "email": "cliente@example.com"
          "fecha": "2025-01-15",
          "canal": "WEB",
          "moneda": "USD",
          "items": [
            { "producto_id": 1, "cantidad": 2, "precio_unit": 50.00, "descuento_pct": 0 },
            ...
          ]
        }
        """
        if not isinstance(ordenes, list):
            raise ValueError("ordenes must be a list")

        results = {
            "total": len(ordenes),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        insert_orden_q = text("""
        INSERT INTO Ventas_Transactional.dbo.Orden (ClienteId, Fecha, Canal, Moneda, Total)
        OUTPUT INSERTED.OrdenId
        VALUES (:cliente_id, :fecha, :canal, :moneda, :total);
        """)

        insert_detalle_q = text("""
        INSERT INTO Ventas_Transactional.dbo.OrdenDetalle
            (OrdenId, ProductoId, Cantidad, PrecioUnit, DescuentoPct)
        VALUES (:orden_id, :producto_id, :cantidad, :precio_unit, :descuento_pct);
        """)

        for idx, orden_data in enumerate(ordenes):
            try:
                # Resolve cliente_id: prefer cliente_id, fallback to email
                cliente_id = None
                if "cliente_id" in orden_data:
                    cliente_id = int(orden_data.get("cliente_id"))
                elif "email" in orden_data:
                    email = orden_data.get("email")
                    cliente_id = self._get_cliente_id_by_email(email)
                    if cliente_id is None:
                        raise ValueError(f"Cliente with email '{email}' not found")
                else:
                    raise ValueError("Must provide either cliente_id or email")

                if not self._cliente_exists(cliente_id):
                    raise ValueError(f"Cliente {cliente_id} not found")

                items = orden_data.get("items") or []
                if not items:
                    raise ValueError("Order must have at least one item")

                # Validate productos and compute total
                total = 0.0
                item_details = []
                for item in items:
                    producto_id = int(item.get("producto_id"))
                    if not self._producto_exists(producto_id):
                        raise ValueError(f"Producto {producto_id} not found")

                    cantidad = int(item.get("cantidad", 0))
                    if cantidad <= 0:
                        raise ValueError("cantidad must be > 0")

                    precio = float(item.get("precio_unit", 0.0))
                    descuento = float(item.get("descuento_pct", 0.0))

                    subtotal = cantidad * precio * (1 - descuento / 100.0)
                    total += subtotal
                    item_details.append({
                        "producto_id": producto_id,
                        "cantidad": cantidad,
                        "precio_unit": precio,
                        "descuento_pct": descuento
                    })

                # Insert Orden
                fecha = orden_data.get("fecha") or datetime.utcnow().isoformat()
                orden_params = {
                    "cliente_id": cliente_id,
                    "fecha": fecha,
                    "canal": orden_data.get("canal"),
                    "moneda": orden_data.get("moneda"),
                    "total": round(total, 2)
                }

                res = self.conn.execute(insert_orden_q, orden_params)
                inserted = res.mappings().first()
                try:
                    res.close()
                except Exception:
                    pass

                if not inserted:
                    raise RuntimeError("Insert did not return an orden id")

                orden_id = inserted["OrdenId"]

                # Insert OrdenDetalle rows
                for detail in item_details:
                    self.conn.execute(insert_detalle_q, {
                        "orden_id": orden_id,
                        "producto_id": detail["producto_id"],
                        "cantidad": detail["cantidad"],
                        "precio_unit": detail["precio_unit"],
                        "descuento_pct": detail["descuento_pct"]
                    })

                results["success"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "row": idx + 1,
                    "error": str(e)
                })

        return results