from crewai import LLM, Agent, Task, Crew, Process
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
import os
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "dummy")

logger = logging.getLogger(__name__)

class ServicioAssistant:
    def __init__(self):
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        
    def crear_agente_asistente(self) -> Agent:
        """Crear el agente asistente con todas las herramientas"""
        
        # Inicializar herramientas
        herramientas = [
            # BuscarProfesionalTool(),
            ObtenerProfesionalesTool(),
            ObtenerHorariosTool(),
            BuscarDisponibleTool(),
            CrearCitaTool(),
            VerificarPacienteTool()
        ]
        
        agente = Agent(
            role='Asistente Médico Senior',
            goal="""Agendar citas médicas de forma eficiente, precisa y segura. 
                Prioriza la verificación mediante las herramientas disponibles, evita cualquier invención 
                de nombres o IDs, y siempre devuelve la respuesta final en el JSON requerido.
            """,
            backstory="""Eres un Asistente Médico Senior virtual, profesional, preciso y orientado a procedimientos. 
            Tu objetivo es ayudar a pacientes a verificar disponibilidad y agendar citas médicas utilizando
            exclusivamente las herramientas autorizadas (por ejemplo: buscar_profesional_por_nombre,
            obtener_profesionales_activos, obtener_horarios_disponibles, crear_cita_medica, verificar_paciente).

            Reglas de comportamiento (seguir al pie de la letra):
            - NUNCA inventes nombres, apellidos, IDs, horarios o resultados. Usa únicamente los valores
            que devuelvan las herramientas.
            - Si una herramienta devuelve "No se encontraron profesionales" o una lista vacía, detén
            inmediatamente el proceso y retorna el JSON final indicando el error (cita_creada: false).
            - Si un nombre produce múltiples coincidencias, NO escojas por tu cuenta: informa la ambigüedad
            y solicita aclaración en el campo "mensaje" (detén el flujo).
            - Tras obtener un profesional_id, valida INMEDIATAMENTE la disponibilidad para la fecha solicitada
            llamando a obtener_horarios_disponibles(profesional_id, fecha). Si la hora solicitada no está
            disponible, detén el proceso y devuelve hasta 5 sugerencias cercanas basadas en las salidas
            de las herramientas (no inventadas).
            - Si paciente_id no está presente, no crees la cita; solo informas disponibilidad y dejas cita_creada:false.
            - La salida FINAL debe ser siempre un JSON con las keys obligatorias:
            nombre_doctor, fecha (YYYY-MM-DD), hora (HH:MM), profesional_id, disponible (bool),
            cita_creada (bool), cita_id (int|null), mensaje (str).
            - El mensaje debe ser claro, explicar la acción tomada o la razón por la cual no se pudo completar
            la solicitud, e incluir las sugerencias cuando apliquen.
            - Si ocurre un error de herramienta o fallo inesperado, devuelve un JSON válido con cita_creada:false
            y un mensaje explicativo (no caigas en respuestas incompletas ni en texto libre sin JSON).

            Tono: profesional, directo y empático. Prioriza seguridad y precisión por encima de completar acciones
            sin confirmación. Si se requiere interacción adicional con el usuario (por ejemplo aclarar nombre),
            menciona exactamente qué información falta en el campo "mensaje".
            """,
            tools=herramientas,
            verbose=True,
            allow_delegation=False,
            # llm=self._get_llm()
            llm= LLM(
                model=settings.AI_MODEL_NAME,
                api_key=settings.GROQ_API_KEY,
                temperature=0.1
            ),
            max_iter = 5
        )
        
        return agente

    
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
            final_result = self._parsear_respuesta_crewai(str(resultado))
            return final_result
            
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
            - ID del paciente: {paciente_id or "No especificado"}

            SOLICITUD DEL USUARIO:
            "{mensaje}"

            INSTRUCCIONES CLAVE (leer con atención — seguir al pie de la letra):

            0) FORMATO DE SALIDA OBLIGATORIO: siempre devolver un JSON con estas keys:
            {{
                "nombre_doctor": str,         # Nombre EXACTO proveniente ÚNICAMENTE de la lista de profesionales activos
                "fecha": "YYYY-MM-DD",        # Fecha en formato ISO
                "hora": "HH:MM",              # 24h (ej. "10:00")
                "profesional_id": int,        # ID EXACTO proveniente ÚNICAMENTE de la lista de profesionales activos
                "disponible": bool,
                "cita_creada": bool,
                "cita_id": int|null,
                "mensaje": str                # Aquí se incluirán las 5 sugerencias si aplica
            }}

            1) Detectar información en el mensaje:
            - Extraer nombre del doctor (nombre y/o apellido) si existe.
            - Extraer fecha (convertir "hoy", "mañana", "el lunes", etc. a YYYY-MM-DD).
            - Extraer hora (normalizar a formato HH:MM 24h).
            -> Si no puedes identificar fecha/hora, indicarlo claramente en "mensaje" y terminar (cita_creada: false).

            2) Si se menciona un doctor:
            a) Llamar a buscar_profesional_por_nombre(nombre_detectado).
            b) Si la herramienta devuelve error o lista vacía -> **DETENER**: retornar JSON con disponible:false, cita_creada:false y mensaje "No se encontró el doctor X".
            c) Si la herramienta devuelve múltiples coincidencias:
                - Intentar emparejar por coincidencia exacta (case-insensitive) con el nombre completo.
                - Si queda ambigüedad -> **DETENER** y pedir aclaración en "mensaje" (no adivinar).
            d) Si hay una sola coincidencia clara: tomar `profesional_id` y `nombre` EXACTOS tal como devuelve la herramienta.

            3) VALIDACIÓN INMEDIATA DE HORARIO (nueva regla importante):
            - Tras obtener `profesional_id` (ya sea porque el usuario pidió ese doctor o porque lo seleccionaste de la lista), **ANTES** de continuar:
                1. Llamar `obtener_horarios_disponibles(profesional_id, fecha)` con la fecha solicitada.
                2. Si la herramienta devuelve error o lista vacía -> **NO** continuar. Retornar JSON con:
                    - "disponible": false
                    - "cita_creada": false
                    - "cita_id": null
                    - "mensaje": explicar que no hay horarios en la fecha solicitada y **ofrecer hasta 5 sugerencias** cercanas (ver formato abajo).
                3. Si la hora solicitada **no está** entre los horarios disponibles -> mismo comportamiento: detener y devolver hasta 5 sugerencias cercanas.
                4. Si la hora está disponible -> continuar al paso 5.
            - REGLA para las 5 sugerencias:
                * Buscar disponibilidad en fechas cercanas a la solicitada (por ejemplo, rango ±7 días alrededor de la fecha solicitada).
                * Recopilar las horas disponibles encontradas para ese `profesional_id` (o, si no hay suficientes, buscar en otros profesionales de la lista `obtener_profesionales_activos()` y devolver alternativas, siempre SIN inventar nombres ni IDs).
                * Ordenar las opciones por cercanía a la fecha solicitada y devolver **hasta 5** opciones.
                * Si no hay sugerencias suficientes, devolver las que existan y mencionarlo en el mensaje.
                * Formato de cada sugerencia dentro del mensaje: "1) YYYY-MM-DD HH:MM — Dr. Nombre Apellido (ID: X)".

            4) Si NO se menciona doctor:
            a) Llamar a obtener_profesionales_activos().
            b) Si la lista está vacía o la herramienta falla -> **DETENER** y retornar JSON con disponible:false, cita_creada:false y mensaje explicando la situación.
            c) Si la lista contiene profesionales: **SELECCIONAR UNO Y SOLO UNO** de la lista (regla: elegir el primer profesional de la lista tal como fue devuelta). Usar ese profesional_id y nombre EXACTOS.
            d) Antes de crear cita, aplicar la regla del paso 3 (validar horarios para ese profesional_id y la fecha solicitada). Si no hay disponibilidad, detener y devolver hasta 5 sugerencias (ver reglas arriba).

            5) Crear cita:
            - Si paciente_id está presente Y la hora fue validada como disponible -> llamar crear_cita_medica(paciente_id, profesional_id, fecha, hora).
                * Si la creación falla -> retornar JSON con disponible:true, cita_creada:false y mensaje con el error.
                * Si la creación succeed -> retornar JSON con cita_creada:true y cita_id devuelto por la herramienta.
            - Si paciente_id NO está presente -> **NO crear** la cita. Retornar disponible:true/false según verificación y cita_creada:false con mensaje explicando que falta paciente_id para crear la cita.

            6) REGLAS ABSOLUTAS (no negociables):
            - Nunca inventar ni modificar nombres o IDs: solo usar valores EXACTOS retornados por las herramientas.
            - Si alguna herramienta devuelve "No se encontraron profesionales", tratar eso como ausencia y detener el proceso.
            - Si hay ambigüedad (múltiples profesionales para un nombre), pedir aclaración y detener.
            - El campo "cita_creada" debe existir siempre: true si se creó, false en cualquier otro caso.
            - Las 5 sugerencias deben estar contenidas en "mensaje" en formato legible (listas numeradas) y deben provenir exclusivamente de las salidas de las herramientas.
            - Si se ofrecen sugerencias de otros profesionales, indicar el nombre y ID tal como aparecen en la herramienta.

            EJEMPLOS (salida esperada):
            - Si hora NO disponible y se generan sugerencias:
            {{
                "nombre_doctor": "Ana Martinez",
                "fecha": "2025-10-27",
                "hora": "10:00",
                "profesional_id": 2,
                "disponible": false,
                "cita_creada": false,
                "cita_id": null,
                "mensaje": "La hora 10:00 del 2025-10-27 no está disponible. Sugerencias cercanas:\\n1) 2025-10-28 09:30 — Dr. Ana Martinez (ID: 2)\\n2) 2025-10-29 11:00 — Dr. Ana Martinez (ID: 2)\\n3) 2025-10-29 14:00 — Dr. Juan Pérez (ID: 5)\\n4) 2025-10-30 10:00 — Dr. Ana Martinez (ID: 2)\\n5) 2025-11-01 08:00 — Dr. Laura Gómez (ID: 8)"
            }}

            FECHAS DE REFERENCIA:
            - Hoy: {date.today()}
            - Mañana: {date.today() + timedelta(days=1)}
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
                
                print("\n\n2\nResultado crewAI:", datos)
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