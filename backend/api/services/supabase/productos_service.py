from typing import Optional
from api.schemas.supabase import ProductoFormData

class ProductoService:
    def __init__(self, client):
        self.client = client

    def create_producto(self, producto_data: ProductoFormData) -> dict:
        data = producto_data.model_dump()
        data = {k: v for k, v in data.items() if v is not None}
        res = self.client.table("producto").insert(data).execute()
        if hasattr(res, "data") and res.data:
            return res.data[0]
        return {**data}

    def get_productos(self, page: int = 1, limit: int = 20) -> dict:
        offset = (page - 1) * limit
        end = offset + limit - 1
        res = self.client.table("producto").select("*").range(offset, end).execute()
        data = res.data if hasattr(res, "data") and res.data else []
        total = len(data)
        return {"data": data, "total": total}

    def get_producto_by_id(self, producto_id: str) -> Optional[dict]:
        res = self.client.table("producto").select("*").eq("producto_id", producto_id).execute()
        data = res.data if hasattr(res, "data") and res.data else []
        return data[0] if data else None

    def update_producto(self, producto_id: str, producto_update: ProductoFormData) -> Optional[dict]:
        update_data = producto_update.model_dump(exclude_unset=True)
        update_data = {k: v for k, v in update_data.items() if v is not None}
        res = self.client.table("producto").update(update_data).eq("producto_id", producto_id).execute()
        data = res.data if hasattr(res, "data") and res.data else []
        return data[0] if data else None

    def delete_producto(self, producto_id: str) -> bool:
        res = self.client.table("producto").delete().eq("producto_id", producto_id).execute()
        if hasattr(res, "data") and res.data:
            return True
        return False
