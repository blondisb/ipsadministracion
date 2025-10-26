from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from supabase import Client
from repositories.supabase_client import obtener_cliente_supabase
from schemas.cita_sch import CitaCrear, CitaActualizar
import logging

logger = logging.getLogger(__name__)

class RepositorioCitas:
    def __init__(self, cliente: Client = None):
        self.cliente = cliente or obtener_cliente_supabase()
        self.tabla = "citas"
    
    def obtener_cita(self, id_cita: int) -> Optional[Dict[str, Any]]:
        try:
            respuesta = (self.cliente.table(self.tabla)
                       .select("*, pacientes(*)")
                       .eq("id", id_cita)
                       .execute())
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error obteniendo cita {id_cita}: {e}")
            return None
    
    def obtener_citas_por_paciente(self, id_paciente: int, saltar: int = 0, limite: int = 100) -> List[Dict[str, Any]]:
        try:
            respuesta = (self.cliente.table(self.tabla)
                       .select("*, pacientes(*)")
                       .eq("paciente_id", id_paciente)
                       .range(saltar, saltar + limite - 1)
                       .execute())
            return respuesta.data
        except Exception as e:
            logger.error(f"Error obteniendo citas para paciente {id_paciente}: {e}")
            return []
    
    def obtener_citas_por_profesional(self, id_profesional: int, fecha_inicio: datetime, fecha_fin: datetime) -> List[Dict[str, Any]]:
        try:
            respuesta = (self.cliente.table(self.tabla)
                       .select("*")
                       .eq("profesional_id", id_profesional)
                       .gte("fecha_cita", fecha_inicio.isoformat())
                       .lte("fecha_cita", fecha_fin.isoformat())
                       .execute())
            return respuesta.data
        except Exception as e:
            logger.error(f"Error obteniendo citas para profesional {id_profesional}: {e}")
            return []
    
    def obtener_todas_citas(self, saltar: int = 0, limite: int = 100) -> List[Dict[str, Any]]:
        try:
            respuesta = (self.cliente.table(self.tabla)
                       .select("*, pacientes(*)")
                       .range(saltar, saltar + limite - 1)
                       .execute())
            return respuesta.data
        except Exception as e:
            logger.error(f"Error obteniendo todas las citas: {e}")
            return []
    
    def crear_cita(self, cita: CitaCrear) -> Optional[Dict[str, Any]]:
        try:
            datos_cita = cita.dict()
            respuesta = self.cliente.table(self.tabla).insert(datos_cita).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error creando cita: {e}")
            return None
    
    def actualizar_cita(self, id_cita: int, cita_actualizar: CitaActualizar) -> Optional[Dict[str, Any]]:
        try:
            datos_actualizar = cita_actualizar.dict(exclude_unset=True)
            respuesta = self.cliente.table(self.tabla).update(datos_actualizar).eq("id", id_cita).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error actualizando cita {id_cita}: {e}")
            return None
    
    def verificar_disponibilidad(self, id_profesional: int, fecha_cita: datetime, duracion_minutos: int = 30) -> bool:
        try:
            hora_fin = fecha_cita + timedelta(minutes=duracion_minutos)
            
            # Buscar citas que se superpongan con el horario solicitado
            respuesta = (self.cliente.table(self.tabla)
                       .select("*")
                       .eq("profesional_id", id_profesional)
                       .eq("estado", "programada")
                       .lt("fecha_cita", hora_fin.isoformat())
                       .execute())
            
            # Verificar superposición para cada cita existente
            for cita in respuesta.data:
                inicio_existente = datetime.fromisoformat(cita["fecha_cita"].replace('Z', '+00:00'))
                fin_existente = inicio_existente + timedelta(minutes=cita.get("duracion_minutos", 30))
                
                # Verificar si hay superposición
                if fecha_cita < fin_existente and inicio_existente < hora_fin:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error verificando disponibilidad: {e}")
            return False