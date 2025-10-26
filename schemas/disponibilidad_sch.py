from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date

class HorarioDisponible(BaseModel):
    fecha: date
    hora_inicio: str
    hora_fin: str
    profesional_id: int
    disponible: bool

class DisponibilidadRequest(BaseModel):
    profesional_id: int
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

class DisponibilidadResponse(BaseModel):
    profesional_id: int
    nombre_profesional: str
    especialidad: str
    fecha_inicio: date
    fecha_fin: date
    horarios_disponibles: List[HorarioDisponible]
    total_disponibles: int