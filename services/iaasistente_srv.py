from smolagents import CodeAgent, Tool
from groq import Groq
from typing import Dict, Any, List
import json
from datetime import datetime, date, timedelta
import logging
from repositories.medicos_rep import RepositorioMedicos
from services.disponibilidad_srv import ServicioDisponibilidad
from repositories.citas_rep import RepositorioCitas
from repositories.pacientes_rep import RepositorioPacientes
from schemas.citas_sch import CitaCrear
from config import settings

logger = logging.getLogger(__name__)

class ServicioAssistant:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.repositorio_profesionales = RepositorioMedicos()
        self.repositorio_citas = RepositorioCitas()
        self.repositorio_pacientes = RepositorioPacientes()
        
    def crear_agente(self) -> CodeAgent:
        # Definir las herramientas
        herramientas = [
            Tool(
                name="buscar_profesional_por_nombre",
                description="Buscar un profesional médico por su nombre o apellido",
                function=self.buscar_profesional_por_nombre
            ),
            Tool(
                name="obtener_profesionales_activos",
                description="Obtener lista de todos los profesionales médicos activos",
                function=self.obtener_profesionales_activos
            ),
            Tool(
                name="obtener_horarios_disponibles",
                description="Obtener horarios disponibles de un profesional en una fecha específica",
                function=self.obtener_horarios_disponibles
            ),
            Tool(
                name="buscar_profesional_disponible_fecha",
                description="Buscar el primer profesional disponible en una fecha y hora específica",
                function=self.buscar_profesional_disponible_fecha
            ),
            Tool(
                name="crear_cita_medica",
                description="Crear una cita médica para un paciente con un profesional en una fecha y hora específica",
                function=self.crear_cita_medica
            ),
            Tool(
                name="verificar_paciente",
                description="Verificar si un paciente existe en el sistema",
                function=self.verificar_paciente
            )
        ]
        
        # Crear el agente con Groq
        agent = CodeAgent(
            tools=herramientas,
            model="groq/llama3-8b-8192",
            max_steps=15,  # Aumentar pasos para incluir creación de cita
            verbosity_level=1
        )
        
        return agent
    
    def buscar_profesional_por_nombre(self, nombre: str) -> List[Dict[str, Any]]:
        """Buscar profesional por nombre o apellido"""
        try:
            profesionales = self.repositorio_profesionales.obtener_profesionales_activos()
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
            
            return resultados
        except Exception as e:
            logger.error(f"Error buscando profesional por nombre {nombre}: {e}")
            return []
    
    def obtener_profesionales_activos(self) -> List[Dict[str, Any]]:
        """Obtener todos los profesionales activos"""
        try:
            profesionales = self.repositorio_profesionales.obtener_profesionales_activos()
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
    
    def obtener_horarios_disponibles(self, profesional_id: int, fecha: str) -> Dict[str, Any]:
        """Obtener horarios disponibles de un profesional en una fecha específica"""
        try:
            servicio_disponibilidad = ServicioDisponibilidad(
                self.repositorio_citas, 
                self.repositorio_profesionales
            )
            
            # Convertir fecha string a date object
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
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
    
    def buscar_profesional_disponible_fecha(self, fecha: str, hora: str) -> Dict[str, Any]:
        """Buscar el primer profesional disponible en una fecha y hora específica"""
        try:
            profesionales = self.obtener_profesionales_activos()
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            
            for profesional in profesionales:
                # Verificar disponibilidad para este profesional
                disponibilidad = self.obtener_horarios_disponibles(profesional['id'], fecha)
                
                if 'horarios_disponibles' in disponibilidad and not disponibilidad.get('error'):
                    for horario in disponibilidad['horarios_disponibles']:
                        if horario['hora_inicio'] == hora:
                            return {
                                'profesional_id': profesional['id'],
                                'nombre_completo': profesional['nombre_completo'],
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
    
    def crear_cita_medica(self, paciente_id: int, profesional_id: int, fecha: str, hora: str, notas: str = "") -> Dict[str, Any]:
        """Crear una cita médica"""
        try:
            # Verificar que el paciente existe
            paciente = self.repositorio_pacientes.obtener_paciente(paciente_id)
            if not paciente:
                return {
                    'success': False,
                    'error': f'Paciente con ID {paciente_id} no encontrado'
                }
            
            # Verificar que el profesional existe
            profesional = self.repositorio_profesionales.obtener_profesional(profesional_id)
            if not profesional:
                return {
                    'success': False,
                    'error': f'Profesional con ID {profesional_id} no encontrado'
                }
            
            # Combinar fecha y hora
            fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
            
            # Verificar disponibilidad antes de crear
            disponibilidad = self.obtener_horarios_disponibles(profesional_id, fecha)
            horario_disponible = False
            
            if 'horarios_disponibles' in disponibilidad:
                for horario in disponibilidad['horarios_disponibles']:
                    if horario['hora_inicio'] == hora:
                        horario_disponible = True
                        break
            
            if not horario_disponible:
                return {
                    'success': False,
                    'error': 'El horario no está disponible'
                }
            
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
            
            cita_creada = self.repositorio_citas.crear_cita(cita_data)
            
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
    
    def verificar_paciente(self, paciente_id: int) -> Dict[str, Any]:
        """Verificar si un paciente existe"""
        try:
            paciente = self.repositorio_pacientes.obtener_paciente(paciente_id)
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
    
    def procesar_solicitud(self, mensaje: str, paciente_id: int = None) -> Dict[str, Any]:
        """Procesar la solicitud del usuario usando el agente"""
        try:
            agente = self.crear_agente()
            
            prompt = f"""
            Eres un asistente médico inteligente que ayuda a los pacientes a agendar citas.
            
            INFORMACIÓN DEL PACIENTE:
            - ID del paciente: {paciente_id or 'No especificado'}
            
            SOLICITUD DEL USUARIO:
            "{mensaje}"
            
            TU TAREA:
            1. Si el usuario menciona un doctor específico, buscar por nombre
            2. Identificar la fecha deseada (mañana, hoy, o fecha específica)
            3. Identificar la hora deseada
            4. Verificar disponibilidad del profesional
            5. SI el paciente_id está proporcionado Y hay disponibilidad, CREAR LA CITA automáticamente
            6. Si no hay paciente_id, solo verificar disponibilidad
            
            FORMATO DE RESPUESTA OBLIGATORIO (JSON):
            {{
                "nombre_doctor": "Nombre del doctor",
                "fecha": "YYYY-MM-DD",
                "hora": "HH:MM",
                "profesional_id": id_del_profesional,
                "disponible": true/false,
                "cita_creada": true/false,
                "cita_id": id_de_la_cita_si_se_creo,
                "mensaje": "Mensaje detallado al usuario"
            }}
            
            REGLAS IMPORTANTES:
            - Si el paciente_id NO está proporcionado, NO crear la cita, solo verificar disponibilidad
            - Si el paciente_id está proporcionado Y hay disponibilidad, CREAR la cita automáticamente
            - Si no se especifica doctor, buscar el primer disponible
            - Si no hay disponibilidad, sugerir alternativas pero NO crear cita
            
            Usa las herramientas en este orden:
            1. Primero verificar_paciente si hay paciente_id
            2. Buscar profesional por nombre o obtener todos
            3. Verificar disponibilidad
            4. Si todo está bien, crear_cita_medica
            
            ¡Responde EXACTAMENTE en el formato JSON especificado!
            """
            
            resultado = agente.run(prompt)
            
            # Parsear la respuesta del agente
            return self._parsear_respuesta_agente(resultado)
            
        except Exception as e:
            logger.error(f"Error procesando solicitud del asistente: {e}")
            return {
                "nombre_doctor": "Error",
                "fecha": "Error",
                "hora": "Error",
                "profesional_id": 0,
                "disponible": False,
                "cita_creada": False,
                "cita_id": None,
                "mensaje": f"Error procesando la solicitud: {str(e)}"
            }
    
    def _parsear_respuesta_agente(self, respuesta: str) -> Dict[str, Any]:
        """Parsear la respuesta del agente al formato requerido"""
        try:
            # Buscar JSON en la respuesta
            import re
            json_match = re.search(r'\{.*\}', respuesta, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                datos = json.loads(json_str)
                
                return {
                    "nombre_doctor": datos.get("nombre_doctor", "No especificado"),
                    "fecha": datos.get("fecha", "No especificada"),
                    "hora": datos.get("hora", "No especificada"),
                    "profesional_id": datos.get("profesional_id", 0),
                    "disponible": datos.get("disponible", False),
                    "cita_creada": datos.get("cita_creada", False),
                    "cita_id": datos.get("cita_id"),
                    "mensaje": datos.get("mensaje", "Solicitud procesada")
                }
            else:
                # Si no encuentra JSON, intentar extraer información
                return {
                    "nombre_doctor": "No identificado",
                    "fecha": "No identificada",
                    "hora": "No identificada",
                    "profesional_id": 0,
                    "disponible": False,
                    "cita_creada": False,
                    "cita_id": None,
                    "mensaje": "No pude procesar tu solicitud. Por favor, sé más específico."
                }
                
        except Exception as e:
            logger.error(f"Error parseando respuesta del agente: {e}")
            return {
                "nombre_doctor": "Error",
                "fecha": "Error",
                "hora": "Error",
                "profesional_id": 0,
                "disponible": False,
                "cita_creada": False,
                "cita_id": None,
                "mensaje": f"Error procesando la respuesta: {str(e)}"
            }