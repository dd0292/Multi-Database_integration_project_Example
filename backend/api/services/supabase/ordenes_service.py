from typing import Optional
from api.schemas.supabase import OrdenFormData

class OrdenService:
    def __init__(self, client):
        self.client = client

    def create_orden(self, orden_data: OrdenFormData) -> dict:
        # Extract top-level order fields and items
        raw = orden_data.model_dump()
        items = raw.pop("items", []) if isinstance(raw, dict) else []
        order_payload = {k: v for k, v in raw.items() if v is not None}

        # Insert order header
        res = self.client.table("orden").insert(order_payload).execute()
        if not (hasattr(res, "data") and res.data):
            raise RuntimeError("Failed to create order header")

        created_order = res.data[0]
        orden_id = created_order.get("orden_id")

        # Insert order detail rows if any
        detalle_rows = []
        for item in items:
            # each item expected to have producto_id, cantidad, precio_unit
            detalle_rows.append({
                "orden_id": orden_id,
                "producto_id": item.get("producto_id"),
                "cantidad": item.get("cantidad"),
                "precio_unit": item.get("precio_unit")
            })

        if detalle_rows:
            try:
                detalle_res = self.client.table("orden_detalle").insert(detalle_rows).execute()
                # attach items returned by Supabase
                if hasattr(detalle_res, "data") and detalle_res.data:
                    created_order["items"] = detalle_res.data
                else:
                    created_order["items"] = detalle_rows
            except Exception as e:
                # If inserting details failed, attempt to clean up the created order
                try:
                    self.client.table("orden").delete().eq("orden_id", orden_id).execute()
                except Exception:
                    pass
                raise
        else:
            created_order["items"] = []

        return created_order

    def get_ordenes(self, page: int = 1, limit: int = 20) -> dict:
        offset = (page - 1) * limit
        end = offset + limit - 1
        # Fetch order headers along with embedded detalle rows using PostgREST embedding
        # This will return a key like 'orden_detalle' containing an array of detail rows
        res = self.client.table("orden").select("*, orden_detalle(*)").range(offset, end).execute()
        data = res.data if hasattr(res, "data") and res.data else []

        # Normalize each order to include an 'items' key (consistent with OrdenResponse)
        normalized = []
        for o in data:
            items = o.get("orden_detalle") or []
            o["items"] = items
            # Optionally remove the embedded key to keep response tidy
            if "orden_detalle" in o:
                del o["orden_detalle"]
            normalized.append(o)

        total = len(normalized)
        return {"data": normalized, "total": total}

    def get_orden_by_id(self, orden_id: str) -> Optional[dict]:
        # Fetch order header
        res = self.client.table("orden").select("*").eq("orden_id", orden_id).execute()
        data = res.data if hasattr(res, "data") and res.data else []
        if not data:
            return None
        orden = data[0]

        # Fetch order details
        det = self.client.table("orden_detalle").select("*").eq("orden_id", orden_id).execute()
        orden["items"] = det.data if hasattr(det, "data") and det.data else []
        return orden

    def update_orden(self, orden_id: str, orden_update: OrdenFormData) -> Optional[dict]:
        update_data = orden_update.model_dump(exclude_unset=True)
        update_data = {k: v for k, v in update_data.items() if v is not None}
        res = self.client.table("orden").update(update_data).eq("orden_id", orden_id).execute()
        data = res.data if hasattr(res, "data") and res.data else []
        return data[0] if data else None

    def delete_orden(self, orden_id: str) -> bool:
        res = self.client.table("orden").delete().eq("orden_id", orden_id).execute()
        if hasattr(res, "data") and res.data:
            return True
        return False
