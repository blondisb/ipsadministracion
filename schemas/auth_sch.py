from pydantic import BaseModel

class Token(BaseModel):
    token_acceso: str
    tipo_token: str

class DatosToken(BaseModel):
    nombre_usuario: str = None