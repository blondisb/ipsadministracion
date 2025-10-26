from supabase import create_client, Client
from config import settings
import logging

logger = logging.getLogger(__name__)

class ClienteSupabase:
    _instancia: Client = None
    
    @classmethod
    def obtener_cliente(cls) -> Client:
        if cls._instancia is None:
            try:
                cls._instancia = create_client(settings.SUPABASE_URL, settings.SUPABASE_API_KEY)
                logger.info("Cliente de Supabase inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando cliente de Supabase: {e}")
                raise
        return cls._instancia

def obtener_cliente_supabase():
    return ClienteSupabase.obtener_cliente()