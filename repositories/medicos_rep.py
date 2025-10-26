from typing import List, Optional, Dict, Any
from supabase import Client
from repositories.supabase_client import obtener_cliente_supabase
import logging

logger = logging.getLogger(__name__)

class RepositorioMedicos:
    def __init__(self, cliente: Client = None):
        self.cliente = cliente or obtener_cliente_supabase()
        self.tabla = "profesionales"
    
    def obtener_profesional(self, profesional_id: int) -> Optional[Dict[str, Any]]:
        try:
            respuesta = self.cliente.table(self.tabla).select("*").eq("id", profesional_id).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error obteniendo medico {profesional_id}: {e}")
            return None
        
    def obtener_profesionales_activos(self) -> List[Dict[str, Any]]:
        try:
            respuesta = self.cliente.table(self.tabla).select("*").eq("activo", True).execute()
            return respuesta.data
        except Exception as e:
            logger.error(f"Error obteniendo medicos activos: {e}")
            return []