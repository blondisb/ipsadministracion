from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date
from repositories.citas_rep import RepositorioCitas
from repositories.medicos_rep import RepositorioMedicos
from services.disponibilidad_srv import ServicioDisponibilidad
from schemas.disponibilidad_sch import DisponibilidadResponse, DisponibilidadRequest
from utils.security import obtener_usuario_actual

router = APIRouter()

def obtener_servicio_disponibilidad() -> ServicioDisponibilidad:
    repositorio_citas = RepositorioCitas()
    repositorio_profesionales = RepositorioMedicos()
    return ServicioDisponibilidad(repositorio_citas, repositorio_profesionales)

@router.get("/profesional/{profesional_id}", response_model=DisponibilidadResponse)
def obtener_disponibilidad_profesional(
    profesional_id: int,
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio (por defecto: hoy)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin (por defecto: 4 semanas desde hoy)"),
    servicio: ServicioDisponibilidad = Depends(obtener_servicio_disponibilidad)
    # ,usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    Obtener horarios disponibles de un profesional en las próximas 4 semanas
    """
    return servicio.obtener_horarios_disponibles(profesional_id, fecha_inicio, fecha_fin)

@router.post("/profesional/{profesional_id}", response_model=DisponibilidadResponse)
def obtener_disponibilidad_profesional_post(
    profesional_id: int,
    request: DisponibilidadRequest,
    servicio: ServicioDisponibilidad = Depends(obtener_servicio_disponibilidad)
    # ,usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    Obtener horarios disponibles de un profesional con parámetros en el body
    """
    return servicio.obtener_horarios_disponibles(
        profesional_id, 
        request.fecha_inicio, 
        request.fecha_fin
    )
