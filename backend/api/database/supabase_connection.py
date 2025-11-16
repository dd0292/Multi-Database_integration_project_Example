from supabase import create_client
from api.config import settings


class SupabaseConnection:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise RuntimeError("Supabase configuration missing. Set SUPABASE_URL and SUPABASE_KEY in env.")
            cls._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return cls._client


def get_supabase_client():
    """Return a Supabase client instance (singleton).

    Use the returned object like: client.table('cliente').select('*').execute()
    """
    return SupabaseConnection.get_client()


def get_cliente_table(client=None):
    """Get the 'cliente' table reference."""
    client = client or get_supabase_client()
    return client.table("cliente")


def get_producto_table(client=None):
    """Get the 'producto' table reference."""
    client = client or get_supabase_client()
    return client.table("producto")


def get_orden_table(client=None):
    """Get the 'orden' table reference."""
    client = client or get_supabase_client()
    return client.table("orden")
