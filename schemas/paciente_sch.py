from pydantic import BaseModel
# , EmailStr
from typing import Optional
from datetime import date, datetime

class PacienteBase(BaseModel):
    nombre: str
    apellido: str
    email: str
    telefono: Optional[str] = None
    fecha_nacimiento: date
    direccion: Optional[str] = None
    contacto_emergencia: Optional[str] = None
    telefono_emergencia: Optional[str] = None

class PacienteCrear(PacienteBase):
    pass

class PacienteActualizar(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    contacto_emergencia: Optional[str] = None
    telefono_emergencia: Optional[str] = None

class Paciente(PacienteBase):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    class Config:
        from_attributes = True