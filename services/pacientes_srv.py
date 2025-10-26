from typing import List, Optional
from fastapi import HTTPException
from repositories.pacientes_rep import RepositorioPacientes
from schemas.paciente_sch import PacienteCrear, PacienteActualizar, Paciente

class ServicioPacientes:
    def __init__(self, repositorio: RepositorioPacientes):
        self.repositorio = repositorio
    
    def obtener_paciente(self, id_paciente: int) -> Paciente:
        datos_paciente = self.repositorio.obtener_paciente(id_paciente)
        if not datos_paciente:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        return Paciente(**datos_paciente)
    
    def obtener_pacientes(self, saltar: int = 0, limite: int = 100) -> List[Paciente]:
        datos_pacientes = self.repositorio.obtener_pacientes(saltar, limite)
        return [Paciente(**paciente) for paciente in datos_pacientes]
    
    def crear_paciente(self, paciente: PacienteCrear) -> Paciente:
        # Verificar si el email ya existe
        paciente_existente = self.repositorio.obtener_paciente_por_email(paciente.email)
        if paciente_existente:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        paciente_creado = self.repositorio.crear_paciente(paciente)
        if not paciente_creado:
            raise HTTPException(status_code=500, detail="Error al crear el paciente")
        
        return Paciente(**paciente_creado)
    
    def actualizar_paciente(self, id_paciente: int, paciente_actualizar: PacienteActualizar) -> Paciente:
        paciente_actualizado = self.repositorio.actualizar_paciente(id_paciente, paciente_actualizar)
        if not paciente_actualizado:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        return Paciente(**paciente_actualizado)
    
    def eliminar_paciente(self, id_paciente: int) -> dict:
        exito = self.repositorio.eliminar_paciente(id_paciente)
        if not exito:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        return {"mensaje": "Paciente eliminado correctamente"}