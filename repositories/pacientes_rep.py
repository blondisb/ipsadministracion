from typing import List, Optional, Dict, Any
from supabase import Client
from repositories.supabase_client import obtener_cliente_supabase
from schemas.paciente_sch import PacienteCrear, PacienteActualizar
import logging

logger = logging.getLogger(__name__)

class RepositorioPacientes:
    def __init__(self, cliente: Client = None):
        self.cliente = cliente or obtener_cliente_supabase()
        self.tabla = "pacientes"
    
    def obtener_paciente(self, id_paciente: int) -> Optional[Dict[str, Any]]:
        try:
            respuesta = self.cliente.table(self.tabla).select("*").eq("id", id_paciente).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error obteniendo paciente {id_paciente}: {e}")
            return None
    
    def obtener_paciente_por_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            respuesta = self.cliente.table(self.tabla).select("*").eq("email", email).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error obteniendo paciente por email {email}: {e}")
            return None
    
    def obtener_pacientes(self, saltar: int = 0, limite: int = 100) -> List[Dict[str, Any]]:
        try:
            respuesta = self.cliente.table(self.tabla).select("*").range(saltar, saltar + limite - 1).execute()
            return respuesta.data
        except Exception as e:
            logger.error(f"Error obteniendo pacientes: {e}")
            return []
    
    def crear_paciente(self, paciente: PacienteCrear) -> Optional[Dict[str, Any]]:
        try:
            paciente.fecha_nacimiento = paciente.fecha_nacimiento.isoformat()
            datos_paciente = paciente.dict()
            respuesta = self.cliente.table(self.tabla).insert(datos_paciente).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error creando paciente: {e}")
            return None
    
    def actualizar_paciente(self, id_paciente: int, paciente_actualizar: PacienteActualizar) -> Optional[Dict[str, Any]]:
        try:
            datos_actualizar = paciente_actualizar.dict(exclude_unset=True)
            respuesta = self.cliente.table(self.tabla).update(datos_actualizar).eq("id", id_paciente).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error actualizando paciente {id_paciente}: {e}")
            return None
    
    def eliminar_paciente(self, id_paciente: int) -> bool:
        try:
            respuesta = self.cliente.table(self.tabla).delete().eq("id", id_paciente).execute()
            return len(respuesta.data) > 0
        except Exception as e:
            logger.error(f"Error eliminando paciente {id_paciente}: {e}")
            return False