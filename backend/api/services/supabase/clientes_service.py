from typing import Optional
from api.schemas.supabase import ClienteFormData


class ClienteService:
    def __init__(self, client):
        """client is a supabase client instance (create_client(...))."""
        self.client = client

    def create_cliente(self, cliente_data: ClienteFormData) -> dict:
        """Create a new cliente in Supabase.
        
        Only sends fields that exist in the cliente table.
        Supabase will auto-generate cliente_id and fecha_registro.
        """
        data = cliente_data.model_dump()
        # Remove any None values to let Supabase use defaults
        data = {k: v for k, v in data.items() if v is not None}
        
        res = self.client.table("cliente").insert(data).execute()
        if hasattr(res, "data") and res.data:
            return res.data[0]
        return {**data}

    def get_clientes(self, page: int = 1, limit: int = 20) -> dict:
        """Fetch paginated list of clientes."""
        offset = (page - 1) * limit
        end = offset + limit - 1
        res = self.client.table("cliente").select("*").range(offset, end).execute()
        data = res.data if hasattr(res, "data") and res.data else []
        total = len(data)
        return {"data": data, "total": total}

    def get_cliente_by_id(self, cliente_id: str) -> Optional[dict]:
        """Fetch a single cliente by cliente_id (UUID)."""
        res = self.client.table("cliente").select("*").eq("cliente_id", cliente_id).execute()
        data = res.data if hasattr(res, "data") and res.data else []
        return data[0] if data else None

    def update_cliente(self, cliente_id: str, cliente_update: ClienteFormData) -> Optional[dict]:
        """Update a cliente by cliente_id."""
        update_data = cliente_update.model_dump(exclude_unset=True)
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        res = self.client.table("cliente").update(update_data).eq("cliente_id", cliente_id).execute()
        data = res.data if hasattr(res, "data") and res.data else []
        return data[0] if data else None

    def delete_cliente(self, cliente_id: str) -> bool:
        """Delete a cliente by cliente_id."""
        res = self.client.table("cliente").delete().eq("cliente_id", cliente_id).execute()
        if hasattr(res, "data") and res.data:
            return True
        return False
