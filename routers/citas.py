from fastapi import APIRouter, Depends
from typing import List
from repositories.citas_rep import RepositorioCitas
from repositories.pacientes_rep import RepositorioPacientes
from services.citas_srv import ServicioCitas
from schemas.citas_sch import Cita, CitaCrear, CitaActualizar, VerificacionDisponibilidad

router = APIRouter()

def obtener_servicio_citas() -> ServicioCitas:
    repositorio_citas = RepositorioCitas()
    repositorio_pacientes = RepositorioPacientes()
    return ServicioCitas(repositorio_citas, repositorio_pacientes)

@router.get("/", response_model=List[Cita])
def obtener_citas(
    saltar: int = 0,
    limite: int = 100,
    servicio: ServicioCitas = Depends(obtener_servicio_citas)
):
    return servicio.obtener_todas_citas(saltar, limite)

@router.get("/{id_cita}", response_model=Cita)
def obtener_cita(
    id_cita: int,
    servicio: ServicioCitas = Depends(obtener_servicio_citas)
):
    return servicio.obtener_cita(id_cita)

@router.get("/paciente/{id_paciente}", response_model=List[Cita])
def obtener_citas_paciente(
    id_paciente: int,
    saltar: int = 0,
    limite: int = 100,
    servicio: ServicioCitas = Depends(obtener_servicio_citas)
):
    return servicio.obtener_citas_por_paciente(id_paciente, saltar, limite)

@router.post("/", response_model=Cita)
def crear_cita(
    cita: CitaCrear,
    servicio: ServicioCitas = Depends(obtener_servicio_citas)
):
    return servicio.crear_cita(cita)

@router.put("/{id_cita}", response_model=Cita)
def actualizar_cita(
    id_cita: int,
    cita_actualizar: CitaActualizar,
    servicio: ServicioCitas = Depends(obtener_servicio_citas)
):
    return servicio.actualizar_cita(id_cita, cita_actualizar)

@router.post("/verificar-disponibilidad")
def verificar_disponibilidad(
    disponibilidad: VerificacionDisponibilidad,
    servicio: ServicioCitas = Depends(obtener_servicio_citas)
):
    return servicio.verificar_disponibilidad(disponibilidad)