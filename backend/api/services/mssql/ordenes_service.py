from typing import Optional, Dict, Any, List
from sqlalchemy import text
from sqlalchemy.engine import Connection
from datetime import datetime

from api.schemas.mssql import OrdenFormData

class OrdenService:
    def __init__(self, conn: Connection):
        self.conn = conn

    def _cliente_exists(self, cliente_id: int) -> bool:
        q = text("SELECT 1 FROM Ventas_Transactional.dbo.Cliente WHERE ClienteId = :id AND Activo = 1;")
        res = self.conn.execute(q, {"id": cliente_id})
        return res.scalar_one_or_none() is not None

    def _producto_exists(self, producto_id: int) -> bool:
        q = text("SELECT 1 FROM Ventas_Transactional.dbo.Producto WHERE ProductoId = :id AND Activo = 1;")
        res = self.conn.execute(q, {"id": producto_id})
        return res.scalar_one_or_none() is not None

    def _normalize_payload(self, payload: Any) -> Dict[str, Any]:
        """
        Accept dict or Pydantic model and return normalized dict with:
        cliente_id (int), fecha (string), canal, moneda, items (list of dicts)
        """
        if hasattr(payload, "model_dump"):
            data = payload.model_dump()
        elif isinstance(payload, dict):
            data = dict(payload)
        else:
            data = dict(payload.__dict__)

        items = data.get("items") or []
        if not isinstance(items, list) or len(items) == 0:
            raise ValueError("items required and must be a non-empty list")

        try:
            cliente_id = int(data.get("cliente_id"))
        except Exception:
            raise ValueError("cliente_id must be convertible to int")

        for it in items:
            if "producto_id" not in it:
                raise ValueError("each item must contain producto_id")
            try:
                it["producto_id"] = int(it["producto_id"])
            except Exception:
                raise ValueError("producto_id must be convertible to int")
            it["cantidad"] = int(it.get("cantidad", 0))
            it["precio_unit"] = float(it.get("precio_unit", 0.0))
            it["descuento_pct"] = float(it.get("descuento_pct", 0.0)) if it.get("descuento_pct") is not None else 0.0

        return {
            "cliente_id": cliente_id,
            "fecha": data.get("fecha") or datetime.utcnow().isoformat(),
            "canal": data.get("canal"),
            "moneda": data.get("moneda"),
            "items": items
        }

    def create_orden(self, orden_data: Any) -> Dict[str, Any]:
        # normalize & validate payload
        norm = self._normalize_payload(orden_data)

        # validate cliente exists
        if not self._cliente_exists(norm["cliente_id"]):
            raise ValueError(f"Cliente with id {norm['cliente_id']} not found")

        items = norm["items"]

        # validate productos exist and prepare details
        details_params: List[Dict[str, Any]] = []
        total = 0.0
        for it in items:
            producto_id = int(it["producto_id"])
            if not self._producto_exists(producto_id):
                raise ValueError(f"Producto with id {producto_id} not found")
            cantidad = int(it["cantidad"])
            precio = float(it["precio_unit"])
            descuento = float(it.get("descuento_pct") or 0.0)
            subtotal = cantidad * precio * (1 - descuento / 100.0)
            total += subtotal
            details_params.append({
                "producto_id": producto_id,
                "cantidad": cantidad,
                "precio_unit": precio,
                "descuento_pct": descuento
            })

        # insert Orden and get id
        q = text("""
        INSERT INTO Ventas_Transactional.dbo.Orden (ClienteId, Fecha, Canal, Moneda, Total)
        OUTPUT INSERTED.OrdenId
        VALUES (:cliente_id, :fecha, :canal, :moneda, :total);
        """)
        params = {
            "cliente_id": norm["cliente_id"],
            "fecha": norm["fecha"],
            "canal": norm["canal"],
            "moneda": norm["moneda"],
            "total": round(total, 2)
        }
        res = self.conn.execute(q, params)
        inserted = res.mappings().first()
        try:
            res.close()
        except Exception:
            pass

        if not inserted:
            raise RuntimeError("Insert did not return an inserted id")

        orden_id = inserted["OrdenId"]

        # insert OrdenDetalle rows
        det_q = text("""
        INSERT INTO Ventas_Transactional.dbo.OrdenDetalle
            (OrdenId, ProductoId, Cantidad, PrecioUnit, DescuentoPct)
        VALUES (:orden_id, :producto_id, :cantidad, :precio_unit, :descuento_pct);
        """)
        for d in details_params:
            self.conn.execute(det_q, {
                "orden_id": orden_id,
                "producto_id": d["producto_id"],
                "cantidad": d["cantidad"],
                "precio_unit": d["precio_unit"],
                "descuento_pct": d["descuento_pct"]
            })

        return self.get_orden_by_id(orden_id)

    def get_ordenes(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        offset = (page - 1) * limit
        q = text("""
        SELECT OrdenId, ClienteId, Fecha, Canal, Moneda, Total
        FROM Ventas_Transactional.dbo.Orden
        WHERE Activo = 1
        ORDER BY OrdenId
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
        """)
        total_q = text("SELECT COUNT(1) AS total FROM Ventas_Transactional.dbo.Orden WHERE Activo = 1;")
        res = self.conn.execute(q, {"offset": offset, "limit": limit})
        rows = [dict(r) for r in res.mappings().all()]
        total = self.conn.execute(total_q).scalar_one()
        return {"data": rows, "total": total}

    def get_orden_by_id(self, orden_id: int) -> Optional[Dict[str, Any]]:
        q = text("""
        SELECT OrdenId, ClienteId, Fecha, Canal, Moneda, Total
        FROM Ventas_Transactional.dbo.Orden
        WHERE OrdenId = :id AND Activo = 1;
        """)
        res = self.conn.execute(q, {"id": orden_id})
        row = res.mappings().first()
        if not row:
            return None
        order = dict(row)

        det_q = text("""
        SELECT OrdenDetalleId, ProductoId, Cantidad, PrecioUnit, DescuentoPct,
               (Cantidad * PrecioUnit * (1 - ISNULL(DescuentoPct,0)/100.0)) AS Subtotal
        FROM Ventas_Transactional.dbo.OrdenDetalle
        WHERE OrdenId = :id AND Activo = 1;
        """)
        det_res = self.conn.execute(det_q, {"id": orden_id})
        items = [dict(r) for r in det_res.mappings().all()]
        order["items"] = items
        return order

    def update_orden(self, orden_id: int, orden_update: Any) -> Optional[Dict[str, Any]]:
        """
        Update main order fields and optionally replace items.
        If 'items' present in payload, existing detalle rows are soft-deleted and new inserted;
        total recomputed.
        """
        if hasattr(orden_update, "model_dump"):
            data = orden_update.model_dump(exclude_unset=True)
        elif isinstance(orden_update, dict):
            data = dict(orden_update)
        else:
            data = dict(orden_update.__dict__)

        allowed_main = ("fecha", "canal", "moneda")
        set_parts = []
        params = {"id": orden_id}
        for i, k in enumerate(allowed_main):
            if k in data:
                set_parts.append(f"{k} = :p{i}")
                params[f"p{i}"] = data[k]
        if set_parts:
            q = text(f"UPDATE Ventas_Transactional.dbo.Orden SET {', '.join(set_parts)} WHERE OrdenId = :id;")
            self.conn.execute(q, params)

        if "items" in data:
            items = data["items"]
            if not isinstance(items, list) or len(items) == 0:
                raise ValueError("items must be a non-empty list")
            del_q = text("UPDATE Ventas_Transactional.dbo.OrdenDetalle SET Activo = 0 WHERE OrdenId = :id;")
            self.conn.execute(del_q, {"id": orden_id})

            total = 0.0
            det_q = text("""
            INSERT INTO Ventas_Transactional.dbo.OrdenDetalle
                (OrdenId, ProductoId, Cantidad, PrecioUnit, DescuentoPct)
            VALUES (:orden_id, :producto_id, :cantidad, :precio_unit, :descuento_pct);
            """)
            for it in items:
                producto_id = int(it["producto_id"])
                cantidad = int(it["cantidad"])
                precio = float(it["precio_unit"])
                descuento = float(it.get("descuento_pct") or 0.0)
                subtotal = cantidad * precio * (1 - descuento / 100.0)
                total += subtotal
                self.conn.execute(det_q, {
                    "orden_id": orden_id,
                    "producto_id": producto_id,
                    "cantidad": cantidad,
                    "precio_unit": precio,
                    "descuento_pct": descuento
                })
            upd_q = text("UPDATE Ventas_Transactional.dbo.Orden SET Total = :total WHERE OrdenId = :id;")
            self.conn.execute(upd_q, {"total": round(total, 2), "id": orden_id})

        return self.get_orden_by_id(orden_id)

    def delete_orden(self, orden_id: int) -> bool:
        q = text("UPDATE Ventas_Transactional.dbo.Orden SET Activo = 0 WHERE OrdenId = :id;")
        res = self.conn.execute(q, {"id": orden_id})
        # soft-delete details too
        try:
            self.conn.execute(text("UPDATE Ventas_Transactional.dbo.OrdenDetalle SET Activo = 0 WHERE OrdenId = :id;"), {"id": orden_id})
        except Exception:
            pass
        return res.rowcount > 0