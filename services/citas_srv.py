from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
from repositories.citas_rep import RepositorioCitas
from repositories.pacientes_rep import RepositorioPacientes
from schemas.citas_sch import CitaCrear, CitaActualizar, Cita, VerificacionDisponibilidad

class ServicioCitas:
    def __init__(self, repositorio_citas: RepositorioCitas, repositorio_pacientes: RepositorioPacientes):
        self.repositorio_citas = repositorio_citas
        self.repositorio_pacientes = repositorio_pacientes
    
    def obtener_cita(self, id_cita: int) -> Cita:
        datos_cita = self.repositorio_citas.obtener_cita(id_cita)
        if not datos_cita:
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        return Cita(**datos_cita)
    
    def obtener_citas_por_paciente(self, id_paciente: int, saltar: int = 0, limite: int = 100) -> List[Cita]:
        # Verificar que el paciente existe
        paciente = self.repositorio_pacientes.obtener_paciente(id_paciente)
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
        datos_citas = self.repositorio_citas.obtener_citas_por_paciente(id_paciente, saltar, limite)
        return [Cita(**cita) for cita in datos_citas]
    
    def obtener_todas_citas(self, saltar: int = 0, limite: int = 100) -> List[Cita]:
        datos_citas = self.repositorio_citas.obtener_todas_citas(saltar, limite)
        return [Cita(**cita) for cita in datos_citas]
    
    def crear_cita(self, cita: CitaCrear) -> Cita:
        # Verificar que el paciente existe
        paciente = self.repositorio_pacientes.obtener_paciente(cita.paciente_id)
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        
        # Verificar disponibilidad
        if not self.repositorio_citas.verificar_disponibilidad(
            cita.profesional_id, 
            cita.fecha_cita, 
            cita.duracion_minutos
        ):
            raise HTTPException(status_code=400, detail="El profesional no está disponible en ese horario")
        
        cita_creada = self.repositorio_citas.crear_cita(cita)
        if not cita_creada:
            raise HTTPException(status_code=500, detail="Error al crear la cita")
        
        return Cita(**cita_creada)
    
    def actualizar_cita(self, id_cita: int, cita_actualizar: CitaActualizar) -> Cita:
        cita_actualizada = self.repositorio_citas.actualizar_cita(id_cita, cita_actualizar)
        if not cita_actualizada:
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        return Cita(**cita_actualizada)
    
    def verificar_disponibilidad(self, disponibilidad: VerificacionDisponibilidad) -> dict:
        esta_disponible = self.repositorio_citas.verificar_disponibilidad(
            disponibilidad.profesional_id,
            disponibilidad.fecha,
            disponibilidad.duracion_minutos
        )
        
        return {
            "profesional_id": disponibilidad.profesional_id,
            "fecha": disponibilidad.fecha,
            "duracion_minutos": disponibilidad.duracion_minutos,
            "disponible": esta_disponible
        }