from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from schemas.paciente_sch import Paciente

class CitaBase(BaseModel):
    profesional_id: int
    nombre_profesional: str
    fecha_cita: datetime
    duracion_minutos: int = 30
    notas: Optional[str] = None

class CitaCrear(CitaBase):
    paciente_id: int

class CitaActualizar(BaseModel):
    fecha_cita: Optional[datetime] = None
    duracion_minutos: Optional[int] = None
    estado: Optional[str] = None
    notas: Optional[str] = None

class Cita(CitaBase):
    id: int
    paciente_id: int
    estado: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    paciente: Optional[Paciente] = None
    
    class Config:
        from_attributes = True

class VerificacionDisponibilidad(BaseModel):
    profesional_id: int
    fecha: datetime
    duracion_minutos: int = 30