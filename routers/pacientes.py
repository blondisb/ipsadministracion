from fastapi import APIRouter, Depends
from typing import List
from repositories.pacientes_rep import RepositorioPacientes
from services.pacientes_srv import ServicioPacientes
from schemas.paciente_sch import Paciente, PacienteCrear, PacienteActualizar

router = APIRouter()

def obtener_servicio_pacientes() -> ServicioPacientes:
    repositorio = RepositorioPacientes()
    return ServicioPacientes(repositorio)

@router.get("/", response_model=List[Paciente])
def obtener_pacientes(
    saltar: int = 0,
    limite: int = 100,
    servicio: ServicioPacientes = Depends(obtener_servicio_pacientes)
):
    return servicio.obtener_pacientes(saltar, limite)

@router.get("/{id_paciente}", response_model=Paciente)
def obtener_paciente(
    id_paciente: int,
    servicio: ServicioPacientes = Depends(obtener_servicio_pacientes)
):
    return servicio.obtener_paciente(id_paciente)

@router.post("/", response_model=Paciente)
def crear_paciente(
    paciente: PacienteCrear,
    servicio: ServicioPacientes = Depends(obtener_servicio_pacientes)
):
    return servicio.crear_paciente(paciente)

@router.put("/{id_paciente}", response_model=Paciente)
def actualizar_paciente(
    id_paciente: int,
    paciente_actualizar: PacienteActualizar,
    servicio: ServicioPacientes = Depends(obtener_servicio_pacientes)
):
    return servicio.actualizar_paciente(id_paciente, paciente_actualizar)

@router.delete("/{id_paciente}")
def eliminar_paciente(
    id_paciente: int,
    servicio: ServicioPacientes = Depends(obtener_servicio_pacientes)
):
    return servicio.eliminar_paciente(id_paciente)