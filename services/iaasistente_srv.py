from crewai import Agent, Task, Crew, Process
from crewai_tools import BaseTool
from groq import Groq
from typing import Dict, Any
import json
from datetime import date, timedelta
import logging
from ai.tools import (
    BuscarProfesionalTool,
    ObtenerProfesionalesTool,
    ObtenerHorariosTool,
    BuscarDisponibleTool,
    CrearCitaTool,
    VerificarPacienteTool
)
from config import settings

logger = logging.getLogger(__name__)

class ServicioAssistant:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        
    def crear_agente_asistente(self) -> Agent:
        """Crear el agente asistente con todas las herramientas"""
        
        # Inicializar herramientas
        herramientas = [
            BuscarProfesionalTool(),
            ObtenerProfesionalesTool(),
            ObtenerHorariosTool(),
            BuscarDisponibleTool(),
            CrearCitaTool(),
            VerificarPacienteTool()
        ]
        
        agente = Agent(
            role='Asistente Médico Senior',
            goal='Ayudar a los pacientes a agendar citas médicas de manera eficiente y precisa',
            backstory="""Eres un asistente médico inteligente y servicial que trabaja en una clínica.
            Tu especialidad es entender las necesidades de los pacientes y agendar citas con los profesionales
            médicos adecuados. Eres preciso, amable y siempre buscas la mejor opción para el paciente.""",
            tools=herramientas,
            verbose=True,
            allow_delegation=False,
            llm=self._get_llm()
        )
        
        return agente
    
    def _get_llm(self):
        """Configurar el LLM con Groq"""
        from langchain_community.chat_models import ChatGroq
        return ChatGroq(
            model="llama3-8b-8192",
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.1
        )
    
    def procesar_solicitud(self, mensaje: str, paciente_id: int = None) -> Dict[str, Any]:
        """Procesar la solicitud del usuario usando crewAI"""
        try:
            # Crear agente y tarea
            agente = self.crear_agente_asistente()
            
            tarea = Task(
                description=self._crear_descripcion_tarea(mensaje, paciente_id),
                agent=agente,
                expected_output="""Un JSON con el siguiente formato exacto:
                {
                    "nombre_doctor": "Nombre del doctor",
                    "fecha": "YYYY-MM-DD",
                    "hora": "HH:MM",
                    "profesional_id": id_del_profesional,
                    "disponible": true/false,
                    "cita_creada": true/false,
                    "cita_id": id_de_la_cita_si_se_creo,
                    "mensaje": "Mensaje detallado al usuario"
                }"""
            )
            
            # Crear crew y ejecutar
            crew = Crew(
                agents=[agente],
                tasks=[tarea],
                process=Process.sequential,
                verbose=True
            )
            
            resultado = crew.kickoff()
            
            # Parsear la respuesta
            return self._parsear_respuesta_crewai(str(resultado))
            
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
    
    def _crear_descripcion_tarea(self, mensaje: str, paciente_id: int = None) -> str:
        """Crear la descripción de la tarea para el agente"""
        
        descripcion = f"""
        INFORMACIÓN DEL PACIENTE:
        - ID del paciente: {paciente_id or 'No especificado'}
        
        SOLICITUD DEL USUARIO:
        "{mensaje}"
        
        TU TAREA:
        1. Analizar la solicitud del usuario e identificar:
           - Nombre del doctor si se menciona
           - Fecha deseada (convertir 'hoy', 'mañana' a fechas reales)
           - Hora deseada
        
        2. Buscar disponibilidad:
           - Si se menciona un doctor específico, buscar su disponibilidad
           - Si no se menciona doctor, buscar el primer profesional disponible
           - Verificar que la fecha y hora estén disponibles
        
        3. Crear cita si es posible:
           - SI el paciente_id está proporcionado Y hay disponibilidad, CREAR la cita automáticamente
           - SI el paciente_id NO está proporcionado, solo verificar disponibilidad
        
        4. Generar respuesta en el formato JSON especificado.
        
        FECHAS DE REFERENCIA:
        - Hoy: {date.today()}
        - Mañana: {date.today() + timedelta(days=1)}
        
        REGLAS IMPORTANTES:
        - Siempre responder en el formato JSON exacto especificado
        - Si no hay disponibilidad, establecer "disponible": false y explicar en el mensaje
        - Si el paciente_id no está proporcionado, NO crear la cita
        - Ser claro y útil en el mensaje para el usuario
        """
        
        return descripcion
    
    def _parsear_respuesta_crewai(self, respuesta: str) -> Dict[str, Any]:
        """Parsear la respuesta de crewAI al formato requerido"""
        try:
            # Buscar JSON en la respuesta
            import re
            json_match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}|\{[^{}]*\}', respuesta, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                # Limpiar el JSON string
                json_str = json_str.replace('\\n', ' ').replace('\\t', ' ').replace('`', '').strip()
                
                # Buscar el JSON más interno si hay múltiples niveles
                inner_json_match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}|\{[^{}]*\}', json_str)
                if inner_json_match:
                    json_str = inner_json_match.group()
                
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
                # Si no encuentra JSON, usar valores por defecto
                return {
                    "nombre_doctor": "No identificado",
                    "fecha": "No identificada",
                    "hora": "No identificada",
                    "profesional_id": 0,
                    "disponible": False,
                    "cita_creada": False,
                    "cita_id": None,
                    "mensaje": f"No pude procesar tu solicitud. Respuesta del sistema: {respuesta[:200]}..."
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON de crewAI: {e}")
            # Intentar extraer información básica del texto
            import re
            fecha_match = re.search(r'(\d{4}-\d{2}-\d{2})', respuesta)
            hora_match = re.search(r'(\d{1,2}:\d{2})', respuesta)
            
            return {
                "nombre_doctor": "No identificado",
                "fecha": fecha_match.group(1) if fecha_match else "No identificada",
                "hora": hora_match.group(1) if hora_match else "No identificada",
                "profesional_id": 0,
                "disponible": False,
                "cita_creada": False,
                "cita_id": None,
                "mensaje": f"Respuesta del asistente: {respuesta[:200]}..."
            }
        except Exception as e:
            logger.error(f"Error parseando respuesta de crewAI: {e}")
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