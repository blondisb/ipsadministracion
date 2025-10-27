from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    token_acceso: str
    tipo_token: str

class DatosToken(BaseModel):
    id_usuario: str
    nombre_usuario: str = None

class UsuarioLogin(BaseModel):
    email: EmailStr
    contraseña: str

class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    apellido: str

class UsuarioCrear(UsuarioBase):
    contraseña: str

class Usuario(UsuarioBase):
    id: int
    activo: bool
    
    class Config:
        from_attributes = True