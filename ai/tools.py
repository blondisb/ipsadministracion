from crewai.tools import BaseTool
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
import logging
from repositories.medicos_rep import RepositorioMedicos
from services.disponibilidad_srv import ServicioDisponibilidad
from repositories.citas_rep import RepositorioCitas
from repositories.pacientes_rep import RepositorioPacientes
from schemas.citas_sch import CitaCrear
from datetime import datetime

logger = logging.getLogger(__name__)

class BuscarProfesionalInput(BaseModel):
    nombre: str = Field(..., description="Nombre o apellido del profesional a buscar")

class BuscarProfesionalTool(BaseTool):
    name: str = "buscar_profesional_por_nombre"
    description: str = "Buscar un profesional médico por su nombre o apellido"
    args_schema: Type[BaseModel] = BuscarProfesionalInput

    def _run(self, nombre: str) -> List[Dict[str, Any]]:
        try:
            repositorio = RepositorioMedicos()
            profesionales = repositorio.obtener_profesionales_activos()
            resultados = []
            
            for profesional in profesionales:
                nombre_completo = f"{profesional['nombre']} {profesional['apellido']}".lower()
                if nombre.lower() in nombre_completo:
                    resultados.append({
                        'id': profesional['id'],
                        'nombre_completo': f"{profesional['nombre']} {profesional['apellido']}",
                        'especialidad': profesional['especialidad'],
                        'email': profesional['email'],
                        'telefono': profesional['telefono']
                    })
            
            return resultados if resultados else [{'ERROR': 'ERROR No se encontraron profesionales con ese nombre'}]
        except Exception as e:
            logger.error(f"Error buscando profesional por nombre {nombre}: {e}")
            return [{'ERROR': 'ERROR No se encontraron profesionales con ese nombre'}]

class ObtenerProfesionalesTool(BaseTool):
    name: str = "obtener_profesionales_activos"
    description: str = "Obtener lista de todos los profesionales médicos activos"

    def _run(self) -> List[Dict[str, Any]]:
        try:
            repositorio = RepositorioMedicos()
            profesionales = repositorio.obtener_profesionales_activos()
            return [{
                'id': p['id'],
                'nombre_completo': f"{p['nombre']} {p['apellido']}",
                'especialidad': p['especialidad'],
                'email': p['email'],
                'telefono': p['telefono']
            } for p in profesionales]
        except Exception as e:
            logger.error(f"Error obteniendo profesionales activos: {e}")
            return []

class ObtenerHorariosInput(BaseModel):
    profesional_id: int = Field(..., description="ID del profesional")
    fecha: str = Field(..., description="Fecha en formato YYYY-MM-DD")

class ObtenerHorariosTool(BaseTool):
    name: str = "obtener_horarios_disponibles"
    description: str = "Obtener horarios disponibles de un profesional en una fecha específica"
    args_schema: Type[BaseModel] = ObtenerHorariosInput

    def _run(self, profesional_id: int, fecha: str) -> Dict[str, Any]:
        try:
            repositorio_citas = RepositorioCitas()
            repositorio_profesionales = RepositorioMedicos()
            servicio_disponibilidad = ServicioDisponibilidad(repositorio_citas, repositorio_profesionales)
            
            # Convertir fecha string a date object
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            from datetime import timedelta
            fecha_fin = fecha_obj + timedelta(days=1)
            
            disponibilidad = servicio_disponibilidad.obtener_horarios_disponibles(
                profesional_id, fecha_obj, fecha_fin
            )
            
            # Filtrar solo los horarios disponibles para la fecha específica
            horarios_disponibles_fecha = [
                horario for horario in disponibilidad.horarios_disponibles 
                if horario.fecha == fecha_obj and horario.disponible
            ]
            
            return {
                'profesional_id': profesional_id,
                'nombre_profesional': disponibilidad.nombre_profesional,
                'fecha': fecha,
                'horarios_disponibles': [
                    {
                        'hora_inicio': horario.hora_inicio,
                        'hora_fin': horario.hora_fin
                    } for horario in horarios_disponibles_fecha
                ],
                'total_disponibles': len(horarios_disponibles_fecha)
            }
        except Exception as e:
            logger.error(f"Error obteniendo horarios disponibles: {e}")
            return {'error': str(e)}

class BuscarDisponibleInput(BaseModel):
    fecha: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    hora: str = Field(..., description="Hora en formato HH:MM")

class BuscarDisponibleTool(BaseTool):
    name: str = "buscar_profesional_disponible_fecha"
    description: str = "Buscar el primer profesional disponible en una fecha y hora específica"
    args_schema: Type[BaseModel] = BuscarDisponibleInput

    def _run(self, fecha: str, hora: str) -> Dict[str, Any]:
        try:
            repositorio_profesionales = RepositorioMedicos()
            repositorio_citas = RepositorioCitas()
            servicio_disponibilidad = ServicioDisponibilidad(repositorio_citas, repositorio_profesionales)
            
            profesionales = repositorio_profesionales.obtener_profesionales_activos()
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            
            for profesional in profesionales:
                # Verificar disponibilidad para este profesional
                disponibilidad = servicio_disponibilidad.obtener_horarios_disponibles(
                    profesional['id'], fecha_obj, fecha_obj
                )
                
                if hasattr(disponibilidad, 'horarios_disponibles'):
                    for horario in disponibilidad.horarios_disponibles:
                        if horario.hora_inicio == hora and horario.disponible:
                            return {
                                'profesional_id': profesional['id'],
                                'nombre_completo': f"{profesional['nombre']} {profesional['apellido']}",
                                'especialidad': profesional['especialidad'],
                                'fecha': fecha,
                                'hora': hora,
                                'disponible': True
                            }
            
            return {
                'disponible': False,
                'mensaje': 'No hay profesionales disponibles en esa fecha y hora'
            }
        except Exception as e:
            logger.error(f"Error buscando profesional disponible: {e}")
            return {'error': str(e)}

class CrearCitaInput(BaseModel):
    paciente_id: int = Field(..., description="ID del paciente")
    profesional_id: int = Field(..., description="ID del profesional")
    fecha: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    hora: str = Field(..., description="Hora en formato HH:MM")
    notas: str = Field("", description="Notas adicionales para la cita")

class CrearCitaTool(BaseTool):
    name: str = "crear_cita_medica"
    description: str = "Crear una cita médica para un paciente con un profesional en una fecha y hora específica"
    args_schema: Type[BaseModel] = CrearCitaInput

    def _run(self, paciente_id: int, profesional_id: int, fecha: str, hora: str, notas: str = "") -> Dict[str, Any]:
        try:
            repositorio_pacientes = RepositorioPacientes()
            repositorio_profesionales = RepositorioMedicos()
            repositorio_citas = RepositorioCitas()
            
            # Verificar que el paciente existe
            paciente = repositorio_pacientes.obtener_paciente(paciente_id)
            if not paciente:
                return {
                    'success': False,
                    'error': f'Paciente con ID {paciente_id} no encontrado'
                }
            
            # Verificar que el profesional existe
            profesional = repositorio_profesionales.obtener_profesional(profesional_id)
            if not profesional:
                return {
                    'success': False,
                    'error': f'Profesional con ID {profesional_id} no encontrado'
                }
            
            # Combinar fecha y hora
            fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            
            # Crear la cita
            cita_data = CitaCrear(
                paciente_id=paciente_id,
                profesional_id=profesional_id,
                nombre_profesional=f"{profesional['nombre']} {profesional['apellido']}",
                fecha_cita=fecha_hora,
                duracion_minutos=30,
                notas=notas,
                tipo_cita="consulta_general"
            )
            
            cita_creada = repositorio_citas.crear_cita(cita_data)
            
            if cita_creada:
                return {
                    'success': True,
                    'cita_id': cita_creada['id'],
                    'mensaje': f'Cita creada exitosamente con {profesional["nombre"]} {profesional["apellido"]}',
                    'fecha': fecha,
                    'hora': hora,
                    'paciente_nombre': f"{paciente['nombre']} {paciente['apellido']}",
                    'profesional_nombre': f"{profesional['nombre']} {profesional['apellido']}"
                }
            else:
                return {
                    'success': False,
                    'error': 'Error al crear la cita en la base de datos'
                }
                
        except Exception as e:
            logger.error(f"Error creando cita médica: {e}")
            return {
                'success': False,
                'error': f'Error del sistema: {str(e)}'
            }

class VerificarPacienteInput(BaseModel):
    paciente_id: int = Field(..., description="ID del paciente a verificar")

class VerificarPacienteTool(BaseTool):
    name: str = "verificar_paciente"
    description: str = "Verificar si un paciente existe en el sistema"
    args_schema: Type[BaseModel] = VerificarPacienteInput

    def _run(self, paciente_id: int) -> Dict[str, Any]:
        try:
            repositorio = RepositorioPacientes()
            paciente = repositorio.obtener_paciente(paciente_id)
            if paciente:
                return {
                    'existe': True,
                    'paciente': {
                        'id': paciente['id'],
                        'nombre': paciente['nombre'],
                        'apellido': paciente['apellido'],
                        'email': paciente['email']
                    }
                }
            else:
                return {
                    'existe': False,
                    'error': f'Paciente con ID {paciente_id} no encontrado'
                }
        except Exception as e:
            logger.error(f"Error verificando paciente: {e}")
            return {
                'existe': False,
                'error': str(e)
            }