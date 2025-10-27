from typing import List, Dict, Any
from datetime import datetime, date, time, timedelta, timezone
from fastapi import HTTPException
from repositories.citas_rep import RepositorioCitas
from repositories.medicos_rep import RepositorioMedicos
from schemas.disponibilidad_sch import HorarioDisponible, DisponibilidadResponse
import logging

logger = logging.getLogger(__name__)

class ServicioDisponibilidad:
    def __init__(self, repositorio_citas: RepositorioCitas, repositorio_profesionales: RepositorioMedicos):
        self.repositorio_citas = repositorio_citas
        self.repositorio_profesionales = repositorio_profesionales
    
    def obtener_horarios_disponibles(self, profesional_id: int, fecha_inicio: date = None, fecha_fin: date = None) -> DisponibilidadResponse:
        # Verificar que el profesional existe
        profesional = self.repositorio_profesionales.obtener_profesional(profesional_id)
        if not profesional:
            raise HTTPException(status_code=404, detail="Profesional no encontrado")
        
        # Establecer fechas por defecto (4 semanas desde hoy)
        hoy = date.today()
        if not fecha_inicio:
            fecha_inicio = hoy
        if not fecha_fin:
            fecha_fin = hoy + timedelta(weeks=4)
        
        # Validar que el rango de fechas no sea demasiado grande
        if (fecha_fin - fecha_inicio).days > 60:  # Máximo 2 meses
            raise HTTPException(status_code=400, detail="El rango de fechas no puede ser mayor a 60 días")
        
        # Obtener citas existentes del profesional en el rango de fechas
        fecha_inicio_dt = datetime.combine(fecha_inicio, time.min)
        fecha_fin_dt = datetime.combine(fecha_fin, time.max)
        
        citas_existentes = self.repositorio_citas.obtener_citas_por_profesional(
            profesional_id, fecha_inicio_dt, fecha_fin_dt
        )
        
        # Generar horarios disponibles
        horarios_disponibles = self._generar_horarios_disponibles(
            profesional_id, fecha_inicio, fecha_fin, citas_existentes
        )
        
        return DisponibilidadResponse(
            profesional_id=profesional_id,
            nombre_profesional=f"{profesional['nombre']} {profesional['apellido']}",
            especialidad=profesional['especialidad'],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            horarios_disponibles=horarios_disponibles,
            total_disponibles=len([h for h in horarios_disponibles if h.disponible])
        )
    
    def _generar_horarios_disponibles(self, profesional_id: int, fecha_inicio: date, fecha_fin: date, citas_existentes: List[Dict[str, Any]]) -> List[HorarioDisponible]:
        horarios = []
        
        # Configuración de horario laboral (puedes hacer esto configurable)
        horario_laboral = {
            'inicio_manana': time(8, 0),   # 8:00 AM
            'fin_manana': time(12, 0),     # 12:00 PM
            'inicio_tarde': time(14, 0),   # 2:00 PM
            'fin_tarde': time(18, 0),      # 6:00 PM
        }
        
        # Días laborales (0=Lunes, 6=Domingo)
        dias_laborales = [0, 1, 2, 3, 4]  # Lunes a Viernes
        
        # Generar horarios para cada día en el rango
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            # Solo generar horarios para días laborales
            if current_date.weekday() in dias_laborales:
                # Horarios de la mañana
                horarios_manana = self._generar_horarios_dia(
                    profesional_id, current_date, 
                    horario_laboral['inicio_manana'], 
                    horario_laboral['fin_manana'],
                    citas_existentes
                )
                horarios.extend(horarios_manana)
                
                # Horarios de la tarde
                horarios_tarde = self._generar_horarios_dia(
                    profesional_id, current_date,
                    horario_laboral['inicio_tarde'],
                    horario_laboral['fin_tarde'],
                    citas_existentes
                )
                horarios.extend(horarios_tarde)
            
            current_date += timedelta(days=1)
        
        return horarios
    
    def _generar_horarios_dia(self, profesional_id: int, fecha: date, hora_inicio: time, hora_fin: time, citas_existentes: List[Dict[str, Any]]) -> List[HorarioDisponible]:
        horarios = []
        duracion_cita = timedelta(minutes=30)  # Duración por defecto de las citas
        # current_time = datetime.combine(fecha, hora_inicio)
        current_time = datetime.combine(fecha, hora_inicio, tzinfo=timezone.utc)
        # hora_fin_dt = datetime.combine(fecha, hora_fin)
        hora_fin_dt = datetime.combine(fecha, hora_fin, tzinfo=timezone.utc)

        
        while current_time + duracion_cita <= hora_fin_dt:
            # Verificar si este horario está disponible
            disponible = self._verificar_disponibilidad_horario(profesional_id, current_time, citas_existentes)
            
            horario = HorarioDisponible(
                fecha=fecha,
                hora_inicio=current_time.strftime("%H:%M"),
                hora_fin=(current_time + duracion_cita).strftime("%H:%M"),
                profesional_id=profesional_id,
                disponible=disponible
            )
            horarios.append(horario)
            
            current_time += duracion_cita
        
        return horarios
    
    def _verificar_disponibilidad_horario(self, profesional_id: int, horario: datetime, citas_existentes: List[Dict[str, Any]]) -> bool:
        for cita in citas_existentes:
            cita_inicio = datetime.fromisoformat(cita['fecha_cita'].replace('Z', '+00:00'))
            cita_duracion = timedelta(minutes=cita.get('duracion_minutos', 30))
            cita_fin = cita_inicio + cita_duracion
            
            # Verificar superposición
            if horario < cita_fin and (horario + timedelta(minutes=30)) > cita_inicio:
                return False
        
        return True