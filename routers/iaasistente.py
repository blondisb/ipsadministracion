from fastapi import APIRouter, HTTPException
from services.iaasistente_srv import ServicioAssistant
from schemas.iaasistente_sch import AssistantRequest, AssistantResponse
import logging

logger = logging.getLogger(__name__)

enrutador = APIRouter()

def obtener_servicio_assistant() -> ServicioAssistant:
    return ServicioAssistant()

@enrutador.post("/", response_model=AssistantResponse)
async def procesar_solicitud_assistant(
    request: AssistantRequest
):
    """
    Endpoint del asistente virtual para agendar citas médicas
    """
    try:
        servicio = obtener_servicio_assistant()
        resultado = servicio.procesar_solicitud(request.mensaje, request.paciente_id)
        
        return AssistantResponse(
            nombre_doctor=resultado["nombre_doctor"],
            fecha=resultado["fecha"],
            hora=resultado["hora"],
            profesional_id=resultado["profesional_id"],
            disponible=resultado["disponible"],
            mensaje=resultado["mensaje"],
            cita_creada=resultado["cita_creada"],
            cita_id=resultado.get("cita_id")
        )
        
    except Exception as e:
        logger.error(f"Error en endpoint assistant: {e}")
        raise HTTPException(status_code=500, detail=f"Error del asistente: {str(e)}")

@enrutador.get("/health")
async def health_check():
    """
    Verificar que el asistente esté funcionando
    """
    return {"status": "healthy", "service": "medical_assistant"}