from pydantic import BaseModel
from typing import Optional
from datetime import date, time

class AssistantRequest(BaseModel):
    mensaje: str
    paciente_id: int

class AssistantResponse(BaseModel):
    nombre_doctor: str
    fecha: str
    hora: str
    profesional_id: int
    disponible: bool
    cita_creada: bool
    cita_id: Optional[int] = None
    mensaje: str